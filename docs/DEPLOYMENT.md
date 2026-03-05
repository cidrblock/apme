# Deployment

## Podman pod (recommended)

The primary deployment target is a Podman pod. All backend services run in a single pod sharing `localhost`; the CLI is run on-the-fly outside the pod with the project directory mounted.

### Prerequisites

- Podman (rootless)
- `loginctl enable-linger $USER` (for rootless runtime directory)
- SELinux: volume mounts use `:Z` for private labeling

### Build

From the repo root:

```bash
./containers/podman/build.sh
```

This builds six images:

| Image | Dockerfile | Purpose |
|-------|------------|---------|
| `apme-primary:latest` | `containers/primary/Dockerfile` | Orchestrator + engine |
| `apme-native:latest` | `containers/native/Dockerfile` | Native Python validator |
| `apme-opa:latest` | `containers/opa/Dockerfile` | OPA + gRPC wrapper |
| `apme-ansible:latest` | `containers/ansible/Dockerfile` | Ansible validator with pre-built venvs |
| `apme-cache-maintainer:latest` | `containers/cache-maintainer/Dockerfile` | Collection cache manager |
| `apme-cli:latest` | `containers/cli/Dockerfile` | CLI client |

### Start the pod

```bash
./containers/podman/up.sh
```

This runs `podman play kube containers/podman/pod.yaml`, which starts the pod `apme-pod` with five containers (Primary, Native, OPA, Ansible, Cache Maintainer). A cache directory (`apme-cache/`) is created in the repo root.

### Run a scan

```bash
cd /path/to/your/ansible/project
/path/to/ansible-forward/containers/podman/run-cli.sh
```

Options:

```bash
containers/podman/run-cli.sh --json .        # JSON output
containers/podman/run-cli.sh --no-native .   # Skip native validator
```

The CLI container joins `apme-pod`, mounts CWD as `/workspace:ro,Z`, and calls `Primary.Scan` at `127.0.0.1:50051`.

### Stop the pod

```bash
podman pod stop apme-pod
podman pod rm apme-pod
```

### Health check

```bash
apme-scan health-check --primary-addr 127.0.0.1:50051
```

Reports status of all services (Primary, Native, OPA, Ansible, Cache Maintainer) with latency.

## Container configuration

### Environment variables

#### Primary

| Variable | Default | Description |
|----------|---------|-------------|
| `APME_PRIMARY_LISTEN` | `0.0.0.0:50051` | gRPC listen address |
| `NATIVE_GRPC_ADDRESS` | — | Native validator address (e.g., `127.0.0.1:50055`) |
| `OPA_GRPC_ADDRESS` | — | OPA validator address (e.g., `127.0.0.1:50054`) |
| `ANSIBLE_GRPC_ADDRESS` | — | Ansible validator address (e.g., `127.0.0.1:50053`) |

If a validator address is unset, that validator is skipped during fan-out.

#### Native

| Variable | Default | Description |
|----------|---------|-------------|
| `APME_NATIVE_VALIDATOR_LISTEN` | `0.0.0.0:50055` | gRPC listen address |

#### OPA

| Variable | Default | Description |
|----------|---------|-------------|
| `APME_OPA_VALIDATOR_LISTEN` | `0.0.0.0:50054` | gRPC listen address |

The OPA binary runs internally on `localhost:8181`; the gRPC wrapper proxies to it.

#### Ansible

| Variable | Default | Description |
|----------|---------|-------------|
| `APME_ANSIBLE_VALIDATOR_LISTEN` | `0.0.0.0:50053` | gRPC listen address |
| `APME_CACHE_ROOT` | `/cache` | Collection cache mount point |

#### Cache Maintainer

| Variable | Default | Description |
|----------|---------|-------------|
| `APME_CACHE_MAINTAINER_LISTEN` | `0.0.0.0:50052` | gRPC listen address |
| `APME_CACHE_ROOT` | `/cache` | Collection cache directory |

### Volumes

| Name | Host path | Container mount | Services | Access |
|------|-----------|-----------------|----------|--------|
| `cache` | `apme-cache/` | `/cache` | Cache Maintainer, Ansible | rw (cache-maintainer), ro (ansible) |
| workspace | CWD (CLI only) | `/workspace` | CLI | ro |

## OPA container details

The OPA container uses a multi-stage Dockerfile:

1. **Stage 1**: Copies the `opa` binary from `docker.io/openpolicyagent/opa:latest`
2. **Stage 2**: Python slim image with `grpcio`, project code, and the Rego bundle

At runtime, `entrypoint.sh`:

1. Starts OPA as a REST server: `opa run --server --addr :8181 /bundle`
2. Waits for OPA to become healthy (polls `/health`)
3. Starts the Python gRPC wrapper (`apme-opa-validator`)

The Rego bundle is baked into the image at build time (no volume mount needed).

### Ansible container details

The Ansible container pre-builds venvs for multiple ansible-core versions during `podman build`:

```
/opt/apme-venvs/
  ├── 2.18/    # venv with ansible-core==2.18.*
  ├── 2.19/    # venv with ansible-core==2.19.*
  └── 2.20/    # venv with ansible-core==2.20.*
```

`prebuild-venvs.sh` runs during the Docker build to create these. At runtime, the validator selects the appropriate venv based on `ansible_core_version` from the `ValidateRequest`.

Collections from the cache volume are symlinked or copied into the venv's `site-packages/ansible_collections/` directory so they're on the Python path (no `ANSIBLE_COLLECTIONS_PATH` or `ansible.cfg` needed).

## Local development (no containers)

For development and testing without containers:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e ".[dev]"

# Run a scan (in-process mode)
apme-scan /path/to/project

# OPA evaluation uses Podman by default; to use a local opa binary:
OPA_USE_PODMAN=0 apme-scan .
```

In-process mode runs the engine and validators (Native, OPA) in the same process. The Ansible validator is not available in this mode (requires pre-built venvs).

## Troubleshooting

See [PODMAN_OPA_ISSUES.md](PODMAN_OPA_ISSUES.md) for common Podman rootless issues:

- `/run/libpod: permission denied` — run in a real login shell, enable linger
- Short-name resolution — use fully qualified image names (`docker.io/...`)
- `/bundle: permission denied` — use `--userns=keep-id` and `:z` volume suffix
