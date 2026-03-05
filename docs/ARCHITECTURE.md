# Architecture

## Overview

APME is a six-container gRPC microservice deployed as a single Podman pod. The Primary service runs the engine (parse + annotate), then fans validation out **in parallel** to three independent validator backends over a unified gRPC contract. The CLI is ephemeral — run on-the-fly with the project directory mounted.

All inter-service communication is gRPC. There is no REST, no message queue, no service discovery. Containers in the same pod share `localhost`; addresses are fixed by convention.

## Container topology

```
┌──────────────────────────── apme-pod ─────────────────────────────┐
│                                                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Primary  │  │  Native  │  │   OPA    │  │ Ansible  │          │
│  │  :50051  │  │  :50055  │  │  :50054  │  │  :50053  │          │
│  │          │  │          │  │          │  │          │          │
│  │ engine + │  │ Python   │  │ OPA bin  │  │ ansible- │          │
│  │ orchestr │  │ rules on │  │ + gRPC   │  │ core     │          │
│  │          │  │ scandata │  │ wrapper  │  │ venvs    │          │
│  └────┬─────┘  └──────────┘  └──────────┘  └────┬─────┘          │
│       │                                          │ ro             │
│  ┌────┴─────────────────────────────────────┐    │                │
│  │         Cache Maintainer :50052          │    │                │
│  │  pull-galaxy / pull-requirements /       ├────┘                │
│  │  clone-org → /cache (rw)                 │                     │
│  └──────────────────────────────────────────┘                     │
└──────────────────────────────────────────────────────────────────┘

     ┌──────────┐
     │   CLI    │  podman run --rm --pod apme-pod
     │ (on-the  │  -v $(pwd):/workspace:ro,Z
     │  -fly)   │  apme-cli:latest apme-scan scan .
     └──────────┘
```

## Services

| Service | Image | Port | Role |
|---------|-------|------|------|
| **Primary** | `apme-primary` | 50051 | Runs the engine (parse → annotate → hierarchy); fans out `ValidateRequest` to all validators in parallel; merges, deduplicates, and returns violations |
| **Native** | `apme-native` | 50055 | Python rules operating on deserialized `scandata` (the full in-memory model). Rules L026–L056, R101–R501 |
| **OPA** | `apme-opa` | 50054 | OPA binary (REST on 8181 internally) + Python gRPC wrapper. Rego rules L001–L025, R118 on the hierarchy JSON |
| **Ansible** | `apme-ansible` | 50053 | Ansible-runtime checks using pre-built venvs (ansible-core 2.18/2.19/2.20). Syntax check, argspec validation, FQCN resolution, deprecation. Rules L057–L059, M001–M004 |
| **Cache Maintainer** | `apme-cache-maintainer` | 50052 | Populates the collection cache from Galaxy and GitHub orgs. Writes to `/cache`; Ansible reads it `ro` |
| **CLI** | `apme-cli` | — | Ephemeral. Reads project files, builds chunked `ScanRequest`, calls `Primary.Scan`, prints violations. Run with `--pod apme-pod` and CWD mounted |

## gRPC service contracts

Proto definitions live in `proto/apme/v1/`. Generated Python stubs in `src/apme/v1/`.

### Primary (`primary.proto`)

```protobuf
service Primary {
  rpc Scan(ScanRequest) returns (ScanResponse);
  rpc Health(HealthRequest) returns (HealthResponse);
}
```

The CLI sends a `ScanRequest` containing the project files as a chunked filesystem (`repeated File`), an optional `ScanOptions` (ansible-core version, collection specs), and a `scan_id`. Primary returns `ScanResponse` with merged violations.

### Validator (`validate.proto`) — unified contract

```protobuf
service Validator {
  rpc Validate(ValidateRequest) returns (ValidateResponse);
  rpc Health(HealthRequest) returns (HealthResponse);
}
```

Every validator container implements this service. The `ValidateRequest` carries everything any validator might need:

| Field | Type | Used by |
|-------|------|---------|
| `project_root` | `string` | All |
| `files` | `repeated File` | Ansible (writes to temp dir) |
| `hierarchy_payload` | `bytes` (JSON) | OPA, Ansible |
| `scandata` | `bytes` (jsonpickle) | Native |
| `ansible_core_version` | `string` | Ansible |
| `collection_specs` | `repeated string` | Ansible |

Each validator ignores the fields it doesn't need. This keeps the contract uniform — adding a new validator means implementing one RPC and choosing which fields to consume.

### CacheMaintainer (`cache.proto`)

