# ADR-024: Remove Legacy ARI Code Paths from the Integrated Engine

## Status

Proposed

## Date

2026-03-20

## Context

When the ARI (Ansible Risk Insights) engine was brought into APME (ADR-003), it arrived with a full standalone application surface: a CLI for scanning content, a RAM (Risk Assessment Model) subsystem for persisting and querying findings on disk, human-readable report formatters, and a parser export path that writes `*.json` artifacts to an output directory. All of these existed to support ARI's original "scan offline, accumulate a knowledge base, report to a terminal" workflow.

APME's current architecture is fundamentally different:

```
Content arrives at Primary (gRPC) →
  Engine ingests, builds hierarchy/tree + scandata →
    Primary fans out to Validators over gRPC →
      Validators return violations →
        Primary merges, classifies, returns response
```

The CLI concern now lives exclusively in `src/apme_engine/cli/` (the `apme-scan` script). No `ari`/`ram` command is registered in `pyproject.toml`. The engine is a library called by the Primary daemon, not a standalone command.

Given this architecture, several ARI-era subsystems have no call sites in the production path and no registered entrypoints:

| Subsystem | Path | Status |
|-----------|------|--------|
| ARI engine CLI | `src/apme_engine/engine/cli/` | Dead — not in `[project.scripts]`, `engine/__init__.main()` is unreachable |
| RAM generator | `src/apme_engine/engine/ram_generator.py` | Dead — no caller outside legacy CLI |
| RAM client / model | `src/apme_engine/engine/risk_assessment_model.py` | Dead — only referenced by scanner RAM hooks and engine CLI |
| Scanner RAM hooks | `src/apme_engine/engine/scanner.py` (RAM methods) | Dead — RAM read/write flags never set by production callers |
| Findings persistence | `src/apme_engine/engine/findings.py` (`dump`, `save_rule_result`) | Dead — file writes not part of gRPC runtime contract |
| ARI report formatting | `src/apme_engine/engine/utils.py` (`report_to_display`, `summarize_findings*`) | Dead — no terminal output in gRPC runtime |
| Parser object dump | `src/apme_engine/engine/parser.py` (`_dump_object_list`, object JSON exports) | Dead — filesystem export not part of payload contract |
| Engine rules placeholder | `src/apme_engine/engine/rules/` | Placeholder only — `__init__.py` states rules moved to `validators.native.rules` |

### What Must Be Kept

The following ARI-derived code remains actively used across the gRPC boundary and must **not** be removed:

- `risk_detector.detect(...)` — called inside `validators.native` to produce `data_report["ari_result"]`
- `ARIResult` / `TargetResult` / `NodeResult` / `RuleResult` model shape — `validators.native._extract_results()` walks this structure to produce `Violation` protos
- Scanner hierarchy and `SingleScan` / `ScanContext` — the payload that Primary passes to validators
- `Findings.report` field (in-memory) — carries `ari_result` consumed by the native validator within the same process

---

## Questions to Answer / Alignment Checklist

Before code deletion begins, the team must answer the following:

