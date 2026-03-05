---
rule_id: L031
validator: native
description: File permission may be insecure (annotation-based).
---

## Insecure file permission (L031)

File permission may be insecure (annotation-based).

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
