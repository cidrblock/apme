# Scanner Refactor Plan: `scanner.py` → Cohesive Modules

**Tracks**: ADR-024 — Scanner Sustainability Refactor
**Status**: Ready for implementation
**Target date**: TBD
**Branch convention**: `refactor/scanner-module-split`

---

## 1. Highest-Risk Functions

These five functions carry the greatest refactor risk due to complexity,
side-effects, or coupling to external schemas.  Address them explicitly at each
step.

| Rank | Function | Location | Risk |
|------|----------|----------|------|
| 1 | `ARIScanner.evaluate()` | `scanner.py` L1355–L1782 | God-method; recursive re-entry for spec mutations; 30+ parameters; RAM I/O + filesystem I/O + output printing all mixed |
| 2 | `SingleScan.__post_init__()` | `scanner.py` L338–L443 | Path-mapping matrix (5 types × in-memory vs file × base_dir); incorrect output breaks all install dirs, index locations, and caching keys |
| 3 | `SingleScan._prepare_dependencies()` | `scanner.py` L509–L551 | Downloads/installs/caches external content; sets `target_path`, `version`, `hash`, `download_url`, `loaded_dependency_dirs` |
| 4 | `SingleScan.construct_trees()` | `scanner.py` L797–L847 | Bridges definitions → call trees; applies spec-mutation annotations; optionally writes `tree.json` |
| 5 | `SingleScan._node_to_dict()` | `scanner.py` L902–L996 | OPA payload serialisation tightly coupled to OPA rule schema; silent schema drift if changed incidentally |

---

## 2. Target Module Tree

```
src/apme_engine/engine/
├── scanner_config.py        # NEW — Config, defaults, supported_target_types
├── scan_state.py            # NEW — SingleScan + all state-mutation helpers
├── dependency_loading.py    # NEW — DependencyLoader (ext_list loop + nested scan)
├── opa_payload.py           # NEW — OpaPayloadBuilder + serialiser helpers
├── result_writer.py         # NEW — ResultWriter (file writes + summary printing)
├── scanner.py               # MODIFIED — ARIScanner only; thin orchestration façade
└── __init__.py              # MODIFIED — re-export any symbols that moved
```

### Module dependency graph (no cycles allowed)

```
scanner_config  ←──────────────────────────────────────┐
scan_state      ← scanner_config                       │
dependency_loading ← scan_state, scanner_config        │ (ARIScanner injected, not imported)
opa_payload     ← scan_state, scanner_config           │
result_writer   ← scan_state, scanner_config           │
scanner.py      ← all of the above ───────────────────→┘
```

`dependency_loading` must **not** import `ARIScanner` at module level.  Pass it
as a constructor argument (typed `Any` or guarded with `TYPE_CHECKING`) to
avoid the `scanner ↔ dependency_loading` cycle.

---

## 3. Interface Contracts

### `DependencyLoader`

```python
# dependency_loading.py
class DependencyLoader:
    def __init__(
        self,
        scanner: Any,            # ARIScanner — injected to avoid circular import
        root_dir: str,
        read_ram: bool,
        read_ram_for_dependency: bool,
        write_ram: bool,
        use_ansible_doc: bool,
        do_save: bool,
    ) -> None: ...

    def load_ext_definitions(
        self,
        scandata: SingleScan,
        *,
        include_test_contents: bool,
        load_all_taskfiles: bool,
    ) -> None:
        """Populate scandata.ext_definitions.
        Allowed mutations: scandata.ext_definitions only.
        """
```

### `OpaPayloadBuilder`

```python
# opa_payload.py
class OpaPayloadBuilder:
    def __init__(self, scandata: SingleScan) -> None: ...

    def build(self, scan_id: str = "") -> YAMLDict:
        """Return the hierarchy + annotation dict for OPA input."""
```

The existing module-level helpers (`_node_to_dict`, `_annotation_to_dict`,
`_location_to_dict`, `_opts_for_opa`, `_json_safe`) become private methods of
`OpaPayloadBuilder`.

### `ResultWriter`

