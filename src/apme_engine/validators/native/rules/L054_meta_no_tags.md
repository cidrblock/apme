---
rule_id: L054
validator: native
description: Role meta galaxy_info should include galaxy_tags.
---

## Meta no tags (L054)

Role meta galaxy_info should include galaxy_tags.

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
