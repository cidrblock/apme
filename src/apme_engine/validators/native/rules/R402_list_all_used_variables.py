"""Native rule R402: list all used variables."""

from dataclasses import dataclass
from typing import cast

from apme_engine.engine.models import (
    AnsibleRunContext,
    Rule,
    RuleResult,
    RunTargetType,
    Severity,
    TaskCall,
    YAMLDict,
)
from apme_engine.engine.models import RuleTag as Tag


@dataclass
class ListAllUsedVariablesRule(Rule):
    """Rule to list all used variables.

    Attributes:
        rule_id: Rule identifier.
        description: Rule description.
        enabled: Whether the rule is enabled.
        name: Rule name.
        version: Rule version.
        severity: Severity level.
        tags: Rule tags.
    """

    rule_id: str = "R402"
    description: str = "Listing all used variables"
    enabled: bool = True
    name: str = "ListAllUsedVariables"
    version: str = "v0.0.1"
    severity: str = Severity.NONE
    tags: tuple[str, ...] = (Tag.VARIABLE,)

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
        """List used variables and return result.

        Args:
            ctx: AnsibleRunContext to process.

        Returns:
            RuleResult with metadata/variables detail, or None.
        """
        task = ctx.current
        if task is None:
            return None

        verdict = False
        detail: dict[str, object] = {}
        if ctx.is_end(task) and isinstance(task, TaskCall):
            verdict = True
            detail["metadata"] = ctx.info
            detail["variables"] = list(task.variable_use.keys())

        return RuleResult(
            verdict=verdict,
            detail=cast("YAMLDict | None", detail),
            file=cast("tuple[str | int, ...] | None", task.file_info()),
            rule=self.get_metadata(),
        )
