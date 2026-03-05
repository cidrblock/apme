---
rule_id: L052
validator: native
description: Galaxy version in meta should be semantic.
---

## Galaxy version (L052)

Galaxy version in meta should be semantic.

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
