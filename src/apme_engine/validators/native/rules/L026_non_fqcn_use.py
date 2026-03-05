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
class NonFQCNUseRule(Rule):
    rule_id: str = "L026"
    description: str = "A task with a short module name is found"
    enabled: bool = True
    name: str = "NonFQCNUse"
    version: str = "v0.0.1"
    severity: Severity = Severity.VERY_LOW
    tags: tuple = Tag.DEPENDENCY

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current

        verdict = (
            task.action_type == ActionType.MODULE_TYPE
            and task.spec.action
            and task.resolved_action
            and task.spec.action != task.resolved_action
            and not task.resolved_action.startswith("ansible.builtin.")
        )
        detail = {
            "module": task.spec.action,
            "fqcn": task.resolved_name,
        }

        return RuleResult(verdict=verdict, detail=detail, file=task.file_info(), rule=self.get_metadata())
