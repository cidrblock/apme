---
rule_id: L040
validator: native
description: YAML should not contain tabs; use spaces.
---

## No tabs (L040)

YAML should not contain tabs; use spaces.

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
