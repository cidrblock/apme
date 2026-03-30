# ContentGraph Rule Migration Tracker

**Status**: In Progress
**Related**: [ADR-044](/.sdlc/adrs/ADR-044-node-identity-progression-model.md) |
[Research](/.sdlc/research/ari-to-contentgraph-migration.md)

## Summary

| Metric | Count |
|--------|-------|
| Total native rules | 96 |
| Ported to GraphRule | 43 |
| Remaining | 53 |
| Migration % | 44.8% |

## Ported Rules (27)

### Phase 2A — Scanner bootstrap + R108 (PR #138)

| Rule | Name | Category |
|------|------|----------|
| R108 | PrivilegeEscalation | INHERITED_PROPERTY |

### Phase 2B — INHERITED_PROPERTY batch (PR #140)

| Rule | Name | Category |
|------|------|----------|
| L033 | UnconditionalOverride | INHERITED_PROPERTY |
| L045 | InlineEnvVar | INHERITED_PROPERTY |
| L047 | NoLogPassword | INHERITED_PROPERTY |
| L049 | LoopVarPrefix | INHERITED_PROPERTY |
| M010 | Python2Interpreter | INHERITED_PROPERTY |
| M022 | TreeOnelineCallbackPlugins | INHERITED_PROPERTY |
| M026 | InvalidInventoryVariableNames | INHERITED_PROPERTY |
| M030 | BrokenConditionalExpressions | INHERITED_PROPERTY |

### Phase 2C — SCOPE_AWARE batch (PR #141)

| Rule | Name | Category |
|------|------|----------|
| L032 | ChangedDataDependence | SCOPE_AWARE |
| L034 | UnusedOverride | SCOPE_AWARE |
| L042 | Complexity | SCOPE_AWARE |
| L086 | PlayVarsUsage | SCOPE_AWARE |
| L093 | SetFactOverride | SCOPE_AWARE |
| L097 | NameUnique | SCOPE_AWARE |
| M005 | DataTagging | SCOPE_AWARE |
| R117 | ExternalRole | SCOPE_AWARE |

### Phase 2D — TASK_LOCAL batch 1 (PR #143)

| Rule | Name | Category |
|------|------|----------|
| L026 | NonFQCNUse | TASK_LOCAL |
| L030 | NonBuiltinUse | TASK_LOCAL |
| L036 | UnnecessaryIncludeVars | TASK_LOCAL |
| L044 | AvoidImplicit | TASK_LOCAL |
| L048 | NoSameOwner | TASK_LOCAL |
| L074 | NoDashesInRoleName | TASK_LOCAL |
| L081 | NumberedNames | TASK_LOCAL |
| L082 | TemplateJ2Ext | TASK_LOCAL |
| L084 | SubtaskPrefix | TASK_LOCAL |
| L092 | LoopVarInName | TASK_LOCAL |

### Phase 2E — TASK_LOCAL batch 2 (PR #TBD)

| Rule | Name | Category |
|------|------|----------|
| L037 | UnresolvedModule | TASK_LOCAL |
| L038 | UnresolvedRole | TASK_LOCAL |
| L075 | AnsibleManaged | TASK_LOCAL |
| L080 | InternalVarPrefix | TASK_LOCAL |
| L085 | RolePathInclude | TASK_LOCAL |
| L100 | VarNamingKeyword | TASK_LOCAL |
| L101 | VarNamingReserved | TASK_LOCAL |
| L102 | VarNamingReadOnly | TASK_LOCAL |
| M027 | LegacyKvMergedWithArgs | TASK_LOCAL |

### Phase 2F — Role-metadata batch (PR #145)

| Rule | Name | Category |
|------|------|----------|
| L027 | RoleWithoutMetadata | ROLE_METADATA |
| L052 | GalaxyVersionIncorrect | ROLE_METADATA |
| L053 | MetaIncorrect | ROLE_METADATA |
| L054 | MetaNoTags | ROLE_METADATA |
| L055 | MetaVideoLinks | ROLE_METADATA |
| L077 | RoleArgSpecs | ROLE_METADATA |
| L079 | RoleVarPrefix | ROLE_METADATA |

---

## Remaining Rules (53)

### Needs `args.raw` / structured args

These need raw argument data or `TaskCall.args[...].is_mutable`
beyond what `module_options` provides.

| Rule | Name | Severity | What it checks |
|------|------|----------|----------------|
| L035 | UnnecessarySetFact | VERY_LOW | `set_fact` with `random` in raw args (impure) |
| L046 | NoFreeForm | LOW | Free-form module invocation via `_raw_params` |
| R111 | ParameterizedImportRole | HIGH | Jinja-templated role name (needs `is_mutable`) |
| R112 | ParameterizedImportTaskfile | MEDIUM | Jinja-templated taskfile path (needs `is_mutable`) |
| R501 | DependencySuggestion | NONE | Suggests collection (needs `possible_candidates`) |

