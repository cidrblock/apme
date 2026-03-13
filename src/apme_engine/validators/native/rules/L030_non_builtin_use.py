"""Native rule L030: detect tasks using non-builtin modules."""

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
class NonBuiltinUseRule(Rule):
    """Rule for tasks using non-builtin modules.

    Attributes:
        rule_id: Rule identifier.
        description: Rule description.
        enabled: Whether the rule is enabled.
        name: Rule name.
        version: Rule version.
        severity: Severity level.
        tags: Rule tags.
    """

    rule_id: str = "L030"
    description: str = "Non-builtin module is used"
    enabled: bool = True
    name: str = "NonBuiltinUse"
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
        """Check for non-builtin module usage and return FQCN detail if found.

        Args:
            ctx: Current Ansible run context.

        Returns:
            RuleResult with verdict and FQCN detail if non-builtin module found, None otherwise.

        """
        task = ctx.current
        if task is None:
            return None

        action_type = getattr(task, "action_type", "")
        resolved_action = getattr(task, "resolved_action", "")
        resolved_name = getattr(task, "resolved_name", "")
        verdict = bool(
            action_type == ActionType.MODULE_TYPE
            and resolved_action
            and not resolved_action.startswith("ansible.builtin.")
        )

        detail = {
            "fqcn": resolved_name,
        }

        return RuleResult(
            verdict=verdict,
            detail=cast("YAMLDict | None", detail),
            file=cast("tuple[str | int, ...] | None", task.file_info()),
            rule=self.get_metadata(),
        )
