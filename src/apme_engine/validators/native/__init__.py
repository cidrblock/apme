"""ARI native validator: runs in-tree rules on context.scandata. Built-in rules in this package."""

import os
from typing import Any, Tuple

from apme_engine.engine.risk_detector import detect
from apme_engine.validators.base import ScanContext, Validator


# Rules that require Ansible runtime (e.g. module schema / argparse validation). Excluded by default.
RULES_REQUIRING_ANSIBLE: Tuple[str, ...] = ("P001", "P002", "P003", "P004")


def _default_rules_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "rules")


def _rule_results_to_violations(data_report: dict) -> list[dict[str, Any]]:
    """Convert ARI detect() report to shared violation shape."""
    violations = []
    ari_result = data_report.get("ari_result")
    if not ari_result or not hasattr(ari_result, "targets"):
        return violations
    for target in ari_result.targets:
        for node_result in getattr(target, "nodes", []) or []:
            for r in getattr(node_result, "rules", []) or []:
                if not getattr(r, "verdict", False):
                    continue
                rule_meta = getattr(r, "rule", None)
                rule_id = getattr(rule_meta, "rule_id", "") if rule_meta else ""
                severity = getattr(rule_meta, "severity", "") or "medium"
                description = getattr(rule_meta, "description", "") or ""
                detail = getattr(r, "detail", None)
                if isinstance(detail, dict) and detail.get("message"):
                    message = detail["message"]
                else:
                    message = description
                file_info = getattr(r, "file", None)
                if isinstance(file_info, (list, tuple)) and len(file_info) >= 1:
                    file_path = str(file_info[0]) if file_info[0] else ""
                    line = file_info[1] if len(file_info) > 1 else None
                else:
                    file_path = ""
                    line = None
                node = getattr(node_result, "node", None)
                path = ""
                if node and hasattr(node, "spec") and hasattr(node.spec, "key"):
                    path = getattr(node.spec, "key", "") or ""
                violations.append({
                    "rule_id": f"native:{rule_id}" if rule_id else "native:unknown",
                    "level": severity,
                    "message": message,
                    "file": file_path,
                    "line": line,
                    "path": path,
                })
    return violations


class NativeValidator:
    """Validator that runs in-tree native (Python) rules on context.scandata (no second parse)."""

    def __init__(self, rules_dir: str = "", exclude_rule_ids: Tuple[str, ...] = None):
        """
        Args:
            rules_dir: Directory containing rule modules. If empty, uses built-in rules in this package.
            exclude_rule_ids: Rule IDs to exclude (e.g. rules requiring Ansible runtime).
                Default: RULES_REQUIRING_ANSIBLE (P001–P004).
        """
        self._rules_dir = rules_dir or _default_rules_dir()
        self._exclude_rule_ids = list(exclude_rule_ids) if exclude_rule_ids is not None else list(RULES_REQUIRING_ANSIBLE)

    def run(self, context: ScanContext) -> list[dict]:
        """Run native rules on context.scandata; return list of violation dicts."""
        scandata = context.scandata
        if not scandata:
            return []
        contexts = getattr(scandata, "contexts", None) or []
        if not contexts:
            return []
        if not os.path.isdir(self._rules_dir):
            return []
        data_report, _ = detect(
            contexts,
            rules_dir=self._rules_dir,
            rules=[],
            rules_cache=[],
            save_only_rule_result=False,
            exclude_rule_ids=self._exclude_rule_ids,
        )
        return _rule_results_to_violations(data_report)
