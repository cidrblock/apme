---
rule_id: L026
validator: native
description: Tasks should use FQCN for modules.
---

## Non-FQCN use (L026)

Tasks should use FQCN for modules.

### Example: violation

```yaml
- name: Example play
  hosts: localhost
  connection: local
  tasks:
    - name: Install
      ansible_galaxy_install:
        name: foo
```

### Example: pass

```yaml
- name: Example play
  hosts: localhost
  connection: local
  tasks:
    - name: Install
      community.general.ansible_galaxy_install:
        name: foo
```
