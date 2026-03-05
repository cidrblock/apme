# Development guide

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e ".[dev]"
```

## Code organization

```
src/apme_engine/
├── cli.py                  CLI entry point (apme-scan)
├── runner.py               run_scan() → ScanContext
├── opa_client.py           OPA eval (Podman or local binary)
│
├── engine/                 ARI-based scanner
│   ├── scanner.py          ARIScanner.evaluate() pipeline
│   ├── parser.py           YAML/Ansible content parser
│   ├── tree.py             TreeLoader (call graph construction)
│   ├── models.py           SingleScan, TaskCall, RiskAnnotation, etc.
│   ├── variable_resolver.py  variable tracking and resolution
│   └── annotators/         per-module risk annotators
│       ├── base.py         RiskAnnotator base class
│       └── ansible.builtin/  shell, command, copy, file, get_url, ...
│
├── validators/
│   ├── base.py             Validator protocol + ScanContext
│   ├── native/             Python rules
│   │   ├── validator.py    NativeValidator (loads + runs rules)
│   │   ├── risk_detector.py  rule discovery and execution
│   │   ├── rules/          one file per rule + colocated tests
│   │   │   ├── L026_non_fqcn_use.py
│   │   │   ├── L026_non_fqcn_use_test.py
│   │   │   ├── _test_helpers.py
│   │   │   └── rule_versions.json
│   │   └── README.md
│   ├── opa/
│   │   ├── validator.py    OpaValidator (calls opa eval)
│   │   └── bundle/         Rego rules + tests + data
│   │       ├── _helpers.rego
│   │       ├── L001_task_name.rego
│   │       ├── L001_task_name_test.rego
│   │       ├── data.json
│   │       └── README.md
│   └── ansible/
│       ├── validator.py    AnsibleValidator
│       ├── _venv.py        venv resolution
│       └── rules/          L057–L059, M001–M004 + .md docs
│
├── daemon/                 gRPC server implementations
│   ├── primary_server.py   Primary orchestrator (engine + fan-out)
│   ├── primary_main.py     entry point: apme-primary
│   ├── native_validator_server.py
│   ├── native_validator_main.py
│   ├── opa_validator_server.py
│   ├── opa_validator_main.py
│   ├── ansible_validator_server.py
│   ├── ansible_validator_main.py
│   ├── cache_maintainer_server.py
│   ├── cache_maintainer_main.py
│   ├── health_check.py     health check utilities
│   └── violation_convert.py  dict ↔ proto Violation conversion
│
└── collection_cache/       Galaxy/GitHub cache management
```

## Adding a new rule

### Native (Python) rule

1. Create `src/apme_engine/validators/native/rules/L0XX_rule_name.py`:

```python
from apme_engine.validators.native.rules._base import Rule

class L0XXRuleName(Rule):
    rule_id = "L0XX"
    description = "Short description"
    level = "warning"

    def match(self, ctx):
        """Return True if this rule applies to the given context."""
        return ctx.type == "taskcall"

    def process(self, ctx):
        """Yield violations for matching contexts."""
        # ctx.spec has task options, module_options, etc.
        if some_condition(ctx):
            yield {
                "rule_id": self.rule_id,
                "level": self.level,
                "message": self.description,
                "file": ctx.file,
                "line": ctx.line,
                "path": ctx.path,
            }
```

2. Create colocated test `src/apme_engine/validators/native/rules/L0XX_rule_name_test.py`:

```python
from apme_engine.validators.native.rules._test_helpers import make_context
from apme_engine.validators.native.rules.L0XX_rule_name import L0XXRuleName

def test_violation():
    ctx = make_context(type="taskcall", module="ansible.builtin.shell", ...)
    violations = list(L0XXRuleName().process(ctx))
    assert len(violations) == 1
    assert violations[0]["rule_id"] == "L0XX"

def test_pass():
    ctx = make_context(type="taskcall", module="ansible.builtin.command", ...)
    violations = list(L0XXRuleName().process(ctx))
    assert len(violations) == 0
```

3. Create rule doc `src/apme_engine/validators/native/rules/L0XX_rule_name.md` (see [RULE_DOC_FORMAT.md](RULE_DOC_FORMAT.md)).

4. Add the rule ID to `rule_versions.json`.

5. Update `docs/LINT_RULE_MAPPING.md` with the new entry.

### OPA (Rego) rule

1. Create `src/apme_engine/validators/opa/bundle/L0XX_rule_name.rego`:

```rego
package apme.rules

import data.apme.helpers

L0XX_violations[v] {
    node := input.hierarchy[_].nodes[_]
    node.type == "taskcall"
    # rule logic
    v := helpers.violation("L0XX", "warning", "Description", node)
}