- [ ] **Q1 — Engine CLI entrypoint reachability.** Is `apme_engine.engine.main()` reachable from any registered script, CI job, deployment script, or documented developer workflow? Confirm it is not in `pyproject.toml [project.scripts]` and not called by any test or CI step.
- [ ] **Q2 — RAM in developer/CI workflows.** Is the RAM KB (generate/update/search/diff/release) used by any developer, CI job, or pre-built artifact? Confirm `ram_generator.py` and `engine/cli/ram/` have no callers outside the engine CLI itself.
- [ ] **Q3 — `Findings.dump()` usage.** Does any code path outside `scanner.save_findings` / `scanner.save_rule_result` call `Findings.dump()`? Confirm by searching all callers.
- [ ] **Q4 — `save_rule_result` / `save_findings` usage.** Do any tests, CI steps, or production callers set `do_save=True` or pass `out_dir` to `ARIScanner.evaluate()`? Confirm no production path enables file output.
- [ ] **Q5 — `report_to_display` / `summarize_findings` usage.** Are these called from anywhere outside the engine CLI or abandoned tests? Confirm all call sites.
- [ ] **Q6 — `_dump_object_list` / parser object exports.** Is `objects=True` ever passed to `ARIScanner.evaluate()` in production? Confirm all callers of `objects` flag.
- [ ] **Q7 — `engine/rules/` compatibility shim.** Does any code `import apme_engine.engine.rules` expecting a rules directory? Confirm the native validator's `default_rules_dir` doesn't reference this path.
- [ ] **Q8 — Native validator RAM dependency.** Does the native validator or Primary ever set `read_ram=True` or `write_ram=True` when constructing `ARIScanner`? Confirm these are always `False` in the gRPC path.
- [ ] **Q9 — `risk_assessment_model.RAMClient` import chain.** `tree.py` and `models.py` import `RAMClient`. Confirm these imports are guarded (`TYPE_CHECKING`) or used only in dead paths before removing `risk_assessment_model.py`.
- [ ] **Q10 — Test coverage of legacy paths.** Do any existing tests exercise the RAM, engine CLI, or report-formatting paths? If yes, decide whether to delete those tests or replace them with contract tests for the new boundary.

---

## Analysis Guidance

### How to Verify Call Sites

For each subsystem, run the following checks before deleting:

1. **Grep for direct imports:**
   ```
   grep -rEn "from.*engine\.cli|import.*engine\.cli" src/ tests/
   grep -rEn "ram_generator|RAMClient|risk_assessment_model" src/ tests/
   grep -rEn "report_to_display|summarize_findings" src/ tests/
   grep -rEn "_dump_object_list|objects=True" src/ tests/
   grep -rEn "save_rule_result|save_findings|register_findings_to_ram|register_indices_to_ram" src/ tests/
   grep -rn "apme_engine\.engine\.rules" src/ tests/
   ```

2. **Grep for registered entrypoints:**
   ```
   grep -n "engine" pyproject.toml
   ```
   Confirm only `apme_engine.cli:main` is registered and no `apme_engine.engine:main` entry exists.

3. **Grep for constructor flags in production callers:**
   ```
   grep -rn "ARIScanner(" src/ tests/
   ```
   For each call site, verify `do_save`, `read_ram`, `write_ram`, `read_ram_for_dependency` are all `False` or absent in the gRPC-path callers.

4. **Trace `RAMClient` import guards:**
   ```
   grep -n "RAMClient\|TYPE_CHECKING" src/apme_engine/engine/tree.py
   grep -n "RAMClient\|TYPE_CHECKING" src/apme_engine/engine/models.py
   ```
   If the import is only under `TYPE_CHECKING`, it is safe to remove with the type annotation.

### How to Verify Entrypoints

- Check `pyproject.toml [project.scripts]` — the registered scripts are the authoritative list of supported CLIs.
- Check `Containerfile*` for any `CMD`/`ENTRYPOINT` that references engine CLI.
- Check `.github/workflows/` for any CI step that calls `ari`, `ari ram`, or `python -m apme_engine.engine`.

### How to Verify Tests

```
grep -rn "ARICLI\|RAMCLI\|ram_generator\|risk_assessment_model\|report_to_display\|summarize_findings\|save_rule_result\|_dump_object_list" tests/
```

Tests covering only dead paths can be deleted. Tests covering `ARIScanner` in the context of hierarchy/payload building must be preserved.

### Incremental Deletion Approach

Delete in this order to minimize broken intermediate states:

1. **Phase 1 — Isolate and remove engine CLI** (lowest risk, no production deps):
   - Delete `src/apme_engine/engine/cli/` (entire subtree)
   - Remove `main()` from `src/apme_engine/engine/__init__.py`
   - Remove `ARICLI`, `RAMCLI` stubs from `engine/__init__.py`
   - Verify: `python -c "from apme_engine.engine import ARIScanner"` still works