```python
# result_writer.py
class ResultWriter:
    def __init__(
        self,
        do_save: bool,
        silent: bool,
        out_dir: str,
    ) -> None: ...

    def emit(
        self,
        findings: Findings,
        scandata: SingleScan,
        *,
        objects: bool,
        include_test_contents: bool,
        save_only_rule_result: bool,
        raw_yaml: bool,
        yaml_label_list: list[str] | None,
    ) -> None:
        """Write rule_result.json, objects.json, and print summary."""
```

### `scanner.py` after refactor (evaluate skeleton)

```python
MAX_SPEC_MUTATION_PASSES = 2

def evaluate(self, type: str, name: str = "", ...) -> SingleScan | None:
    previous_mutations: YAMLDict = {}
    result: SingleScan | None = None
    for _pass in range(MAX_SPEC_MUTATION_PASSES):
        result = self._run_scan_pass(
            ..., spec_mutations_from_previous_scan=previous_mutations
        )
        if result is None or not result.spec_mutations:
            break
        if equal(result.spec_mutations, previous_mutations):
            if not self.silent:
                logger.warning(
                    "Spec mutation loop detected; stopping after pass %d.", _pass + 1
                )
            break
        previous_mutations = result.spec_mutations
    return result
```

---

## 4. Step-by-Step Implementation Checklist

### Phase 0 — Baseline (before any moves)

- [ ] Run the full test suite; record pass/fail baseline.
- [ ] Run `mypy --strict src/apme_engine/engine/scanner.py`; record existing errors.
- [ ] Run `ruff check src/apme_engine/engine/scanner.py`; record existing warnings.
- [ ] Add a **golden-payload snapshot test** for `SingleScan.build_hierarchy_payload()` (or equivalent) using a minimal fixture tree.  This test must pass before and after every subsequent step.
- [ ] Grep for all import-site references to symbols that will move:
  ```bash
  grep -rn "from.*scanner import\|from.*engine import.*SingleScan\|from.*engine import.*Config" \
      src/ tests/ validators/ --include="*.py"
  ```
  Record the list; it is the import-update checklist for Phase 5.

---

### Phase 1 — Create `scanner_config.py`

**Goal**: extract all configuration and defaults with zero behaviour change.

- [ ] Create `src/apme_engine/engine/scanner_config.py`.
- [ ] Move to `scanner_config.py`:
  - `Config` dataclass (including `__post_init__`)
  - All `default_*` module-level constants:
    - `ARI_CONFIG_PATH`
    - `default_config_path`
    - `default_data_dir`
    - `default_rules_dir`
    - `default_log_level`
    - `default_rules`
    - `default_disable_default_rules`
    - `default_logger_key`
  - `supported_target_types` (if defined in `scanner.py`)
- [ ] In `scanner.py`, replace moved symbols with imports from `scanner_config`.
- [ ] Run `mypy --strict` on `scanner_config.py`; fix all errors.
- [ ] Run `ruff check` on `scanner_config.py`; fix all warnings.
- [ ] Run full test suite; assert no regressions.
- [ ] **Commit**: `refactor(engine): extract Config and defaults to scanner_config.py`

---

### Phase 2 — Create `scan_state.py`

**Goal**: isolate `SingleScan` and all its helpers; this is the largest single
move.

- [ ] Create `src/apme_engine/engine/scan_state.py`.
- [ ] Move to `scan_state.py` (the complete `SingleScan` class including all
  methods):
  - All dataclass fields and their type annotations
  - `__post_init__`
  - `make_target_path`
  - `get_src_root`
  - `get_source_path`
  - `_prepare_dependencies`
  - `create_load_file`
  - `load_definitions_root`
  - `apply_spec_mutations`
  - `set_target_object`
  - `construct_trees`
  - `resolve_variables`
  - `annotate`
  - `count_definitions`
  - `set_metadata`
  - `set_metadata_findings`
  - `load_index`
  - `_node_to_dict` *(temporary — will move to `opa_payload.py` in Phase 4)*
  - `_annotation_to_dict` *(temporary)*
  - `_location_to_dict` *(temporary)*
  - `_opts_for_opa` *(temporary)*
  - `_json_safe` *(temporary)*
  - `build_hierarchy_payload` *(temporary)*
  - `apply_rules` *(temporary — calls payload builder)*