### Needs `yaml_lines` / raw YAML content

These rules inspect raw YAML text (whitespace, indentation, line
length, quoting, Jinja spacing, etc.). Requires adding `yaml_lines`
or equivalent to `ContentNode`.

| Rule | Name | Severity | What it checks |
|------|------|----------|----------------|
| L040 | NoTabs | VERY_LOW | Tab characters in YAML |
| L041 | KeyOrder | VERY_LOW | Task key ordering (name first, etc.) |
| L043 | DeprecatedBareVars | LOW | Bare Jinja in `with_*` / `when` |
| L051 | Jinja | VERY_LOW | Jinja spacing style (`{{ x }}` vs `{{x}}`) |
| L060 | LineLength | VERY_LOW | Line exceeds max length |
| L073 | Indentation | VERY_LOW | Indentation consistency |
| L076 | AnsibleFactsBracket | VERY_LOW | `ansible_facts['x']` vs `ansible_facts.x` |
| L078 | DotNotation | VERY_LOW | Dict bracket vs dot notation |
| L083 | HardcodedGroup | LOW | Hardcoded group references |
| L091 | BoolFilter | LOW | Bare `bool` filter style in `when` |
| L094 | DynamicTemplateDate | LOW | Dynamic date strings in templates |
| L098 | YamlKeyDuplicates | HIGH | Duplicate keys in YAML |
| L099 | YamlQuotedStrings | VERY_LOW | Quoted vs unquoted scalar style |
| M014 | TopLevelFactVariables | HIGH | `set_fact` at play level |
| M015 | PlayHostsMagicVariable | MEDIUM | Magic variables in `hosts:` |
| M019 | OmapPairsYamlTags | LOW | `!!omap` / `!!pairs` YAML tags |
| M020 | VaultEncryptedTag | LOW | `!vault` encrypted marker |

### Needs annotation infrastructure

These rules read/write task annotations from module annotators.
Requires exposing the annotation pipeline to `GraphRule`.

| Rule | Name | Severity | What it checks |
|------|------|----------|----------------|
| L031 | FilePermissionRule | MEDIUM | Insecure file permissions (disabled) |
| P001 | ModuleNameValidation | NONE | Module name validation + annotation emit |
| P002 | ModuleArgumentKeyValidation | NONE | Arg key validation + annotations |
| P003 | ModuleArgumentValueValidation | NONE | Arg value validation + annotations |
| P004 | VariableValidation | NONE | Variable validation + annotations |
| R101 | CommandExec | LOW | Mutable command execution |
| R103 | DownloadExec | HIGH | Download-then-execute pattern |
| R104 | InvalidDownloadSource | HIGH | Inbound URL not allowlisted |
| R105 | OutboundTransfer | MEDIUM | Outbound transfer with mutable dest |
| R106 | InboundTransfer | MEDIUM | Inbound transfer with mutable src |
| R107 | InsecurePkgInstall | HIGH | Package install with insecure flags |
| R109 | ConfigChange | LOW | Mutable config key changes |
| R113 | PkgInstall | MEDIUM | Parameterized package install target |
| R114 | FileChange | LOW | Mutable file change path/src |
| R115 | FileDeletion | LOW | File deletion risk |

### Needs variable tracking (`variable_use` / `variable_set`)

| Rule | Name | Severity | What it checks |
|------|------|----------|----------------|
| L039 | UndefinedVariable | LOW | Unknown variable types |
| L050 | VarNaming | VERY_LOW | Variable name convention (lowercase/underscore) |
| R402 | ListAllUsedVariables | NONE | Lists `variable_use` keys (aggregation rule) |
| R404 | ShowVariables | NONE | Dumps `variable_set` (disabled, debug rule) |

### Cross-task / aggregation

| Rule | Name | Severity | What it checks |
|------|------|----------|----------------|
| R401 | ListAllInboundSrc | VERY_LOW | Lists inbound `src` across scan (end aggregation) |

### Collection/plugin targets (no `COLLECTION` node type yet)

These rules target collection-level or plugin-level files.
Currently `match()` returns `False` because the graph has no
collection/plugin nodes. Deferred until `ContentGraph` adds
those node types.

| Rule | Name | Severity | What it checks |
|------|------|----------|----------------|
| L056 | Sanity | VERY_LOW | `defined_in` path matches ignore patterns |
| L087 | CollectionLicense | LOW | Collection missing LICENSE/COPYING |
| L088 | CollectionReadme | VERY_LOW | Collection README missing |
| L089 | PluginTypeHints | VERY_LOW | Plugin `.py` missing return type hints |
| L090 | PluginFileSize | VERY_LOW | Plugin `.py` entry file too large |
| L095 | SchemaValidation | HIGH | Playbook/galaxy schema keys (always-false match) |
| L096 | MetaRuntime | HIGH | `requires_ansible` in `meta/runtime.yml` |
| L103 | GalaxyChangelog | LOW | Collection missing CHANGELOG |
| L104 | GalaxyRuntime | MEDIUM | Collection missing `meta/runtime.yml` |
| L105 | GalaxyRepository | LOW | `galaxy.yml` missing `repository` |

