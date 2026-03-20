# ADR-024: Scanner Sustainability Refactor — Module Split and Bounded Two-Pass Loop

## Status

Proposed

## Date

2026-03-20

## Context

`src/apme_engine/engine/scanner.py` is 2 046 lines long and contains three
largely distinct concerns in a single file:

1. **Configuration** (`Config` dataclass, environment defaults, logger setup)
2. **Scan state** (`SingleScan` dataclass and ~30 helper methods that mutate it)
3. **Orchestration** (`ARIScanner.evaluate()` — ~430 lines, 30+ parameters)

Additionally, a group of serialisation helpers for the OPA input payload and all
output/persistence side-effects (write rule results, write objects, print
summary) also live in this file.

### High-risk hotspots identified by complexity + side-effect analysis

| # | Function | Lines (approx.) | Risk factors |
|---|----------|-----------------|--------------|
| 1 | `ARIScanner.evaluate()` | 1355–1782 | God-method: config normalisation, RAM cache reads/writes, dependency installation, tree build, rule evaluation, output formatting, **recursive re-entry for spec mutations** |
| 2 | `SingleScan.__post_init__()` | 338–443 | Path-mapping matrix across 5 target types × in-memory vs file × base_dir; sets install dirs, index locations, and caching keys — breakage silently corrupts all downstream outputs |
| 3 | `SingleScan._prepare_dependencies()` | 509–551 | I/O-heavy: downloads, installs, caches; sets `target_path`, `version`, `hash`, `download_url`, `loaded_dependency_dirs` |
| 4 | `SingleScan.construct_trees()` | 797–847 | Bridges definitions into call trees; applies spec-mutation annotations; optionally writes `tree.json` |
| 5 | `SingleScan._node_to_dict()` | 902–996 | OPA payload serialisation tightly coupled to OPA rule schema; silent schema drift if changed incidentally |

### Recursion hazard in `evaluate()`

When `scandata.spec_mutations` is non-empty and differs from
`spec_mutations_from_previous_scan`, `evaluate()` tail-calls **itself** with
the accumulated mutations.  This is currently bounded only by an equality check
(`equal(...)`), but:

- Any regression in the `equal()` helper or in mutation generation could
  produce unbounded recursion.
- The recursive call re-passes all 30+ original parameters, creating a long
  copy-paste parameter list that must stay perfectly in sync.
- Stack-depth-based profiling and debugging become significantly harder.
- Unit testing "what happens on a second pass?" requires invoking the full
  `evaluate()` method rather than a simple loop iteration.

### Module-level side-effects at import time

`scanner.py` performs non-trivial initialisation at import time (e.g., path
joining for `default_data_dir`, `default_rules_dir`).  These side-effects make
the module harder to mock in unit tests.

### Why this matters now

The engine is the critical data path for every validator.  As the project grows,
more contributors will touch `scanner.py` for unrelated reasons (new rule
support, new OPA payload fields, new output formats), generating constant
merge-conflict churn and increasing the risk that one area's change silently
breaks another.

## Decision

**We will split `scanner.py` into six cohesive modules and replace the
spec-mutation tail-call recursion with an explicit bounded two-pass loop.**

### Proposed module boundaries

All files live under `src/apme_engine/engine/`:

| Module | Exports | Responsibility |
|--------|---------|----------------|
| `scanner_config.py` | `Config`, `supported_target_types`, module-level defaults | Configuration dataclass, env-var defaults, logger initialisation policy |
| `scan_state.py` | `SingleScan` | Mutable per-scan state model and all methods that read/write it (`__post_init__`, `make_target_path`, `get_source_path`, `_prepare_dependencies`, `load_definitions_root`, `apply_spec_mutations`, `set_target_object`, `construct_trees`, `resolve_variables`, `annotate`, `count_definitions`, `set_metadata`, `set_metadata_findings`, `load_index`) |
| `dependency_loading.py` | `DependencyLoader` | Populate `scandata.ext_definitions`; encapsulates the `ext_list` construction loop and nested `ARIScanner(load_only=True)` fallback currently embedded in `evaluate()` |
| `opa_payload.py` | `OpaPayloadBuilder` | Produce the hierarchy + annotation dict consumed by OPA; contains `_node_to_dict`, `_annotation_to_dict`, `_location_to_dict`, `_opts_for_opa`, `_json_safe`, `build_hierarchy_payload` |
| `result_writer.py` | `ResultWriter` | All output side-effects: write `rule_result.json`, write `objects.json`, print summary, pretty JSON/YAML output |
| `scanner.py` (retained) | `ARIScanner` | Thin orchestration façade; `evaluate()` delegates to the modules above; retains RAM-read/write helpers and `time_records` plumbing |