- [ ] Import `scanner_config` symbols (not `scanner`) in `scan_state.py`.
- [ ] In `scanner.py`, replace `SingleScan` with `from .scan_state import SingleScan`.
- [ ] Run golden-payload snapshot test; assert pass.
- [ ] Run `mypy --strict` on `scan_state.py`; fix all errors.
- [ ] Run `ruff check` on `scan_state.py`; fix all warnings.
- [ ] Run full test suite; assert no regressions.
- [ ] **Commit**: `refactor(engine): extract SingleScan to scan_state.py`

---

### Phase 3 — Create `dependency_loading.py`

**Goal**: remove the `ext_list` construction loop and nested
`ARIScanner(load_only=True)` calls from `evaluate()`.

- [ ] Create `src/apme_engine/engine/dependency_loading.py`.
- [ ] Implement `DependencyLoader` per the interface contract in §3 above.
- [ ] Move the following code from `evaluate()` to
  `DependencyLoader.load_ext_definitions()`:
  - `ext_list` construction loop (iterating `scandata.loaded_dependency_dirs`)
  - Duplicate self-reference guard (`is_root` check)
  - Local role path rewrite logic
  - RAM lookup (`load_definitions_from_ram`) for each dependency
  - Fallback `ARIScanner(...).evaluate(load_only=True)` for cache misses
  - `scandata.ext_definitions[key] = ...` assignments
- [ ] Pass `ARIScanner` instance as a constructor argument; import it with
  `TYPE_CHECKING` guard to avoid circular import:
  ```python
  from __future__ import annotations
  from typing import TYPE_CHECKING
  if TYPE_CHECKING:
      from .scanner import ARIScanner
  ```
- [ ] In `evaluate()`, replace the extracted block with:
  ```python
  loader = DependencyLoader(
      scanner=self, root_dir=self.root_dir,
      read_ram=self.read_ram, read_ram_for_dependency=self.read_ram_for_dependency,
      write_ram=self.write_ram, use_ansible_doc=self.use_ansible_doc, do_save=self.do_save,
  )
  loader.load_ext_definitions(scandata, include_test_contents=include_test_contents,
                               load_all_taskfiles=load_all_taskfiles)
  ```
- [ ] Preserve `time_records` begin/end calls around `loader.load_ext_definitions()`.
- [ ] Run `mypy --strict` on `dependency_loading.py`; fix all errors.
- [ ] Run `ruff check` on `dependency_loading.py`; fix all warnings.
- [ ] Run full test suite; assert no regressions.
- [ ] **Commit**: `refactor(engine): extract dependency loading to DependencyLoader`

---

### Phase 4 — Create `opa_payload.py`

**Goal**: isolate all OPA payload serialisation; prevent scanner orchestration
changes from drifting the schema.

- [ ] Create `src/apme_engine/engine/opa_payload.py`.
- [ ] Move from `scan_state.py` to `OpaPayloadBuilder` in `opa_payload.py`:
  - `_node_to_dict` → `OpaPayloadBuilder._node_to_dict`
  - `_annotation_to_dict` → `OpaPayloadBuilder._annotation_to_dict`
  - `_location_to_dict` → `OpaPayloadBuilder._location_to_dict`
  - `_opts_for_opa` → `OpaPayloadBuilder._opts_for_opa`
  - `_json_safe` → `OpaPayloadBuilder._json_safe`
  - `build_hierarchy_payload` → `OpaPayloadBuilder.build`
- [ ] Update `SingleScan.apply_rules()` to call
  `OpaPayloadBuilder(self).build(scan_id)` instead of `self.build_hierarchy_payload(scan_id)`.
- [ ] Run golden-payload snapshot test; assert exact equality.
- [ ] Run `mypy --strict` on `opa_payload.py`; fix all errors.
- [ ] Run `ruff check` on `opa_payload.py`; fix all warnings.
- [ ] Run full test suite; assert no regressions.
- [ ] **Commit**: `refactor(engine): extract OPA payload serialisation to OpaPayloadBuilder`

