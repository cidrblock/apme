from dataclasses import dataclass

from apme_engine.engine.models import (
    AnsibleRunContext,
    Rule,
    RuleResult,
    RunTargetType,
    Severity,
    VariableDict,
)
from apme_engine.engine.models import (
    RuleTag as Tag,
)


@dataclass
class ShowVariablesRule(Rule):
    rule_id: str = "R404"
    description: str = "Show all variables"
    enabled: bool = False
    name: str = "ShowVariables"
    version: str = "v0.0.1"
    severity: Severity = Severity.NONE
    tags: tuple = Tag.VARIABLE

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current

        verdict = True
        detail = {"variables": task.variable_set}

        return RuleResult(verdict=verdict, detail=detail, file=task.file_info(), rule=self.get_metadata())

    def print(self, result: RuleResult):
        variables = result.detail["variables"]
        var_table = "None"
        if variables:
            var_table = "\n" + VariableDict.print_table(variables)
        output = f"ruleID={self.rule_id}, \
            severity={self.severity}, \
            description={self.description}, \
            verdict={result.verdict}, \
            file={result.file}, \
            variables={var_table}\n"
        return output
