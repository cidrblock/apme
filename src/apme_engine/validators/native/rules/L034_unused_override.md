---
rule_id: L034
validator: native
description: Lower-precedence override may be unused.
scope: inventory
---

## Unused override (L034)

A variable redefined at a lower-precedence scope will be shadowed by the higher-precedence definition, making the override effectively dead code. For example, setting a variable in `group_vars` that is already defined in `role_vars` (higher precedence) has no effect.

This rule requires the engine to resolve multi-scope variable precedence, which cannot be fully tested in the single-playbook harness.

### Violation (requires multi-scope precedence context)

```yaml
# group_vars/all.yml defines: app_port: 8080
# The role vars/main.yml (higher precedence) already defines: app_port: 9090
# This play-level var at lower precedence is effectively dead:
- name: Deploy application
  hosts: appservers
  vars:
    app_port: 3000
  tasks:
    - name: Show port
      ansible.builtin.debug:
        msg: "Port is {{ app_port }}"
```

### Example: pass

```yaml
- name: Deploy application
  hosts: appservers
  tasks:
    - name: Run health check
      ansible.builtin.command: whoami
```
