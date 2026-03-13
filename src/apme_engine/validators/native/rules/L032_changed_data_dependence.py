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
    rule_id: str = "L032"
    description: str = "A variable is re-defined"
    enabled: bool = True
    name: str = "ChangedDataDependence"
    version: str = "v0.0.1"
    severity: str = Severity.VERY_LOW
    tags: tuple[str, ...] = (Tag.VARIABLE,)

    def match(self, ctx: AnsibleRunContext) -> bool:
        if ctx.current is None:
            return False
        return bool(ctx.current.type == RunTargetType.Task)

    def process(self, ctx: AnsibleRunContext) -> RuleResult | None:
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