---

### Phase 5 — Create `result_writer.py`

**Goal**: decouple output side-effects from the orchestration loop.

- [ ] Create `src/apme_engine/engine/result_writer.py`.
- [ ] Move from the tail of `evaluate()` to `ResultWriter.emit()`:
  - `do_save` branching for `rule_result.json` writes
  - `objects` branching for `objects.json` writes
  - `summarize_findings` call and print
  - Pretty JSON/YAML print block (`raw_yaml`, `yaml_label_list`)
  - RAM write calls (`register_*_to_ram`) — *if* consensus is to move them;
    otherwise document them as staying in `scanner.py` and leave a `# TODO` comment
- [ ] In `evaluate()`, replace the extracted tail with:
  ```python
  writer = ResultWriter(do_save=self.do_save, silent=self.silent, out_dir=out_dir)
  writer.emit(findings, scandata, objects=objects, include_test_contents=include_test_contents,
              save_only_rule_result=save_only_rule_result, raw_yaml=bool(raw_yaml),
              yaml_label_list=yaml_label_list)
  ```
- [ ] Run `mypy --strict` on `result_writer.py`; fix all errors.
- [ ] Run `ruff check` on `result_writer.py`; fix all warnings.
- [ ] Run full test suite; assert no regressions.
- [ ] **Commit**: `refactor(engine): extract output side-effects to ResultWriter`

---

### Phase 6 — Replace spec-mutation recursion with bounded loop

**Goal**: eliminate the recursive `return self.evaluate(...)` call.

- [ ] Add constant at module level in `scanner.py`:
  ```python
  MAX_SPEC_MUTATION_PASSES = 2
  ```
- [ ] Rename current `evaluate()` body to `_run_scan_pass()` (private).
  `_run_scan_pass` accepts the same parameters minus `spec_mutations_from_previous_scan`
  which becomes an explicit parameter rather than a passthrough.
- [ ] Rewrite `evaluate()` as the two-pass loop shown in §3 above.
- [ ] Verify the `equal()` helper call and warning message are **identical** to
  what was there before.
- [ ] Write a unit test that:
  1. Creates a mock `_run_scan_pass` that returns spec mutations on pass 1 and
     no mutations on pass 2.
  2. Asserts `evaluate()` calls `_run_scan_pass` exactly twice.
  3. Creates a mock that always returns the same mutations.
  4. Asserts the loop-detection warning fires and `_run_scan_pass` is called at
     most `MAX_SPEC_MUTATION_PASSES` times.
- [ ] Run full test suite; assert no regressions.
- [ ] **Commit**: `refactor(engine): replace spec-mutation recursion with bounded two-pass loop`

---

### Phase 7 — Update import sites and `__init__.py`

- [ ] Re-run the grep from Phase 0 to find all remaining `from .scanner import`
  references to moved symbols.
- [ ] Update each callsite to import from the correct new module.
- [ ] Update `src/apme_engine/engine/__init__.py` to re-export any public symbols
  from new modules (if the `__init__.py` currently re-exports from `scanner`).
- [ ] Run full test suite; assert no regressions.
- [ ] Run `mypy --strict` across `src/apme_engine/`; fix all errors.
- [ ] Run `ruff check` across `src/apme_engine/`; fix all warnings.
- [ ] **Commit**: `refactor(engine): update import sites after scanner module split`

---

### Phase 8 — Final verification

- [ ] Confirm `scanner.py` no longer contains: `_node_to_dict`,
  `_annotation_to_dict`, `_location_to_dict`, `_opts_for_opa`, `_json_safe`,
  `build_hierarchy_payload`, `Config`, `SingleScan`.
- [ ] Confirm `scanner.py` contains no `return self.evaluate(...)` call.
- [ ] Confirm `MAX_SPEC_MUTATION_PASSES = 2` exists.
- [ ] Run golden-payload snapshot test one final time.
- [ ] Run full test suite; assert green.
- [ ] Run `mypy --strict` across `src/`; assert zero new errors vs baseline.
- [ ] Run `ruff check` across `src/`; assert zero new warnings vs baseline.
- [ ] Open PR; link to ADR-024.
- [ ] **Commit**: `chore(engine): post-split cleanup and verification`

