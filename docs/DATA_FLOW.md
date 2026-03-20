# Data flow

This document traces a scan request from CLI to violation output, covering every transformation and serialization boundary.

## Request lifecycle

```
User runs:  apme-scan scan /path/to/project
            │
            ▼
┌───────────────────────────────────────────────────────┐
│  CLI (apme_engine/cli/)                                │
│                                                       │
│  1. Walk project directory                            │
│  2. Filter: TEXT_EXTENSIONS, skip SKIP_DIRS,          │
│     exclude >2 MiB and binary files                   │
│  3. Build ScanRequest:                                │
│     - scan_id (uuid)                                  │
│     - project_root (basename)                         │
│     - files[] = File(path=relative, content=bytes)    │
│     - options (ansible_core_version, collection_specs)│
│                                                       │
│  gRPC call: Primary.Scan(ScanRequest) ───────────────────────┐
└───────────────────────────────────────────────────────┘       │
                                                                ▼
┌──────────────────────────────────────────────────────────────────┐
│  Primary (daemon/primary_server.py)                              │
│                                                                  │
│  4. _write_chunked_fs(): write request.files to temp dir         │
│                                                                  │
│  5. run_scan(temp_dir, project_root):                            │
│     ┌────────────────────────────────────────────────────┐       │
│     │  Engine (engine/scanner.py — ARIScanner.evaluate)  │       │
│     │                                                    │       │
│     │  a. load_definitions_root()                        │       │
│     │     Parser.run() → playbooks, roles, taskfiles,    │       │
│     │     tasks, modules, mappings                       │       │
│     │                                                    │       │
│     │  b. construct_trees()                              │       │
│     │     TreeLoader → PlaybookCall → PlayCall →         │       │
│     │     RoleCall → TaskFileCall → TaskCall trees       │       │
│     │                                                    │       │
│     │  c. resolve_variables()                            │       │
│     │     Walk trees, resolve variable references,       │       │
│     │     track set_fact / register / include_vars       │       │
│     │                                                    │       │
│     │  d. annotate()                                     │       │
│     │     RiskAnnotators (per-module: shell, command,     │       │
│     │     get_url, file, copy, etc.) add RiskAnnotations │       │
│     │     to each TaskCall                               │       │
│     │                                                    │       │
│     │  e. build_hierarchy_payload()                      │       │
│     │     Serialize trees → JSON hierarchy:              │       │
│     │     { scan_id, hierarchy: [{root_key, root_type,   │       │
│     │       root_path, nodes: [{type, key, file, line,   │       │
│     │       module, options, module_options,              │       │
│     │       annotations}]}], metadata }                  │       │
│     │                                                    │       │
│     │  Returns: ScanContext                              │       │
│     │    .hierarchy_payload = dict (JSON-serializable)   │       │
│     │    .scandata = SingleScan (full in-memory model)   │       │
│     └────────────────────────────────────────────────────┘       │
│                                                                  │
│  6. Build ValidateRequest:                                       │
│     - hierarchy_payload = json.dumps(ctx.hierarchy_payload)      │
│     - scandata = jsonpickle.encode(ctx.scandata)                 │
│     - files, ansible_core_version, collection_specs              │
│                                                                  │
│  7. Parallel fan-out (asyncio.gather):                           │
│     ┌─────────────────────────────────────────────────────┐      │
│     │                                                     │      │
│     │  ┌─► Native :50055                                  │      │
│     │  │   - jsonpickle.decode(scandata) → SingleScan     │      │
│     │  │   - Build ScanContext, run NativeValidator        │      │
│     │  │   - Python rules on contexts/trees               │      │
│     │  │   → violations[] + ValidatorDiagnostics          │      │
│     │  │                                                  │      │
│     │  ├─► OPA :50054                                     │      │
│     │  │   - json.loads(hierarchy_payload)                 │      │
│     │  │   - POST to local OPA REST (:8181)               │      │
│     │  │   - Rego eval: data.apme.rules.violations        │      │
│     │  │   → violations[] + ValidatorDiagnostics          │      │
│     │  │                                                  │      │
│     │  ├─► Ansible :50053                                 │      │
│     │  │   - Write files to temp dir                      │      │
│     │  │   - Create ephemeral venv (UV-cached)            │      │
│     │  │   - Run AnsibleValidator (syntax, argspec,       │      │
│     │  │     FQCN, deprecation, redirect, removed)        │      │
│     │  │   → violations[] + ValidatorDiagnostics          │      │
│     │  │                                                  │      │
│     │  └─► Gitleaks :50056                                │      │
│     │      - Write files to temp dir                      │      │
│     │      - Run gitleaks detect --no-git                 │      │
│     │      - Filter vault + Jinja false positives         │      │
│     │      → violations[] + ValidatorDiagnostics          │      │
│     │                                                     │      │
│     └─────────────────────────────────────────────────────┘      │
│                                                                  │
│  8. Merge all violations                                         │
│  9. Deduplicate by (rule_id, file, line)                         │
│ 10. Sort by (file, line)                                         │
│ 11. Convert to proto Violation messages                          │
│ 12. Aggregate diagnostics:                                       │
│     - Engine timing (parse, annotate, tree build)                │
│     - Each validator's ValidatorDiagnostics                      │
│     - Fan-out wall-clock, total wall-clock                       │
│                                                                  │
│  Return: ScanResponse(violations, scan_id, diagnostics)          │
└──────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────┐
│  CLI                                          │
│                                               │
│ 13. Print violations (table or --json)        │
│     rule_id | level | file:line | message     │
│                                               │
│ 14. If -v: show validator summaries +         │
│     top 10 slowest rules                      │
│     If -vv: full per-rule breakdown,          │
│     metadata, engine phase timing             │
└───────────────────────────────────────────────┘
```