### Control-flow change: recursion → two-pass loop

**Current behaviour (pseudocode):**

```python
def evaluate(self, ..., spec_mutations_from_previous_scan=None):
    # ... full scan ...
    if scandata.spec_mutations:
        if equal(scandata.spec_mutations, spec_mutations_from_previous_scan):
            logger.warning("loop detected")
        else:
            return self.evaluate(..., spec_mutations_from_previous_scan=scandata.spec_mutations)
```

**Replacement (semantics-preserving):**

```python
MAX_SPEC_MUTATION_PASSES = 2

def evaluate(self, ...):
    previous_mutations: YAMLDict = {}
    for _pass in range(MAX_SPEC_MUTATION_PASSES):
        scandata = self._run_scan_pass(..., spec_mutations_from_previous_scan=previous_mutations)
        if not scandata.spec_mutations:
            break
        if equal(scandata.spec_mutations, previous_mutations):
            logger.warning("Spec mutation loop detected; stopping after pass %d.", _pass + 1)
            break
        previous_mutations = scandata.spec_mutations
    return scandata
```

`_run_scan_pass()` is a private method containing the body of the current
`evaluate()` minus the recursion block.  It accepts
`spec_mutations_from_previous_scan` so the loop-detection logic is unchanged.

The constant `MAX_SPEC_MUTATION_PASSES = 2` makes intent explicit and provides
a hard upper bound that is absent today.

## Alternatives Considered

### Alternative 1: Keep the monolith

**Description**: Leave `scanner.py` as-is and address issues only through
comments and docstrings.

**Pros**:
- Zero refactor risk.
- No import path changes needed.

**Cons**:
- Merge conflicts accumulate as the project grows.
- The recursive hotspot remains a latent infinite-loop risk.
- OPA schema changes silently ripple through unrelated code.
- New contributors cannot easily own a subsystem.

**Why not chosen**: The project is in active development, not maintenance mode.
Technical debt accumulated now multiplies with every subsequent feature.

### Alternative 2: Partial extraction (dependency loading only)

**Description**: Extract only `DependencyLoader` out of `evaluate()`, leaving
everything else in place.

**Pros**:
- Smaller diff, lower risk.
- Removes the highest-complexity loop from `evaluate()`.

**Cons**:
- Does not address the OPA schema coupling.
- Does not address the recursion hazard.
- `scanner.py` still grows as new features land.

**Why not chosen**: Partial extraction leaves the other hotspots unaddressed and
requires a second disruptive refactor later.

### Alternative 3: Keep the recursion, just add a depth guard

**Description**: Add a `_depth` counter parameter to `evaluate()` and raise
`RuntimeError` if it exceeds 2.

**Pros**:
- Minimal change; runtime protection.

**Cons**:
- Adds a parameter with no domain meaning.
- Stack-depth profiling is still harder than a loop.
- Testing the second-pass path still requires full invocation.

**Why not chosen**: An explicit loop is equally safe, easier to reason about,
and does not bloat the already long parameter list.

### Alternative 4: Full rewrite with a `ScanPlan` dataclass

**Description**: Introduce a `ScanPlan` dataclass to separate the
"what to do" (pure) from "doing it" (impure) phases of `evaluate()`.

**Pros**:
- Enables unit testing of decision logic without I/O.
- Cleanest architecture long-term.

**Cons**:
- Higher implementation risk in a single PR.
- Requires agreeing on the exact `ScanPlan` schema before merging.

**Why not chosen at this stage**: The `ScanPlan` concept is valuable but
orthogonal to the file-split.  It can be added in a follow-on PR after the
module split stabilises.

## Consequences

### Positive

- Merge conflict churn in `scanner.py` reduced: each contributor touches only
  the relevant sub-module.
- `ARIScanner.evaluate()` shrinks from ~430 lines to an orchestration skeleton
  of ~100 lines.
- OPA payload schema changes are isolated to `opa_payload.py`; scanner
  orchestration changes cannot accidentally drift the schema.
