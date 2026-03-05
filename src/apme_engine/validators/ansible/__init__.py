"""Ansible validator: runs checks that require an ansible-core runtime (venv).

Rules are colocated under rules/ and follow the same pattern as native and OPA validators.
Each rule module exports a run() function that returns a list of violation dicts.
"""

import sys
from pathlib import Path

from apme_engine.validators.base import ScanContext

from .rules import L057_syntax, L058_argspec_doc, L059_argspec_mock, M001_M004_introspect


def _extract_task_nodes(hierarchy_payload: dict) -> list[dict]:
    """Extract all taskcall nodes from the hierarchy payload."""
    nodes = []
    for tree in hierarchy_payload.get("hierarchy", []):
        for node in tree.get("nodes", []):
            if node.get("type") == "taskcall":
                nodes.append(node)
    return nodes


class AnsibleValidator:
    """Validator that runs ansible-core checks via pre-built venvs.

    Rules:
      L057 - Syntax check (ansible-playbook --syntax-check)
      L058 - Argspec validation (docstring-based)
      L059 - Argspec validation (mock/patch-based)
      M001 - FQCN resolution
      M002 - Deprecated module
      M003 - Module redirect
      M004 - Removed/tombstoned module
    """

    def __init__(
        self,
        venv_root: Path,
        env_extra: dict | None = None,
    ):
        self._venv_root = venv_root
        self._env_extra = env_extra

    def run(self, context: ScanContext) -> list[dict]:
        """Run all ansible checks and return violation dicts."""
        violations: list[dict] = []
        root_dir = Path(context.root_dir) if context.root_dir else None

        # L057: Syntax check (needs files on disk)
        if root_dir and root_dir.is_dir():
            l057 = L057_syntax.run(
                venv_root=self._venv_root,
                root_dir=root_dir,
                env_extra=self._env_extra,
            )
            violations.extend(l057)
            sys.stderr.write(f"  L057 (syntax): {len(l057)} issue(s)\n")

        # Hierarchy-payload-based checks
        task_nodes = _extract_task_nodes(context.hierarchy_payload) if context.hierarchy_payload else []
        if not task_nodes:
            sys.stderr.write(f"Ansible validator: total {len(violations)} violation(s)\n")
            sys.stderr.flush()
            return violations

        sys.stderr.write(f"Ansible validator: checking {len(task_nodes)} task(s)\n")

        # M001-M004: Plugin introspection
        m_violations = M001_M004_introspect.run(
            task_nodes=task_nodes,
            venv_root=self._venv_root,
            env_extra=self._env_extra,
        )
        violations.extend(m_violations)
        sys.stderr.write(f"  M001-M004 (introspection): {len(m_violations)} issue(s)\n")

        # L058: Argspec (docstring)
        l058 = L058_argspec_doc.run(
            task_nodes=task_nodes,
            venv_root=self._venv_root,
            env_extra=self._env_extra,
        )
        violations.extend(l058)
        sys.stderr.write(f"  L058 (argspec-doc): {len(l058)} issue(s)\n")

        # L059: Argspec (mock/patch)
        l059 = L059_argspec_mock.run(
            task_nodes=task_nodes,
            venv_root=self._venv_root,
            env_extra=self._env_extra,
        )
        violations.extend(l059)
        sys.stderr.write(f"  L059 (argspec-mock): {len(l059)} issue(s)\n")

        sys.stderr.write(f"Ansible validator: total {len(violations)} violation(s)\n")
        sys.stderr.flush()
        return violations
