
# Architecture

  ```
  CLI ──► Primary Orchestrator
               │
               ├──► Native Validator   (Python rules)
               ├──► OPA Validator      (Rego policies)
               ├──► Ansible Validator  (ansible-core introspection)
               ├──► Gitleaks Scanner   (secret detection)
               └──► Cache Maintainer   (Galaxy + GitHub)
  ```

  All gRPC. All async. All in a Podman pod.

