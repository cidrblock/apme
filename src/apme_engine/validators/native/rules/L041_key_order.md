---
rule_id: L041
validator: native
description: Task keys should follow canonical order (e.g. name before module).
---

## Key order (L041)

Task keys should follow canonical order (e.g. name before module).

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