## Engine pipeline detail

The engine (`ARIScanner.evaluate()`) runs five stages in sequence. All stages operate on the same in-memory model; there is no intermediate serialization between stages.

### Stage 1: Load definitions

`Parser.run()` dispatches by load type (`PROJECT`, `COLLECTION`, `ROLE`, `PLAYBOOK`, `TASKFILE`). Produces:

- `root_definitions` — playbooks, roles, taskfiles, tasks, modules found in the scan target
- `ext_definitions` — external dependencies (collections, roles from cache)
- `mappings` — index of module → FQCN, role → path, etc.

### Stage 2: Construct trees

`TreeLoader` builds directed graphs of call objects:

```
PlaybookCall → PlayCall → RoleCall → TaskFileCall → TaskCall
                        └──────────► TaskCall (play-level tasks)
```

Each node has a `spec` (the parsed YAML structure), `key` (unique identifier), and edges to children. The tree preserves execution order and nesting.

### Stage 3: Resolve variables

Walks the tree and tracks variable definitions (`set_fact`, `register`, `include_vars`, role defaults/vars) and usages. Produces:

- `variable_use` annotations on tasks (which variables are referenced)
- Resolution of `{{ var }}` references where statically determinable

### Stage 4: Annotate

Per-module `RiskAnnotator` subclasses inspect each `TaskCall` and attach `RiskAnnotation` objects:

| Annotator | Risk types |
|-----------|------------|
| `ShellAnnotator` | `CMD_EXEC` |
| `CommandAnnotator` | `CMD_EXEC` |
| `GetUrlAnnotator` | `INBOUND_TRANSFER` |
| `UriAnnotator` | `INBOUND_TRANSFER`, `OUTBOUND_TRANSFER` |
| `CopyAnnotator` | `FILE_CHANGE` |
| `FileAnnotator` | `FILE_CHANGE` |
| `UnarchiveAnnotator` | `FILE_CHANGE`, `INBOUND_TRANSFER` |
| `LineinfileAnnotator` | `FILE_CHANGE` |
| `GitAnnotator` | `INBOUND_TRANSFER` |
| `PackageAnnotator` | `PACKAGE_INSTALL` |

