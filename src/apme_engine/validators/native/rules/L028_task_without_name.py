from dataclasses import dataclass

from apme_engine.engine.models import (
    AnsibleRunContext,
    RunTargetType,
    Rule,
    Severity,
    RuleTag as Tag,
    RuleResult,
)


@dataclass
class TaskWithoutNameRule(Rule):
    rule_id: str = "L028"
    description: str = "A task without name is found"
    enabled: bool = True
    name: str = "TaskWithoutName"
    version: str = "v0.0.1"
    severity: Severity = Severity.LOW
    tags: tuple = Tag.DEPENDENCY

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current

        verdict = not task.spec.name

        return RuleResult(verdict=verdict, file=task.file_info(), rule=self.get_metadata())
