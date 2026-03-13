"""Native rule R101: detect parameterized command execution."""

from dataclasses import dataclass
from typing import cast

from apme_engine.engine.models import (
    AnnotationCondition,
    AnsibleRunContext,
    Rule,
    RuleResult,
    RunTargetType,
    Severity,
    YAMLDict,
)
from apme_engine.engine.models import DefaultRiskType as RiskType
from apme_engine.engine.models import (
    RuleTag as Tag,
)


@dataclass
class CommandExecRule(Rule):
    """Rule for parameterized command execution.

    Attributes:
        rule_id: Rule identifier.
        description: Rule description.
        enabled: Whether the rule is enabled.
        name: Rule name.
        version: Rule version.
        severity: Severity level.
        tags: Rule tags.
    """

    rule_id: str = "R101"
    description: str = "A parameterized command execution found"
    enabled: bool = True
    name: str = "CommandExec"
    version: str = "v0.0.1"
    severity: str = Severity.LOW
    tags: tuple[str, ...] = (Tag.COMMAND,)

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
        """Check for parameterized command execution and return result.

        Args:
            ctx: AnsibleRunContext to process.

        Returns:
            RuleResult with cmd detail, or None.
        """
        task = ctx.current
        if task is None:
            return None

        ac = AnnotationCondition().risk_type(RiskType.CMD_EXEC).attr("is_mutable_cmd", True)
        verdict = task.has_annotation_by_condition(ac)

        detail = {}
        if verdict:
            anno = task.get_annotation_by_condition(ac)
            if anno:
                cmd = getattr(anno, "command", None)
                if cmd is not None:
                    detail["cmd"] = cmd.raw

        return RuleResult(
            verdict=verdict,
            detail=cast(YAMLDict | None, detail),
            file=cast("tuple[str | int, ...] | None", task.file_info()),
            rule=self.get_metadata(),
        )