violations[v] {
    L0XX_violations[v]
}
```

2. Create colocated test `src/apme_engine/validators/opa/bundle/L0XX_rule_name_test.rego`:

```rego
package apme.rules

test_L0XX_violation {
    result := violations with input as {"hierarchy": [{"nodes": [...]}]}
    count({v | v := result[_]; v.rule_id == "L0XX"}) > 0
}

test_L0XX_pass {
    result := violations with input as {"hierarchy": [{"nodes": [...]}]}
    count({v | v := result[_]; v.rule_id == "L0XX"}) == 0
}
```

3. Create rule doc `src/apme_engine/validators/opa/bundle/L0XX.md`.

### Ansible rule

Ansible rules live in `src/apme_engine/validators/ansible/rules/` and typically require the Ansible runtime (subprocess calls to `ansible-playbook`, `ansible-doc`, or Python imports from ansible-core). Create a `.md` doc for each rule.

## Proto / gRPC changes

Proto definitions: `proto/apme/v1/*.proto`

After modifying a `.proto` file, regenerate stubs:

```bash
./scripts/gen_grpc.sh
```

This generates `*_pb2.py` and `*_pb2_grpc.py` in `src/apme/v1/`. Generated files are checked in.

To add a new service:

1. Create `proto/apme/v1/newservice.proto`
2. Add it to the `PROTOS` array in `scripts/gen_grpc.sh`
3. Run `./scripts/gen_grpc.sh`
4. Implement the servicer in `src/apme_engine/daemon/`
5. Add an entry point in `pyproject.toml`

## Testing

### Test structure

```
tests/
├── test_cli.py                    CLI tests
├── test_opa_client.py             OPA client + Rego eval tests
├── test_scanner_hierarchy.py      Engine hierarchy tests
├── test_validators.py             Validator tests
├── test_validator_servicers.py    gRPC servicer tests
├── test_collection_cache_venv_builder.py
├── test_rule_doc_coverage.py      Asserts every rule has a .md doc
├── rule_doc_parser.py             Parses rule .md frontmatter
├── rule_doc_integration_test.py   Runs .md examples through engine
├── conftest.py                    Shared fixtures
└── integration/
    ├── test_e2e.sh                End-to-end container test
    └── test_playbook.yml          Sample playbook for e2e

src/apme_engine/validators/native/rules/
    *_test.py                      Colocated native rule tests
```

### Running tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_validators.py

# Native rule tests only
pytest src/apme_engine/validators/native/rules/

# With coverage
pytest --cov=src/apme_engine --cov-report=term-missing --cov-fail-under=95

# Integration test (requires Podman + built images)
pytest -m integration tests/integration/test_e2e.py

# Skip image rebuild if already built
APME_E2E_SKIP_BUILD=1 pytest -m integration tests/integration/test_e2e.py

# Keep pod running after test for debugging
APME_E2E_SKIP_TEARDOWN=1 pytest -m integration tests/integration/test_e2e.py
```

### OPA Rego tests

Rego tests run via the OPA binary (Podman or local):

```bash
podman run --rm \
  -v "$(pwd)/src/apme_engine/validators/opa/bundle:/bundle:ro,z" \
  --userns=keep-id -u root \
  docker.io/openpolicyagent/opa:latest test /bundle -v
```

### Coverage target

Coverage is configured at 95% (`fail_under = 95` in `pyproject.toml`). Rule files under `validators/*/rules/` are excluded from coverage measurement (they have colocated tests instead).

## Rule ID conventions

| Prefix | Category | Examples |
|--------|----------|----------|
| **L** | Lint (style, correctness, best practice) | L001–L059 |
| **M** | Modernize (ansible-core metadata) | M001–M004 |
| **R** | Risk/security (annotation-based) | R101–R501, R118 |
| **P** | Policy (legacy, superseded by L058/L059) | P001–P004 |

Rule IDs are independent of the validator that implements them. The user sees rule IDs; the underlying validator is an implementation detail.

See [LINT_RULE_MAPPING.md](LINT_RULE_MAPPING.md) for the complete cross-reference.

## Entry points

Defined in `pyproject.toml`:

| Command | Module | Purpose |
|---------|--------|---------|
| `apme-scan` | `apme_engine.cli:main` | CLI (scan, cache, health-check) |
| `apme-primary` | `apme_engine.daemon.primary_main:main` | Primary daemon |
| `apme-native-validator` | `apme_engine.daemon.native_validator_main:main` | Native validator daemon |
| `apme-opa-validator` | `apme_engine.daemon.opa_validator_main:main` | OPA validator daemon |
| `apme-ansible-validator` | `apme_engine.daemon.ansible_validator_main:main` | Ansible validator daemon |
| `apme-cache-maintainer` | `apme_engine.daemon.cache_maintainer_main:main` | Cache maintainer daemon |
