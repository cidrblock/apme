"""Native rule R113: detect parameterized package installation."""

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
class PkgInstallRuleResult(RuleResult):
    """Result subclass for PkgInstallRule."""


@dataclass
class PkgInstallRule(Rule):
    """Rule for parameterized package installation.

    Attributes:
        rule_id: Rule identifier.
        description: Rule description.
        enabled: Whether the rule is enabled.
        name: Rule name.
        version: Rule version.
        severity: Severity level.
        tags: Rule tags.
        result_type: Type of RuleResult to produce.
    """

    rule_id: str = "R113"
    description: str = "A parameterized pkg installation is found"
    enabled: bool = True
    name: str = "PkgInstall"
    version: str = "v0.0.1"
    severity: str = Severity.MEDIUM
    tags: tuple[str, ...] = (Tag.PACKAGE,)
    result_type: type = PkgInstallRuleResult

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
        """Check for parameterized pkg install and return result.

        Args:
            ctx: Current Ansible run context.

        Returns:
            RuleResult with verdict and pkg detail if parameterized install found, None otherwise.

        """
        task = ctx.current
        if task is None:
            return None

        ac = AnnotationCondition().risk_type(RiskType.PACKAGE_INSTALL).attr("is_mutable_pkg", True)
        verdict = task.has_annotation_by_condition(ac)

        detail = {}
        if verdict:
            anno = task.get_annotation_by_condition(ac)
            if anno:
                detail["pkg"] = getattr(anno, "pkg", None)

        return RuleResult(
            verdict=verdict,
            detail=cast("YAMLDict | None", detail),
            file=cast("tuple[str | int, ...] | None", task.file_info()),
            rule=self.get_metadata(),
        )
