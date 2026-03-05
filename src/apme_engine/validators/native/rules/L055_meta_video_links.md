---
rule_id: L055
validator: native
description: Role meta video_links should be valid URLs.
---

## Meta video links (L055)

Role meta video_links should be valid URLs.

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
