---
rule_id: L077
validator: native
description: Roles should have meta/argument_specs.yml for fail-fast parameter validation.
scope: role
---

## Role argument specs (L077)

Roles should have `meta/argument_specs.yml` (Ansible 2.11+) for fail-fast parameter validation.

### Example: violation

```yaml
# roles/myrole/meta/main.yml
galaxy_info:
  author: acme
dependencies: []
```

### Example: pass

```yaml
# roles/myrole/meta/main.yml
galaxy_info:
  author: acme
dependencies: []
argument_specs:
  main:
    short_description: Configure the service.
    options:
      service_port:
        type: int
        description: Port to listen on.
        default: 8080
```
