"""Native rule L041: detect task keys in non-canonical order."""

import re
from dataclasses import dataclass
from typing import cast

from apme_engine.engine.models import (
    AnsibleRunContext,
    Rule,
    RuleResult,
    RunTargetType,
    Severity,
    YAMLDict,
)
from apme_engine.engine.models import (
    RuleTag as Tag,
)

# Canonical order: name first, then block keys, then module/action, then task options (tags, when, etc.), then args.
# Simplified: we check that "name" appears before the module key in the YAML line order.
TASK_TOP_KEYS_ORDER = ["name", "block", "include", "import", "set_fact", "debug", "vars", "loop", "when", "tags"]

# Keys that should typically come before the action (module) key in a task
PREFERRED_BEFORE_ACTION = {"name"}


def _top_level_keys_from_yaml(yaml_lines: str) -> list[str]:
    """Return list of top-level task keys in source order (as they appear in yaml_lines).

    Args:
        yaml_lines: Raw YAML lines of the task.

    Returns:
        List of top-level keys in source order.
    """
    keys = []
    for line in yaml_lines.splitlines():
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            stripped = stripped[2:].lstrip()
        match = re.match(r"^(\w+)\s*:", stripped)
        if match:
            keys.append(match.group(1))
    return keys


def _first_action_key(keys: list[str], module_name: str) -> str | None:
    """First key that looks like an action (module name or 'local_action', 'action').

    Args:
        keys: List of task keys.
        module_name: Resolved module name.

    Returns:
        First action-like key, or None.
    """
    action_like = {"local_action", "action"}
    for k in keys:
        if k in action_like or k == module_name or (module_name and module_name.split(".")[-1] == k):
            return k
    return None


@dataclass
class KeyOrderRule(Rule):
    """Rule for task keys following canonical order (e.g. name before module).

    Attributes:
        rule_id: Rule identifier.
        description: Rule description.
        enabled: Whether the rule is enabled.
        name: Rule name.
        version: Rule version.
        severity: Severity level.
        tags: Rule tags.
    """

    rule_id: str = "L041"
    description: str = "Task keys should follow canonical order (e.g. name before module)"
    enabled: bool = True
    name: str = "KeyOrder"
    version: str = "v0.0.1"
    severity: str = Severity.VERY_LOW
    tags: tuple[str, ...] = (Tag.QUALITY,)

    def match(self, ctx: AnsibleRunContext) -> bool:
        """Check if context has a task target.

        Args:
            ctx: AnsibleRunContext to evaluate.

        Returns:
            True if current target is a task.
        """
        if ctx.current is None:
            return False
        return bool(ctx.current.type == RunTargetType.Task)

    def process(self, ctx: AnsibleRunContext) -> RuleResult | None:
        """Check task key order and return result.

        Args:
            ctx: AnsibleRunContext to process.

        Returns:
            RuleResult with keys_order detail, or None.
        """
        task = ctx.current
        if task is None:
            return None
        spec = task.spec
        yaml_lines = getattr(spec, "yaml_lines", "") or ""
        if not yaml_lines.strip():
            return RuleResult(
                verdict=False,
                file=cast("tuple[str | int, ...] | None", task.file_info()),
                rule=self.get_metadata(),
            )

        keys = _top_level_keys_from_yaml(yaml_lines)
        if not keys:
            return RuleResult(
                verdict=False,
                file=cast("tuple[str | int, ...] | None", task.file_info()),
                rule=self.get_metadata(),
            )

        module_name = getattr(spec, "module", "") or ""
        first_action = _first_action_key(keys, module_name)
        if not first_action:
            return RuleResult(
                verdict=False,
                file=cast("tuple[str | int, ...] | None", task.file_info()),
                rule=self.get_metadata(),
            )

        # Violation: "name" exists but appears after the action key
        action_index = keys.index(first_action) if first_action in keys else -1
        name_index = keys.index("name") if "name" in keys else -1
        verdict = name_index > action_index if (name_index >= 0 and action_index >= 0) else False
        detail: YAMLDict = {}
        if verdict:
            detail["keys_order"] = keys  # type: ignore[assignment]
            detail["message"] = "name should appear before the action/module key"
        return RuleResult(
            verdict=verdict,
            detail=detail,
            file=cast("tuple[str | int, ...] | None", task.file_info()),
            rule=self.get_metadata(),
        )
