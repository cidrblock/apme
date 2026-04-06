---
rule_id: L080
validator: native
description: Internal role variables should be prefixed with __ (double underscore).
scope: task
---

## Internal variable prefix (L080)

Internal role variables (from `set_fact` or `register`) should be prefixed with `__` to signal they are private.

Only fires inside `roles/` directories. Checks `set_fact` keys for missing `__` prefix.

### Example: violation

```yaml
- name: Set unprefixed variable in role
  ansible.builtin.set_fact:
    temp_value: "something"
```

### Example: pass

```yaml
- name: Set prefixed variable in role
  ansible.builtin.set_fact:
    __temp_value: "something"
```
