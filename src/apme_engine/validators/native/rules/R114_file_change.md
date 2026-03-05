---
rule_id: R114
validator: native
description: File change (annotation-based).
---

## File change (R114)

File change (annotation-based).

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
