from dataclasses import dataclass
import re

from apme_engine.engine.models import (
    AnsibleRunContext,
    RunTargetType,
    Rule,
    Severity,
    RuleTag as Tag,
    RuleResult,
)

VAR_NAMING_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass
class VarNamingRule(Rule):
    rule_id: str = "L050"
    description: str = "Variable names should follow naming convention (lowercase, underscores)"
    enabled: bool = True
    name: str = "VarNaming"
    version: str = "v0.0.1"
    severity: Severity = Severity.VERY_LOW
    tags: tuple = Tag.VARIABLE

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current
        variable_use = getattr(task, "variable_use", None) or {}
        invalid = [k for k in variable_use if k and not VAR_NAMING_PATTERN.match(k)]
        verdict = len(invalid) > 0
        detail = {}
        if invalid:
            detail["variables"] = invalid
            detail["message"] = "variable names should be lowercase with underscores"
        return RuleResult(verdict=verdict, detail=detail, file=task.file_info(), rule=self.get_metadata())