2. **Phase 2 — Remove RAM subsystem** (moderate risk, import chain):
   - Remove `src/apme_engine/engine/ram_generator.py`
   - Remove `src/apme_engine/engine/risk_assessment_model.py`
   - Remove RAM hooks from `scanner.py`: `load_metadata_from_ram`, `load_definitions_from_ram`, `register_findings_to_ram`, `register_indices_to_ram`, `save_findings`, RAM constructor params (`read_ram`, `write_ram`, `read_ram_for_dependency`, `ram_client`)
   - Remove `RAMClient` import from `tree.py` and `models.py`
   - Verify: `ARIScanner(root_dir=..., rules_dir=...)` constructs and runs without error

3. **Phase 3 — Remove report formatting and parser export** (low risk, confirm call sites):
   - Remove `report_to_display`, `summarize_findings`, `summarize_findings_data`, `show_all_ram_metadata`, `diff_files_data`, `show_diffs` from `utils.py`
   - Remove `_dump_object_list` and `objects` parameter path from `parser.py`
   - Remove `do_save`, `save_only_rule_result` (the `evaluate()` parameter that controls whether only rule results are written, distinct from the `save_rule_result` scanner method), and `out_dir` parameters from `ARIScanner.evaluate()` if no longer needed
   - Verify: native validator end-to-end test passes

4. **Phase 4 — Remove findings persistence** (moderate risk, `Findings` used internally):
   - Remove `Findings.dump()` and `Findings.save_rule_result()` methods from `findings.py`
   - Remove `findings.py` lock/unlock helpers if only used by persistence methods
   - Keep `Findings` dataclass if still used as in-memory container by scanner/native validator
   - Verify: native validator still reads `findings.report["ari_result"]` correctly

5. **Phase 5 — Remove engine rules placeholder**:
   - Delete `src/apme_engine/engine/rules/` directory
   - Remove any `default_rules_dir` references pointing at `engine/rules/`
   - Verify: native validator's `default_rules_dir` points at `validators.native.rules` correctly

---

## Decision Trees

### Subsystem 1: Engine CLI (`src/apme_engine/engine/cli/**`)

```
Q: Is `apme_engine.engine.main()` registered in [project.scripts]?
│
├─ YES → The CLI is a supported entrypoint.
│        ACTION: Do NOT delete. Add integration test. Document supported commands.
│
└─ NO → Confirmed: not in pyproject.toml scripts.
         │
         Q: Is it called by any Containerfile CMD/ENTRYPOINT or CI step?
         │
         ├─ YES → Treat as semi-supported. Gate behind feature flag or remove from Containerfile.
         │        ACTION: Document removal timeline, deprecate explicitly.
         │
         └─ NO → Confirmed dead entrypoint.
                  │
                  Q: Are there tests that exercise ARICLI or RAMCLI directly?
                  │
                  ├─ YES → Evaluate test value: if testing legacy path only, delete the tests too.
                  │        ACTION: Delete tests + delete `src/apme_engine/engine/cli/`.
                  │
                  └─ NO → No tests, no production callers.
                           ACTION (RECOMMENDED): Delete `src/apme_engine/engine/cli/` (entire subtree),
                           remove `main()` and CLI stubs from `engine/__init__.py`.
```

**Expected outcome:** Delete `src/apme_engine/engine/cli/` and clean up `engine/__init__.py`.

---

### Subsystem 2: RAM / Risk Assessment Model

This covers `ram_generator.py`, `risk_assessment_model.py`, and the RAM hooks in `scanner.py`.

