"""Native rule L028: detect tasks without a name attribute."""

from dataclasses import dataclass
from typing import cast

from apme_engine.engine.models import (
    AnsibleRunContext,
    Rule,
    RuleResult,
    RunTargetType,
    Severity,
)
from apme_engine.engine.models import (
    RuleTag as Tag,
)


@dataclass
class TaskWithoutNameRule(Rule):
    """Rule for tasks missing a name attribute.

    Attributes:
        rule_id: Unique rule identifier.
        description: Human-readable rule description.
        enabled: Whether the rule is active.
        name: Short name of the rule.
        version: Rule version string.
        severity: Severity level of violations.
        tags: Categorization tags.

    """

    rule_id: str = "L028"
    description: str = "A task without name is found"
    enabled: bool = True
    name: str = "TaskWithoutName"
    version: str = "v0.0.1"
    severity: str = Severity.LOW
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
        """Check for tasks without name and return verdict.

        Args:
            ctx: Current Ansible run context.

        Returns:
            RuleResult with verdict if task lacks name, None otherwise.

        """
        task = ctx.current
        if task is None:
            return None

        verdict = not getattr(task.spec, "name", None)

        return RuleResult(
            verdict=verdict,
            file=cast("tuple[str | int, ...] | None", task.file_info()),
            rule=self.get_metadata(),
        )
