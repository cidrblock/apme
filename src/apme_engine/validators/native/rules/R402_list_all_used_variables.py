from dataclasses import dataclass

from apme_engine.engine.models import (
    AnsibleRunContext,
    Rule,
    RuleResult,
    RunTargetType,
    Severity,
)
from apme_engine.engine.models import (
    RuleTag as Tag,
)


@dataclass
class ListAllUsedVariablesRule(Rule):
    rule_id: str = "R402"
    description: str = "Listing all used variables"
    enabled: bool = True
    name: str = "ListAllUsedVariables"
    version: str = "v0.0.1"
    severity: Severity = Severity.NONE
    tags: tuple = Tag.VARIABLE

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current

        verdict = False
        detail = {}
        if ctx.is_end(task):
            verdict = True
            detail["metadata"] = ctx.info
            detail["variables"] = list(task.variable_use.keys())

        return RuleResult(verdict=verdict, detail=detail, file=task.file_info(), rule=self.get_metadata())
