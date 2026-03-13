"""Native rule L031: detect insecure file permissions."""

from dataclasses import dataclass
from typing import cast

from apme_engine.engine.models import (
    AnnotationCondition,
    AnsibleRunContext,
    Rule,
    RuleResult,
    RunTargetType,
    Severity,
)
from apme_engine.engine.models import (
    DefaultRiskType as RiskType,
)
from apme_engine.engine.models import (
    RuleTag as Tag,
)


@dataclass
class FilePermissionRule(Rule):
    """Rule for tasks with insecure file permissions.

    Attributes:
        rule_id: Rule identifier.
        description: Rule description.
        enabled: Whether the rule is enabled.
        name: Rule name.
        version: Rule version.
        severity: Severity level.
        tags: Rule tags.
    """

    rule_id: str = "L031"
    description: str = "File permission is not secure."
    enabled: bool = False
    name: str = "FilePermissionRule"
    version: str = "v0.0.1"
    severity: str = Severity.MEDIUM
    tags: tuple[str, ...] = (Tag.SYSTEM,)

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
        """Check for insecure file permissions and return result.

        Args:
            ctx: AnsibleRunContext to process.

        Returns:
            RuleResult with verdict, or None.
        """
        task = ctx.current
        if task is None:
            return None

        # define a condition for this rule here
        ac = AnnotationCondition().risk_type(RiskType.FILE_CHANGE).attr("is_insecure_permissions", True)
        verdict = task.has_annotation_by_condition(ac)

        return RuleResult(
            verdict=verdict,
            file=cast("tuple[str | int, ...] | None", task.file_info()),
            rule=self.get_metadata(),
        )
