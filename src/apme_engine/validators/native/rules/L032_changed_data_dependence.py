"""Native rule L032: detect variable re-definition (changed data dependence)."""

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
    RuleTag as Tag,
)


@dataclass
class ChangedDataDependenceRule(Rule):
    """Rule for tasks that re-define variables.

    Attributes:
        rule_id: Rule identifier.
        description: Rule description.
        enabled: Whether the rule is enabled.
        name: Rule name.
        version: Rule version.
        severity: Severity level.
        tags: Rule tags.
    """

    rule_id: str = "L032"
    description: str = "A variable is re-defined"
    enabled: bool = True
    name: str = "ChangedDataDependence"
    version: str = "v0.0.1"
    severity: str = Severity.VERY_LOW
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
        """Check for variable re-definition and return result.

        Args:
            ctx: AnsibleRunContext to process.

        Returns:
            RuleResult with variables detail, or None.
        """
        task = ctx.current
        if task is None:
            return None

        verdict = False
        variables_list: list[dict[str, object]] = []
        defined_vars = getattr(task.spec, "defined_vars", None) or []
        variable_set = getattr(task, "variable_set", {}) or {}
        if defined_vars:
            for v in defined_vars:
                all_definitions = variable_set.get(v, [])
                if len(all_definitions) > 1:
                    variables_list.append(
                        {
                            "name": v,
                            "defined_by": [d.setter for d in all_definitions],
                        }
                    )
                    verdict = True

        detail: dict[str, object] = {"variables": variables_list}
        return RuleResult(
            verdict=verdict,
            detail=cast("YAMLDict | None", detail),
            file=cast("tuple[str | int, ...] | None", task.file_info()),
            rule=self.get_metadata(),
        )