```
Q: Is RAM KB generation used in any developer, CI, or deployment workflow?
│
├─ YES → RAM is an active feature.
│        Q: Is it supported as an APME feature or a personal dev tool?
│        ├─ Supported feature → Create a REQ, keep code, add tests.
│        └─ Personal dev tool → Remove from main codebase, document in CONTRIBUTING.md.
│
└─ NO → RAM is not an active feature. Confirmed by: no [project.scripts] entry,
         no CI reference, no Containerfile reference.
         │
         Q: Do the scanner's RAM constructor flags (read_ram, write_ram) default
            to False and are never overridden by production callers?
         │
         ├─ NO (some caller sets them True) → Find and audit that caller.
         │   ├─ Caller is test-only → Delete the test + remove RAM code.
         │   └─ Caller is production → Do NOT delete; it is live code.
         │
         └─ YES → All production callers use defaults (False/False).
                   │
                   Q: Do tree.py and models.py import RAMClient under TYPE_CHECKING
                      or as a live runtime import?
                   │
                   ├─ Live import → Must remove annotation + import together with RAMClient deletion.
                   └─ TYPE_CHECKING only → Safe to remove the annotation when deleting risk_assessment_model.py.
                   │
                   ACTION (RECOMMENDED):
                   - Delete `ram_generator.py` and `risk_assessment_model.py`.
                   - Strip RAM hooks from `scanner.py`:
                     load_metadata_from_ram, load_definitions_from_ram,
                     register_findings_to_ram, register_indices_to_ram,
                     save_findings, save_rule_result (RAM path),
                     ram_client field, read_ram/write_ram/read_ram_for_dependency params.
                   - Remove RAMClient imports from tree.py and models.py.
```

**Expected outcome:** Delete `ram_generator.py`, `risk_assessment_model.py`; strip RAM methods and constructor params from `scanner.py`; clean up import chains.

---

### Subsystem 3: Findings Persistence (`findings.py` — `dump`, `save_rule_result`)

```
Q: Is Findings.dump() called by any production code path?
│
├─ YES → Identify the caller.
│   ├─ Caller is scanner.save_findings (which is a RAM hook) → Covered by Subsystem 2 deletion.
│   └─ Caller is something else → Audit and decide independently.
│
└─ NO → dump() is only called from dead paths (scanner RAM hooks, engine CLI).
         │
         Q: Is Findings.save_rule_result() called by any production code path?
         │
         ├─ YES (not via scanner.save_rule_result) → Audit that caller.
         │
         └─ NO → save_rule_result() is only triggered when do_save=True, which
                  is never set in the gRPC path.
                  │
                  Q: Is the Findings dataclass itself used as an in-memory
                     container in the scanner or native validator?
                  │
                  ├─ YES → Keep the dataclass; remove only the dump/save_rule_result methods
                  │        and the lock helpers used exclusively by those methods.
                  │
                  └─ NO → Delete findings.py entirely.
                  │
                  ACTION (RECOMMENDED):
                  - Remove Findings.dump() and Findings.save_rule_result() methods.
                  - Remove lock_file/unlock_file/remove_lock_file helpers from utils.py
                    if they are only used by dump().
                  - Retain the Findings dataclass if scanner or native validator
                    still uses it as an in-memory result container.
```

**Expected outcome:** Remove `dump()` and `save_rule_result()` from `findings.py`; retain the `Findings` dataclass if referenced internally.

---

### Subsystem 4: Human-readable ARI Report Formatting (`utils.py`)

Functions: `report_to_display`, `summarize_findings`, `summarize_findings_data`, `show_all_ram_metadata`, `diff_files_data`, `show_diffs`

```
Q: Is report_to_display() called by any code outside engine/cli/?
│
├─ YES → Identify the caller.
│   ├─ Caller is scanner.py (print path, silent=False) → Remove the silent/pretty/output_format
│   │   path from evaluate(); these are only activated by the actual legacy ARI CLI flags
│   │   `--json`, `--yaml`, and `--silent` defined in `src/apme_engine/engine/cli/__init__.py`.
│   └─ Caller is production gRPC path → Do NOT remove; audit the output destination.
│
└─ NO → Only called from engine CLI (silent=False path) or test.
         │
         Q: Is summarize_findings() called by any production code outside engine/cli/?
         │
         ├─ YES → Audit. If it provides value, keep it but rename to remove "ARI" branding.
         │
         └─ NO → Only called from engine CLI or dead scanner path.
                  │
                  ACTION (RECOMMENDED):
                  - Remove report_to_display(), summarize_findings(),
                    summarize_findings_data() from utils.py.
                  - Remove show_all_ram_metadata(), diff_files_data(), show_diffs()
                    (these are exclusively RAM/diff CLI helpers).
                  - Remove the silent, pretty, output_format fields and their
                    conditional branches from ARIScanner.
```