- Output policy (file writes, summary printing) is isolated to
  `result_writer.py`; the engine can return results without CLI-like side
  effects.
- The bounded two-pass loop eliminates the latent infinite-recursion risk.
- `MAX_SPEC_MUTATION_PASSES` constant documents intent and is trivially
  adjustable.
- Sub-modules are individually testable in isolation.

### Negative

- **Caller import paths change**: any code importing `SingleScan` directly from
  `scanner` must be updated to `scan_state`. This is an accepted trade-off (see
  user decision in prior discussion).
- Initial PR diff is large (mechanical moves).  Reviewers must verify
  behaviour-neutrality carefully.
- IDE navigation improves (smaller files), but contributors must learn the new
  layout.

### Neutral

- `ARIScanner` remains the single public API entry point; all callers that use
  only `ARIScanner.evaluate()` are unaffected.
- `time_records` plumbing stays in `scanner.py` for now; it can be moved to a
  pipeline abstraction in a future PR.

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Circular imports between `scan_state` and `dependency_loading` | Medium | High | `dependency_loading` must depend on `scan_state` (not the reverse); `ARIScanner` injection via parameter avoids back-reference to `scanner` |
| Behaviour change in spec-mutation loop | Low | High | Preserve exact `equal()` call and warning message; add unit tests that assert pass count and mutation values before merging |
| OPA schema drift during move | Low | High | Add golden-payload snapshot tests for `OpaPayloadBuilder` before moving code; assert schema equality in CI |
| Import path breakage in validators or CLI | Medium | Medium | `grep` for all `from .engine.scanner import` references before merging; update all callsites in the same PR |
| Incomplete move (partial function left in old location) | Medium | Medium | Post-move, verify `scanner.py` contains no serialisation helpers (`_node_to_dict`, etc.) via CI lint rule or grep check |

## Implementation Plan

See `docs/scanner-refactor-plan.md` for the full step-by-step checklist and
suggested commit breakdown.

### Acceptance Criteria

1. All existing tests pass with no modifications to test logic (only import path
   updates permitted).
2. `scanner.py` no longer contains `_node_to_dict`, `_annotation_to_dict`,
   `_location_to_dict`, `_opts_for_opa`, `_json_safe`, or `build_hierarchy_payload`.
3. `scanner.py` no longer contains the `Config` dataclass.
4. `scanner.py` no longer contains the `SingleScan` dataclass.
5. `ARIScanner.evaluate()` contains no `return self.evaluate(...)` call.
6. `MAX_SPEC_MUTATION_PASSES = 2` constant is present in `scanner.py` (or
   `scanner_config.py`).
7. `mypy --strict` passes across all new modules (per ADR-018).
8. `ruff check` passes across all new modules (per ADR-014).
9. A snapshot test for `OpaPayloadBuilder.build()` asserts the payload schema
   against a known fixture tree.
10. CI green on `main` after merge.

## Implementation Notes

- **Import order**: create new modules in dependency order —
  `scanner_config.py` → `scan_state.py` → `dependency_loading.py` →
  `opa_payload.py` → `result_writer.py` — before touching `scanner.py`.
- **Circular import guard**: `dependency_loading.py` receives `ARIScanner` as a
  constructor argument (typed as `Any` or via `TYPE_CHECKING` import) to avoid
  a circular reference between `scanner.py` and `dependency_loading.py`.
- **Public `__init__.py`**: if `src/apme_engine/engine/__init__.py` re-exports
  symbols, update it to re-export from the new modules.
- **Type stubs**: no `.pyi` stubs needed; all new modules are typed inline per
  ADR-018.

## Related Decisions

- ADR-003: Vendor the ARI Engine (engine code is owned in-repo, changes are acceptable)
- ADR-014: Ruff linter and prek pre-commit hooks (all new modules must pass ruff)
- ADR-018: mypy strict type checking (all new modules must pass mypy --strict)
- ADR-009: Separate Remediation Engine (remediation operates on parsed model; clean boundaries here help)

## References

- `src/apme_engine/engine/scanner.py` — source of all analysis above
- `docs/scanner-refactor-plan.md` — step-by-step implementation checklist
- Prior conversation: complexity + side-effect analysis of the five highest-risk functions

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-03-20 | Copilot | Initial proposal based on scanner.py analysis |
