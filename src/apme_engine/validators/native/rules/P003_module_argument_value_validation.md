---
rule_id: P003
validator: native
description: Validate module argument values (Ansible required).
---

## Module argument value (P003)

Validate module argument values (Ansible required).

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