Annotations are attached to the `TaskCall` and serialized into the hierarchy payload's `annotations` array, making them available to OPA rules (e.g., R118 checks for `inbound_transfer`).

### Stage 5: Build hierarchy payload

Serializes the tree into a flat JSON structure consumable by OPA and other payload-based validators:

```json
{
  "scan_id": "uuid",
  "hierarchy": [
    {
      "root_key": "playbook:/path/to/pb.yml",
      "root_type": "playbook",
      "root_path": "/path/to/pb.yml",
      "nodes": [
        {
          "type": "taskcall",
          "key": "task:...",
          "file": "pb.yml",
          "line": 5,
          "module": "ansible.builtin.shell",
          "options": { "name": "Run something", "become": true },
          "module_options": { "_raw_params": "echo hello" },
          "annotations": [
            { "risk_type": "cmd_exec", "detail": { "cmd": "echo hello" } }
          ]
        }
      ]
    }
  ],
  "metadata": { "type": "project", "name": "myproject" }
}
```

## Serialization boundaries

### CLI → Primary (gRPC)

Files are sent as protobuf `File` messages (path + content bytes). This is the "chunked filesystem" pattern — the CLI reads all text files from the project and sends them over the wire so the Primary doesn't need filesystem access.

### Primary → Validators (gRPC)

Two serialization formats in one `ValidateRequest`:

1. **`hierarchy_payload`** — `json.dumps()` → bytes. The complete hierarchy as JSON. Used by OPA (Rego operates on JSON) and Ansible (for reference).

2. **`scandata`** — `jsonpickle.encode()` → bytes. The full `SingleScan` object including trees, contexts, specs, and annotations. Used by Native (needs the in-memory Python object model). jsonpickle preserves Python types for round-trip `decode()`.

### Validators → Primary (gRPC)

Each validator returns `ValidateResponse` containing:
- Protobuf `Violation` messages
- `ValidatorDiagnostics` with per-rule timing, violation counts, and validator-specific metadata

Primary converts violations to dicts, merges, deduplicates, and converts back to proto. It also aggregates all `ValidatorDiagnostics` with engine phase timing into a `ScanDiagnostics` message on the `ScanResponse`.

### Diagnostics flow

```
Engine → EngineDiagnostics (parse_ms, annotate_ms, tree_build_ms, total_ms)
                              ↓
Native  → ValidatorDiagnostics (per-rule timing from detect() records)
OPA     → ValidatorDiagnostics (opa_query_ms, per-rule violation counts)
Ansible → ValidatorDiagnostics (per-phase: syntax, introspect, argspec; venv_build_ms)
Gitleaks→ ValidatorDiagnostics (subprocess_ms, files_written)
                              ↓
Primary aggregates → ScanDiagnostics
                              ↓
ScanResponse.diagnostics → CLI (-v / -vv) or JSON consumer
```

## Violation shape

Every violation, regardless of source validator, has the same structure:

```
rule_id   : string   e.g. "L024", "native:L029", "M002"
level     : string   "error", "warning", "info"
message   : string   human-readable description
file      : string   relative path to file
line      : int      line number (or LineRange {start, end})
path      : string   hierarchy path (e.g. "playbook > play > task")
```

The `rule_id` prefix convention:
- No prefix → OPA rule
- `native:` → native Python rule
- No prefix → Ansible/Modernize rule (M001–M004, L057–L059)

## Local (in-process) mode

When running without the daemon, the CLI auto-starts a local daemon and runs everything in-process:

1. Engine runs directly (no temp dir, no gRPC)
2. `NativeValidator` and `OpaValidator` run in the same process
3. OPA is invoked via Podman (`podman run ... opa eval`) or local binary
4. Results are merged locally

This mode is useful for development and testing but does not support the Ansible validator (which requires pre-built venvs in the container).
