---
rule_id: L049
validator: native
description: Loop variable should use prefix (e.g. item_).
---

## Loop var prefix (L049)

Loop variable should use prefix (e.g. item_).

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
