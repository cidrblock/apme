---
rule_id: R101
validator: native
description: Task executes parameterized command (annotation-based)
---

## Command exec (R101)

The rule checks whether a task executes a parameterized command that could be overwritten (e.g. variable in command args). It relies on annotations from the engine.

### Example: violation

```yaml
- name: Example play
  hosts: localhost
  connection: local
  tasks:
    - name: Run command
      ansible.builtin.command: bash {{ install_script }}
```

### Example: pass

```yaml
- name: Example play
  hosts: localhost
  connection: local
  tasks:
    - name: Run command
      ansible.builtin.command: bash /tmp/install_script.sh
```
