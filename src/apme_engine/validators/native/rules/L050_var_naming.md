---
rule_id: L050
validator: native
description: Variable names: lowercase, underscores.
---

## Var naming (L050)

Variable names: lowercase, underscores.

### Example: violation

```yaml
- name: Example play
  hosts: localhost
  connection: local
  tasks:
    - name: Bad
      ansible.builtin.shell: whoami
```

### Example: pass

```yaml
- name: Example play
  hosts: localhost
  connection: local
  tasks:
    - name: Ok
      ansible.builtin.command: whoami
```
