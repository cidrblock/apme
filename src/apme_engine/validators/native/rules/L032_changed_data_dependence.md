---
rule_id: L032
validator: native
description: Variable redefinition may cause confusion.
---

## Changed data dependence (L032)

Variable redefinition may cause confusion.

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
