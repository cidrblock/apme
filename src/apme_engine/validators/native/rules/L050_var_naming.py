import re
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

VAR_NAMING_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass
class VarNamingRule(Rule):
    rule_id: str = "L050"
    description: str = "Variable names should follow naming convention (lowercase, underscores)"
    enabled: bool = True
    name: str = "VarNaming"
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
        variable_use = getattr(task, "variable_use", None) or {}
        invalid = [k for k in variable_use if k and not VAR_NAMING_PATTERN.match(k)]
        verdict = len(invalid) > 0
        detail: dict[str, object] = {}
        if invalid:
            detail["variables"] = invalid
            detail["message"] = "variable names should be lowercase with underscores"
        return RuleResult(
            verdict=verdict,
            detail=cast(YAMLDict | None, detail),
            file=cast("tuple[str | int, ...] | None", task.file_info()),
            rule=self.get_metadata(),
        )
