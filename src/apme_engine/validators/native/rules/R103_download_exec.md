---
rule_id: R103
validator: native
description: Task downloads and executes (annotation-based).
---

## Download exec (R103)

Task downloads and executes (annotation-based).

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