### Disabled / stub

| Rule | Name | Severity | What it checks |
|------|------|----------|----------------|
| M029 | InventoryScriptMissingMeta | MEDIUM | Inventory script `_meta` (disabled, no implementation) |

---

## Recommended Porting Order

1. ~~**Phase 2E**: Simple task-local batch 2 (9 rules)~~ **DONE**
2. ~~**Phase 2F**: Role-metadata rules (7 rules)~~ **DONE**
3. **Phase 2G**: `args.raw` / structured args extension (5 rules: L035, L046, R111, R112, R501)
4. **Phase 2H**: `yaml_lines` extension + content rules (17 rules)
5. **Phase 2I**: Annotation infrastructure + risk/policy rules (15 rules)
6. **Phase 2J**: Variable tracking rules (4 rules)
7. **Phase 2K**: Collection/plugin targets + aggregation (11 rules)
8. **Skip**: M029 (disabled stub, no real implementation)

## ContentNode Extension Checklist

Fields still needed for full migration:

- [ ] `yaml_lines: list[str]` — raw YAML source lines for the node's span
- [ ] `raw_args: str | dict` — free-form / raw args (for L035, L046)
- [ ] `is_mutable: bool` — template/variable detection on args (for R111, R112)
- [ ] `possible_candidates: list[tuple[str,str]]` — resolution candidates (for R501)
- [ ] `annotations: dict[str, object]` — module annotator output
- [ ] `variable_use: list[VariableRef]` — variables referenced by this node
- [ ] `variable_set: list[VariableRef]` — variables defined by this node
- [ ] `COLLECTION` / `PLUGIN` node types in `NodeType` enum
- [ ] `role_files: dict[str, str]` — role file existence checks (argument_specs, etc.)
  - **L077 partial port**: currently checks only `role_metadata.get("argument_specs")`
    (embedded in meta/main.yml). The old rule also scans `spec.files` for a
    standalone `meta/argument_specs.yml` file. Full parity requires either a
    `role_files` field on `ContentNode` or having `GraphBuilder` resolve the
    file during role construction and merge into `role_metadata`.

---

## Outstanding Work Beyond Rule Porting

### Phase 3 — Progression + Provenance (ADR-044)

After Phase 2 (all rules ported), Phase 3 adds:

1. **NodeState progression**: Record content state at each pipeline phase
   (original → formatted → scanned → transformed → rescanned).
2. **PropertyOrigin consumed by rules**: Already-ported inherited-property
   rules (R108, L047, L045, etc.) use PropertyOrigin to attribute violations
   to the defining scope (play) rather than every inheriting child task.
3. **Gateway ScanSnapshot accumulation**: Gateway persists per-node timeline
   across scans for trend queries.
4. **Enabled capabilities**: Complexity metrics, AI escalation enrichment,
   topology visualization, best-practices pattern rules, dependency quality
   scorecards.

### Rule doc integration tests (short-term gap)

**Problem**: The old `rule_doc_integration_test.py` harness runs rule `.md`
examples through the old pipeline (`run_scan_playbook_yaml`). Scope-aware
and inherited-property graph rules (L097, L093, M005, R117, L034, L086)
added violation examples with `### Violation (context-dependent)` headings
to avoid parser matching, since the old pipeline can't test them.

**Resolution**: When Phase 2 completes and the old pipeline is removed, the
rule doc harness must be rewritten to use `ContentGraphScanner`. At that
point, all `(context-dependent)` headings revert to standard
`### Example: violation` and become testable.

### `tests/fixtures/graph-patterns/` coverage

The comprehensive fixture directory was created in Phase 1 and covers:
handlers/notify, block rescue/always, import_playbook chains, static
roles, import/include tasks/roles, vars_files, host_vars, nested blocks,
collection layout with `galaxy.yml`, Python plugins with `py_imports`.

**Currently used by**: `test_content_graph_shadow.py` (structural
equivalence), `test_python_analyzer.py`.

**Not yet used for**: graph-pattern-specific `GraphBuilder` edge-type
validation tests (e.g., assert every edge type in the taxonomy is produced).

### Old pipeline removal (end of Phase 2)

Once all 96 rules are ported and `ContentGraph` is primary:

- Remove `TreeLoader`, `AnsibleRunContext`, `RunTarget`, `ObjectList`,
  `Context.add()`, old `build_hierarchy_payload()`
- Remove `APME_USE_CONTENT_GRAPH` feature flag
- Rewrite `rule_doc_integration_test.py` to use `ContentGraphScanner`
- Single rule interface (`GraphRule`), zero adapter