```protobuf
service CacheMaintainer {
  rpc PullGalaxy(PullGalaxyRequest) returns (PullGalaxyResponse);
  rpc PullRequirements(PullRequirementsRequest) returns (PullRequirementsResponse);
  rpc CloneOrg(CloneOrgRequest) returns (CloneOrgResponse);
  rpc Health(HealthRequest) returns (HealthResponse);
}
```

### Common types (`common.proto`)

- **`Violation`** — `rule_id`, `level`, `message`, `file`, `line` (int or range), `path`
- **`File`** — `path` (relative), `content` (bytes)
- **`HealthRequest` / `HealthResponse`** — status string

## Parallel validator fan-out

Primary calls all configured validators concurrently using `concurrent.futures.ThreadPoolExecutor`:

```
              ┌─► Native  ─── violations ──┐
              │                             │
Primary ──────┼─► OPA     ─── violations ──┼──► merge + dedup + sort
              │                             │
              └─► Ansible ─── violations ──┘
```

Wall-clock time = `max(native, opa, ansible)` instead of `sum`. Each validator is discovered by environment variable (`NATIVE_GRPC_ADDRESS`, `OPA_GRPC_ADDRESS`, `ANSIBLE_GRPC_ADDRESS`). If a variable is unset, that validator is skipped.

## Serialization

| Data | Format | Wire type | Producer | Consumer |
|------|--------|-----------|----------|----------|
| Hierarchy payload | JSON (`json.dumps`) | `bytes` in protobuf | Engine (Primary) | OPA, Ansible |
| Scandata | jsonpickle (`jsonpickle.encode`) | `bytes` in protobuf | Engine (Primary) | Native |
| Violations | Protobuf `Violation` messages | gRPC | All validators | Primary |
| Project files | Protobuf `File` messages | gRPC | CLI | Primary, Ansible |

**jsonpickle** is used for scandata because the engine's in-memory model (`SingleScan`) contains complex Python objects (trees, contexts, specs, annotations) that standard JSON cannot represent. jsonpickle preserves types for round-trip deserialization.

## OPA container internals

The OPA container runs a multi-process architecture:

1. **OPA binary** starts as a REST server on `localhost:8181` with the Rego bundle mounted
2. **`entrypoint.sh`** waits for OPA to become healthy
3. **`apme-opa-validator`** (Python gRPC wrapper) starts on port 50054, receives `ValidateRequest`, extracts `hierarchy_payload`, POSTs it to the local OPA REST API, and converts the response to `ValidateResponse`

This keeps OPA's native REST interface intact while presenting a uniform gRPC contract to Primary.

## Volumes

| Volume | Mount | Services | Access |
|--------|-------|----------|--------|
| **cache** | `/cache` | Cache Maintainer (rw), Ansible (ro) | Collection cache (Galaxy + GitHub) |
| **workspace** | `/workspace` | CLI (ro) | Project being scanned (mounted from host CWD) |

## Port map

| Port | Service | Protocol |
|------|---------|----------|
| 50051 | Primary | gRPC |
| 50052 | Cache Maintainer | gRPC |
| 50053 | Ansible | gRPC |
| 50054 | OPA | gRPC (wrapper; OPA REST on 8181 internal) |
| 50055 | Native | gRPC |

## Scaling

**Scale pods, not services within a pod.** Each pod is a self-contained stack (Primary + Native + OPA + Ansible + Cache Maintainer) that can process a scan request end-to-end.

```
                    ┌─────────────┐
  ScanRequest ────► │ Load        │
                    │ Balancer    │
                    │ (K8s Svc)   │
                    └──┬──┬──┬────┘
                       │  │  │
              ┌────────┘  │  └────────┐
              ▼           ▼           ▼
         ┌─────────┐ ┌─────────┐ ┌─────────┐
         │ Pod 1   │ │ Pod 2   │ │ Pod 3   │
         │ (full   │ │ (full   │ │ (full   │
         │  stack) │ │  stack) │ │  stack) │
         └─────────┘ └─────────┘ └─────────┘
```

Within a pod, containers share `localhost` — no config change needed. If a single validator is the bottleneck for one request, the fix is parallelism *inside* that validator (e.g., task-level concurrency), not more containers.

The Cache Maintainer is the one exception: it could be extracted to a shared service across pods if multiple pods need to share a single cache volume. For single-pod deployments this is unnecessary.

## Health checks

The CLI `health-check` subcommand calls `Health` on all services and reports status:

```bash
apme-scan health-check --primary-addr 127.0.0.1:50051
```

Primary, Native, OPA, Ansible, and Cache Maintainer all implement the `Health` RPC. A service returning `status: "ok"` is healthy; any gRPC error marks it degraded.
