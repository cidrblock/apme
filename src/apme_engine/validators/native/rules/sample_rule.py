from dataclasses import dataclass

from apme_engine.engine.models import (
    AnsibleRunContext,
    Rule,
    RuleResult,
    RunTargetType,
    Severity,
)


@dataclass
class SampleRule(Rule):
    rule_id: str = "Sample101"
    description: str = "echo task block"
    enabled: bool = False
    name: str = "EchoTaskContent"
    version: str = "v0.0.1"
    severity: Severity = Severity.NONE
    tags: tuple = "sample"

    def match(self, ctx: AnsibleRunContext) -> bool:
        # specify targets to be checked
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current

        verdict = True
        detail = {}
        task_block = task.content.yaml()
        detail["task_block"] = task_block

        return RuleResult(verdict=verdict, detail=detail, file=task.file_info(), rule=self.get_metadata())
