---
rule_id: L027
validator: native
description: Roles should have meta/main.yml with metadata.
---

## Role without metadata (L027)

Roles should have meta/main.yml with metadata.

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