---

## 5. Suggested Commit Breakdown

| # | Commit message | Phase |
|---|----------------|-------|
| 1 | `test(engine): add golden-payload snapshot test for build_hierarchy_payload` | 0 |
| 2 | `refactor(engine): extract Config and defaults to scanner_config.py` | 1 |
| 3 | `refactor(engine): extract SingleScan to scan_state.py` | 2 |
| 4 | `refactor(engine): extract dependency loading to DependencyLoader` | 3 |
| 5 | `refactor(engine): extract OPA payload serialisation to OpaPayloadBuilder` | 4 |
| 6 | `refactor(engine): extract output side-effects to ResultWriter` | 5 |
| 7 | `refactor(engine): replace spec-mutation recursion with bounded two-pass loop` | 6 |
| 8 | `refactor(engine): update import sites after scanner module split` | 7 |
| 9 | `chore(engine): post-split cleanup and verification` | 8 |

All commits should be pushed on a single branch `refactor/scanner-module-split`
and merged as a single PR so reviewers can see the full picture.  Individual
commits within the PR allow `git bisect` to isolate regressions.

---

## 6. Testing Strategy

### Pre-existing tests to keep green

Run after every phase commit:
```bash
python -m pytest tests/ -x -q
```

### New tests to add before starting (Phase 0)

1. **Golden-payload snapshot test** (`tests/engine/test_opa_payload_snapshot.py`):
   - Construct a minimal `SingleScan` from a fixture playbook YAML.
   - Call `build_hierarchy_payload()` (pre-refactor) / `OpaPayloadBuilder(scandata).build()` (post-refactor).
   - Assert the returned dict matches a stored JSON fixture exactly.
   - This test guards against silent OPA schema drift throughout all phases.

2. **Spec-mutation loop unit test** (`tests/engine/test_evaluate_mutation_loop.py`):
   - Mock `_run_scan_pass` to inject controlled mutations.
   - Assert two-pass loop terminates correctly under all three cases:
     a. No mutations on pass 1 → exits after 1 pass.
     b. Different mutations on pass 1, none on pass 2 → exits after 2 passes.
     c. Same mutations on both passes → exits after 2 passes with warning log.

### Import-path regression guard (Phase 7)

Add a smoke test that imports each new module and asserts the expected public
symbols are present:
```python
from apme_engine.engine.scanner_config import Config, supported_target_types
from apme_engine.engine.scan_state import SingleScan
from apme_engine.engine.dependency_loading import DependencyLoader
from apme_engine.engine.opa_payload import OpaPayloadBuilder
from apme_engine.engine.result_writer import ResultWriter
from apme_engine.engine.scanner import ARIScanner, MAX_SPEC_MUTATION_PASSES
```

---

## 7. Circular Import Prevention Checklist

| Import | Allowed? | Notes |
|--------|----------|-------|
| `scanner_config` → anything in engine | ✗ | Leaf module; no intra-engine imports |
| `scan_state` → `scanner_config` | ✓ | |
| `scan_state` → `scanner` | ✗ | Would create cycle |
| `dependency_loading` → `scan_state` | ✓ | |
| `dependency_loading` → `scanner` | `TYPE_CHECKING` only | Injected at runtime |
| `opa_payload` → `scan_state` | ✓ | |
| `opa_payload` → `scanner` | ✗ | Not needed |
| `result_writer` → `scan_state` | ✓ | |
| `result_writer` → `scanner` | ✗ | Not needed |
| `scanner` → all of the above | ✓ | Façade imports everything |

If any cycle is detected at runtime (`ImportError: cannot import name ...
circular import`), resolve by:
1. Moving the shared symbol to `scanner_config.py` (if it's a constant/type).
2. Using `TYPE_CHECKING` guards and string annotations.
3. Passing the object as a parameter instead of importing its class.
