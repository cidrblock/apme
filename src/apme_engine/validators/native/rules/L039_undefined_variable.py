from dataclasses import dataclass

from apme_engine.engine.models import (
    AnsibleRunContext,
    RunTargetType,
    VariableType,
    Rule,
    Severity,
    RuleTag as Tag,
    RuleResult,
)


@dataclass
class UndefinedVariableRule(Rule):
    rule_id: str = "L039"
    description: str = "Undefined variable is found"
    enabled: bool = True
    name: str = "UndefinedVariable"
    version: str = "v0.0.1"
    severity: Severity = Severity.LOW
    tags: tuple = Tag.VARIABLE

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current

        verdict = False
        detail = {}
        for v_name in task.variable_use:
            v = task.variable_use[v_name]
            if v and v[-1].type == VariableType.Unknown:
                verdict = True
                current = detail.get("undefined_variables", [])
                current.append(v_name)
                detail["undefined_variables"] = current

        return RuleResult(verdict=verdict, detail=detail, file=task.file_info(), rule=self.get_metadata())
