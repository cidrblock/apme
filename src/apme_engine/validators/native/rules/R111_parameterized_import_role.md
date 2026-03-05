---
rule_id: R111
validator: native
description: Parameterized role import (annotation-based).
---

## Parameterized import role (R111)

Parameterized role import (annotation-based).

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