**Expected outcome:** Remove ARI report/summarize helpers and RAM display utilities from `utils.py`; strip `silent`/`pretty`/`output_format` from `ARIScanner` if those are only set by the dead CLI.

---

### Subsystem 5: Parser JSON Dump / Object Export (`parser.py`)

Function: `_dump_object_list`; path guarded by `objects=True` parameter to `ARIScanner.evaluate()`.

```
Q: Is objects=True ever passed to ARIScanner.evaluate() by production callers?
│
├─ YES → Identify the caller.
│   ├─ Caller is engine CLI (--objects flag) → Dead path; covered by CLI deletion.
│   └─ Caller is gRPC path → Keep _dump_object_list; document as debug export.
│
└─ NO → objects=True is only set by the dead CLI --objects flag.
         │
         Q: Are the collections.json / roles.json / tasks.json artifacts consumed
            by any downstream process, test fixture, or CI step?
         │
         ├─ YES → Keep the export path; document it as a supported debug artifact.
         │
         └─ NO → No downstream consumers confirmed.
                  │
                  ACTION (RECOMMENDED):
                  - Remove _dump_object_list() from parser.py.
                  - Remove the objects parameter and its conditional block from
                    ARIScanner.evaluate() and scanner.py.
                  - Remove the out_dir parameter from evaluate() if it is only
                    used for objects output and save_rule_result.
```

**Expected outcome:** Remove `_dump_object_list`, the `objects` parameter, and `out_dir` parameter from `parser.py` and `scanner.py` once confirmed no production callers pass them.

---

### Subsystem 6: Engine Rules Placeholder (`src/apme_engine/engine/rules/`)

```
Q: Does any code import from apme_engine.engine.rules?
│
├─ YES → Identify the importer.
│   ├─ Importer expects rules to live here → Redirect to validators.native.rules.
│   └─ Importer is for compatibility shim → Evaluate whether shim is still needed.
│
└─ NO → Nothing imports from engine.rules.
         │
         Q: Does ARIScanner or config.rules_dir reference engine/rules/ as a path?
         │
         ├─ YES → Update the path to point at validators.native.rules,
         │        then remove the placeholder.
         │
         └─ NO → The placeholder exists purely as documentation artifact.
                  │
                  ACTION (RECOMMENDED):
                  - Delete src/apme_engine/engine/rules/ directory.
                  - Confirm config.rules_dir does not resolve to this path.
                  - Update any documentation that references engine/rules/.
```

**Expected outcome:** Delete `src/apme_engine/engine/rules/`; update `config.rules_dir` if needed to point at `validators.native.rules`.

---

## Decision

**Remove all ARI-era code paths that exist solely to support standalone ARI scanning, RAM KB management, or terminal report output.**

The engine's supported contract going forward is:

> **Engine ingests content, builds hierarchy/tree and scandata, hands the `ScanContext` to Primary, which fans it out to validators over gRPC. No file output, no RAM KB, no terminal formatting, no ARI CLI.**

This decision updates and narrows the scope of ADR-003 (which brought the ARI engine in as a "full integration"). The integration was correct; retaining the full ARI CLI/RAM/reporting surface was not explicitly decided and is now explicitly rejected.

### What Is Being Removed

1. `src/apme_engine/engine/cli/` — ARI and RAM CLI entrypoints
2. `src/apme_engine/engine/ram_generator.py` — RAM KB batch generator
3. `src/apme_engine/engine/risk_assessment_model.py` — RAM client, storage layout, release/diff/search helpers
4. RAM hooks in `src/apme_engine/engine/scanner.py` — `load_*_from_ram`, `register_*_to_ram`, `save_findings`, `save_rule_result` (RAM path), `ram_client`, `read_ram`/`write_ram`/`read_ram_for_dependency` constructor parameters
5. Persistence methods in `src/apme_engine/engine/findings.py` — `dump()`, `save_rule_result()`
6. ARI report formatting in `src/apme_engine/engine/utils.py` — `report_to_display`, `summarize_findings*`, `show_all_ram_metadata`, `diff_files_data`, `show_diffs`
7. Parser object dump in `src/apme_engine/engine/parser.py` — `_dump_object_list`, `objects` parameter path
8. `src/apme_engine/engine/rules/` — placeholder package

