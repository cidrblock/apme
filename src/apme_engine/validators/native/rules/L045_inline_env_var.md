---
rule_id: L045
validator: native
description: Avoid inline environment in tasks.
---

## Inline env var (L045)

Avoid inline environment in tasks.

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
