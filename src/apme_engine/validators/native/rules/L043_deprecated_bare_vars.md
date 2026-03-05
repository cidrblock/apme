---
rule_id: L043
validator: native
description: Avoid {{ foo }}; prefer explicit form.
---

## Deprecated bare vars (L043)

Avoid {{ foo }}; prefer explicit form.

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
