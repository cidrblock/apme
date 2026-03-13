"""Native rule L026: detect tasks using short module names instead of FQCN."""

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
    ExecutableType as ActionType,
)
from apme_engine.engine.models import (
    RuleTag as Tag,
)


@dataclass
class NonFQCNUseRule(Rule):
    """Rule for tasks using short module names instead of FQCN.

    Attributes:
        rule_id: Rule identifier.
        description: Rule description.
        enabled: Whether the rule is enabled.
        name: Rule name.
        version: Rule version.
        severity: Severity level.
        tags: Rule tags.
    """

    rule_id: str = "L026"
    description: str = "A task with a short module name is found"
    enabled: bool = True
    name: str = "NonFQCNUse"
    version: str = "v0.0.1"
    severity: str = Severity.VERY_LOW
    tags: tuple[str, ...] = (Tag.DEPENDENCY,)

    def match(self, ctx: AnsibleRunContext) -> bool:
        """Return True if the current target is a task.

        Args:
            ctx: Current Ansible run context.

        Returns:
            True if the current target is a task.

        """
        if ctx.current is None:
            return False
        return bool(ctx.current.type == RunTargetType.Task)

    def process(self, ctx: AnsibleRunContext) -> RuleResult | None:
        """Check for short module names and return FQCN detail if found.

        Args:
            ctx: Current Ansible run context.

        Returns:
            RuleResult with verdict and FQCN detail if short module found, None otherwise.

        """
        task = ctx.current
        if task is None:
            return None

        action_type = getattr(task, "action_type", "")
        spec_action = getattr(task.spec, "action", None)
        resolved_action = getattr(task, "resolved_action", "")
        resolved_name = getattr(task, "resolved_name", "")
        verdict = bool(
            action_type == ActionType.MODULE_TYPE
            and spec_action
            and resolved_action
            and spec_action != resolved_action
            and not resolved_action.startswith("ansible.builtin.")
        )
        detail = {
            "module": spec_action or "",
            "fqcn": resolved_name,
        }

        return RuleResult(
            verdict=verdict,
            detail=cast("YAMLDict | None", detail),
            file=cast("tuple[str | int, ...] | None", task.file_info()),
            rule=self.get_metadata(),
        )