### What Is Not Being Removed

- `risk_detector.detect(...)` and `ARIResult`/`TargetResult`/`NodeResult`/`RuleResult` model shape
- In-memory `Findings` dataclass (if still used as a result container)
- Hierarchy building, tree construction, `ScanContext` and `SingleScan`
- `ARIScanner.evaluate()` core scan path (minus the RAM/file-output branches)

---

## Consequences

### Positive

- Reduced maintenance surface: ~500–1000 lines of ARI-era code removed
- Engine contract is explicit: build hierarchy + scandata, nothing more
- Eliminates misleading `ari`, `ari ram` command surface that was never registered or documented in APME
- Reduces import chain complexity (`risk_assessment_model` → `tree.py` / `models.py`)
- Removes file I/O side effects from the scan path, making the engine easier to test in isolation
- Confirms ADR-003's intent: ARI integrated as a library, not as a standalone application

### Negative

- Cannot recover RAM KB capability without reimplementing it; if a future use case needs it, it must be designed as a proper APME feature with a REQ and ADR
- Deleting `summarize_findings` removes a potentially useful debug utility; teams may want to keep it in a `debug.py` module or similar

### Neutral

- No changes to the gRPC API, proto definitions, or validator contracts
- No changes to `risk_detector.detect()` or the native validator's `ari_result` consumption path
- Tests covering the dead paths should be removed; tests covering the hierarchy/payload contract must be kept and extended

---

## Definition of Done

This ADR is complete and the associated clean-up task can be closed when all of the following are true:

- [ ] All items in "Questions to Answer / Alignment Checklist" are answered and documented
- [ ] `src/apme_engine/engine/cli/` is deleted
- [ ] `src/apme_engine/engine/ram_generator.py` is deleted
- [ ] `src/apme_engine/engine/risk_assessment_model.py` is deleted
- [ ] `src/apme_engine/engine/rules/` is deleted
- [ ] RAM hooks removed from `scanner.py` (`load_*_from_ram`, `register_*_to_ram`, `save_findings`, `save_rule_result` RAM path, `ram_client`, `read_ram`, `write_ram`, `read_ram_for_dependency`)
- [ ] `Findings.dump()` and `Findings.save_rule_result()` removed from `findings.py`
- [ ] `report_to_display`, `summarize_findings*`, `show_all_ram_metadata`, `diff_files_data`, `show_diffs` removed from `utils.py`
- [ ] `_dump_object_list` and `objects` parameter removed from `parser.py`
- [ ] `main()`, `ARICLI`/`RAMCLI` stubs removed from `engine/__init__.py`
- [ ] All tests covering only the deleted paths are removed
- [ ] Existing contract tests (hierarchy payload, native validator end-to-end) pass with no changes
- [ ] `python -c "from apme_engine.engine import ARIScanner"` succeeds
- [ ] `apme-scan`, `apme-primary`, and all gRPC daemon entrypoints start cleanly
- [ ] PR reviewed and approved by at least one team member

---

## Implementation Notes

- This ADR documents the **decision and deletion plan only**. Code changes are tracked in a separate task linked to this ADR.
- The analysis checklist questions should be answered in the linked task before any code is deleted.
- Deletion should proceed in the phased order described in "Analysis Guidance — Incremental Deletion Approach" to keep the codebase buildable throughout.

---

## Related Decisions

- ADR-003: Vendor the ARI Engine — this ADR narrows the scope of what "full integration" means; the engine is a library, not a standalone application
- ADR-007: Async gRPC servers — confirms the gRPC-first architecture that makes the ARI CLI unnecessary
- ADR-009: Separate Remediation Engine — confirms that mutation/rewriting is out-of-scope for the engine, further reducing the ARI feature surface needed

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-03-20 | AI agent | Initial proposal |
