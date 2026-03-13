"""Native rule R104: detect network transfer from unauthorized source."""

import re
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

allow_url_list = ["https://*"]

deny_url_list = ["http://*"]


@dataclass
class InvalidDownloadSourceRule(Rule):
    """Rule for network transfer from unauthorized source.

    Attributes:
        rule_id: Rule identifier.
        description: Rule description.
        enabled: Whether the rule is enabled.
        name: Rule name.
        version: Rule version.
        severity: Severity level.
        tags: Rule tags.
    """

    rule_id: str = "R104"
    description: str = "A network transfer from unauthorized source is found."
    enabled: bool = True
    name: str = "InvalidDownloadSource"
    version: str = "v0.0.1"
    severity: str = Severity.HIGH
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
        """Check for unauthorized download source and return result.

        Args:
            ctx: AnsibleRunContext to process.

        Returns:
            RuleResult with invalid_src detail, or None.
        """
        task = ctx.current
        if task is None:
            return None

        ac = AnnotationCondition().risk_type(RiskType.INBOUND)

        verdict = False
        detail = {}

        anno = task.get_annotation_by_condition(ac)
        src = getattr(anno, "src", None) if anno else None
        if anno and src is not None and not self.is_allowed_url(src.value, allow_url_list, deny_url_list):
            verdict = True
            detail["invalid_src"] = src.value

        return RuleResult(
            verdict=verdict,
            detail=cast("YAMLDict | None", detail),
            file=cast("tuple[str | int, ...] | None", task.file_info()),
            rule=self.get_metadata(),
        )

    def is_allowed_url(self, src: str, allow_list: list[str], deny_list: list[str]) -> bool:
        """Check if URL is allowed by allow/deny lists.

        Args:
            src: URL to check.
            allow_list: List of allowed URL patterns.
            deny_list: List of denied URL patterns.

        Returns:
            True if URL is allowed.
        """
        matched: bool = True
        if len(allow_list) > 0:
            matched = False
            for a in allow_list:
                res = re.match(a, src)
                if res:
                    matched = True
        elif len(deny_list) > 0:
            for d in deny_list:
                res = re.match(d, src)
                if res:
                    matched = False
        return matched
