#!/usr/bin/env bash
# Pre-build ansible-core venvs at image build time.
# Each venv lives at /opt/ansible-venvs/<major.minor> (e.g. /opt/ansible-venvs/2.20).
set -e

VENVS_ROOT="${1:-/opt/ansible-venvs}"
VERSIONS="2.18 2.19 2.20"

for ver in $VERSIONS; do
    echo "==> Building venv for ansible-core ~=${ver}.0 at ${VENVS_ROOT}/${ver}"
    python3 -m venv "${VENVS_ROOT}/${ver}"
    "${VENVS_ROOT}/${ver}/bin/pip" install --no-cache-dir "ansible-core~=${ver}.0"
    echo "    $(${VENVS_ROOT}/${ver}/bin/ansible-playbook --version | head -1)"
done

echo "Pre-built venvs: $(ls ${VENVS_ROOT})"
