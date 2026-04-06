---
rule_id: L096
validator: native
description: meta/runtime.yml requires_ansible must be a valid version specifier.
scope: collection
---

## Meta runtime (L096)

The `requires_ansible` key in `meta/runtime.yml` must be a valid PEP 440 version specifier.

Maps to ansible-lint `meta-runtime` rule.

Requires collection-level target type not yet in the engine. Currently disabled.

### Example: violation

```yaml
# meta/runtime.yml without requires_ansible
plugin_routing: {}
```

### Example: pass

```yaml
# meta/runtime.yml with valid version specifier
requires_ansible: ">=2.15.0"
```
