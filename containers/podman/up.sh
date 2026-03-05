#!/usr/bin/env bash
# Start the APME pod (Primary, Ansible, OPA, Cache maintainer). Run from repo root.
# CLI is not part of the pod; use run-cli.sh to run a scan with CWD mounted.
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
podman play kube containers/podman/pod.yaml
echo "Pod apme-pod started. Run a scan: containers/podman/run-cli.sh"
