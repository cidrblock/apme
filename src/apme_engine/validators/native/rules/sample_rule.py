"""Sample rule that echoes task block content for testing."""

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


@dataclass
class SampleRule(Rule):
    """Sample rule that echoes task block content.

    Attributes:
        rule_id: Rule identifier.
        description: Rule description.
        enabled: Whether the rule is enabled.
        name: Rule name.
        version: Rule version.
        severity: Severity level.
        tags: Rule tags.
    """

    rule_id: str = "Sample101"
    description: str = "echo task block"
    enabled: bool = False
    name: str = "EchoTaskContent"
    version: str = "v0.0.1"
    severity: str = Severity.NONE
    tags: tuple[str, ...] = ("sample",)

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
        """Process task and return rule result with task block.

        Args:
            ctx: Current Ansible run context.

        Returns:
            RuleResult with task block content, None if task unavailable.

        """
        if ctx.current is None:
            return None
        task = ctx.current
        if not isinstance(task, TaskCall) or task.content is None:
            return None

        verdict = True
        detail: YAMLDict = {}
        task_block = task.content.yaml()
        detail["task_block"] = task_block

        return RuleResult(
            verdict=verdict,
            detail=detail,
            file=cast("tuple[str | int, ...] | None", task.file_info()),
            rule=self.get_metadata(),
        )
