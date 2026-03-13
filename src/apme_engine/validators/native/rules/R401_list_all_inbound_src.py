"""Native rule R401: list all inbound sources."""

from dataclasses import dataclass
from typing import cast

from apme_engine.engine.models import (
    AnnotationCondition,
    AnsibleRunContext,
    DefaultRiskType,
    Rule,
    RuleResult,
    RunTargetType,
    Severity,
    TaskCall,
    YAMLDict,
)
from apme_engine.engine.models import RuleTag as Tag


@dataclass
class ListAllInboundSrcRule(Rule):
    """Rule to list all inbound sources.

    Attributes:
        rule_id: Rule identifier.
        description: Rule description.
        enabled: Whether the rule is enabled.
        name: Rule name.
        version: Rule version.
        severity: Severity level.
        tags: Rule tags.
    """

    rule_id: str = "R401"
    description: str = "List all inbound sources"
    enabled: bool = True
    name: str = "ListAllInboundSrcRule"
    version: str = "v0.0.1"
    severity: str = Severity.VERY_LOW
    tags: tuple[str, ...] = (Tag.DEBUG,)

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
        """List inbound sources and return result.

        Args:
            ctx: AnsibleRunContext to process.

        Returns:
            RuleResult with inbound_src detail, or None.
        """
        task = ctx.current
        if task is None:
            return None

        ac = AnnotationCondition().risk_type(DefaultRiskType.INBOUND)
        verdict = False
        detail: dict[str, object] = {}
        src_list: list[str] = []
        if ctx.is_end(task):
            tasks = ctx.search(ac)
            for t in tasks:
                if isinstance(t, TaskCall):
                    anno = t.get_annotation_by_condition(ac)
                    if anno is not None and hasattr(anno, "src") and anno.src is not None:
                        src_list.append(anno.src.value)
            if len(src_list) > 0:
                verdict = True
                detail["inbound_src"] = src_list

        return RuleResult(
            verdict=verdict,
            detail=cast("YAMLDict | None", detail),
            file=cast("tuple[str | int, ...] | None", task.file_info()),
            rule=self.get_metadata(),
        )
