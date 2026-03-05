---
rule_id: L030
validator: native
description: Prefer ansible.builtin modules when available.
---

## Non-builtin use (L030)

Prefer ansible.builtin modules when available.

### Example: violation

```yaml
- name: Example play
  hosts: localhost
  connection: local
  tasks:
    - name: Copy
      copy:
        src: a
        dest: /tmp/b
```

### Example: pass

```yaml
- name: Example play
  hosts: localhost
  connection: local
  tasks:
    - name: Copy
      ansible.builtin.copy:
        src: a
        dest: /tmp/b
```
