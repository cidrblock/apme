"""Native rule R105: detect outbound network transfer to parameterized URL."""

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
from apme_engine.engine.models import (
    DefaultRiskType as RiskType,
)
from apme_engine.engine.models import (
    RuleTag as Tag,
)


@dataclass
class InboundTransferRule(Rule):
    """Rule for outbound network transfer to parameterized URL.

    Attributes:
        rule_id: Rule identifier.
        description: Rule description.
        enabled: Whether the rule is enabled.
        name: Rule name.
        version: Rule version.
        severity: Severity level.
        tags: Rule tags.
    """

    rule_id: str = "R105"
    description: str = "An outbound network transfer to a parameterized URL is found"
    enabled: bool = True
    name: str = "OutboundTransfer"
    version: str = "v0.0.1"
    severity: str = Severity.MEDIUM
    tags: tuple[str, ...] = (Tag.NETWORK,)

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
        """Check for outbound transfer to parameterized URL and return result.

        Args:
            ctx: AnsibleRunContext to process.

        Returns:
            RuleResult with from/to detail, or None.
        """
        task = ctx.current
        if task is None:
            return None

        ac = AnnotationCondition().risk_type(RiskType.OUTBOUND).attr("is_mutable_dest", True)
        verdict = task.has_annotation_by_condition(ac)

        detail = {}
        if verdict:
            anno = task.get_annotation_by_condition(ac)
            if anno:
                src = getattr(anno, "src", None)
                dest = getattr(anno, "dest", None)
                if src is not None:
                    detail["from"] = src.value
                if dest is not None:
                    detail["to"] = dest.value

        return RuleResult(
            verdict=verdict,
            detail=cast("YAMLDict | None", detail),
            file=cast("tuple[str | int, ...] | None", task.file_info()),
            rule=self.get_metadata(),
        )
