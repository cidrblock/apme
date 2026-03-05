from dataclasses import dataclass
from apme_engine.engine.models import (
    AnsibleRunContext,
    RunTargetType,
    ExecutableType as ActionType,
    Rule,
    Severity,
    RuleTag as Tag,
    RuleResult,
)


@dataclass
class UnresolvedRoleRuleResult(RuleResult):
    pass


@dataclass
class UnresolvedRoleRule(Rule):
    rule_id: str = "L038"
    description: str = "Unresolved role is found"
    enabled: bool = True
    name: str = "UnresolvedRole"
    version: str = "v0.0.1"
    severity: Severity = Severity.LOW
    tags: tuple = Tag.DEPENDENCY
    result_type: type = UnresolvedRoleRuleResult

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current

        verdict = task.action_type == ActionType.ROLE_TYPE and task.spec.action and not task.resolved_action
        detail = {
            "role": task.spec.action,
        }

        return RuleResult(verdict=verdict, detail=detail, file=task.file_info(), rule=self.get_metadata())
