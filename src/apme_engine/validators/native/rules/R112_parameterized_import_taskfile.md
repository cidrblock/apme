---
rule_id: R112
validator: native
description: Parameterized taskfile import (annotation-based).
---

## Parameterized import taskfile (R112)

Parameterized taskfile import (annotation-based).

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
