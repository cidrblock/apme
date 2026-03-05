# Native (Python) validator

Runs in-tree Python rules on `context.scandata` from the engine. Rules live in `rules/`.

## Colocated tests

Each rule can have a colocated test file: `*_test.py` next to the rule module (e.g. `R301_non_fqcn_use_test.py` next to `R301_non_fqcn_use.py`). Tests use **Python objects**, not Ansible YAML:

- **`_test_helpers.py`** in `rules/` provides `make_task_spec`, `make_task_call`, `make_role_spec`, `make_role_call`, and `make_context` to build minimal engine objects.
- Tests instantiate the rule class, build a context with the helper, then call `rule.match(ctx)` and `rule.process(ctx)` and assert on the result.

Pytest collects these when run with the rules path (or via `testpaths` in pyproject.toml). Example:

```bash
pytest src/apme_engine/validators/native/rules/ -v
```

To add a test for a new rule: create `Rxxx_rule_name_test.py`, import the rule class and helpers, and add tests that cover “fires when” and “does not fire when” cases.
