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
class PrivilegeEscalationRule(Rule):
    rule_id: str = "R108"
    description: str = "Privilege escalation is found"
    enabled: bool = True
    name: str = "PrivilegeEscalation"
    version: str = "v0.0.1"
    severity: Severity = Severity.HIGH
    tags: tuple = Tag.SYSTEM

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current

        verdict = task.become and task.become.enabled
        detail = {}
        if verdict:
            detail = task.become.__dict__

        return RuleResult(verdict=verdict, detail=detail, file=task.file_info(), rule=self.get_metadata())
