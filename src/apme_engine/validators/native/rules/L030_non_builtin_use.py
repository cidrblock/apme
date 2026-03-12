from dataclasses import dataclass

from apme_engine.engine.models import (
    AnsibleRunContext,
    Rule,
    RuleResult,
    RunTargetType,
    Severity,
)
from apme_engine.engine.models import (
    ExecutableType as ActionType,
)
from apme_engine.engine.models import (
    RuleTag as Tag,
)


@dataclass
class NonBuiltinUseRule(Rule):
    rule_id: str = "L030"
    description: str = "Non-builtin module is used"
    enabled: bool = True
    name: str = "NonBuiltinUse"
    version: str = "v0.0.1"
    severity: Severity = Severity.VERY_LOW
    tags: tuple = Tag.DEPENDENCY

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current

        verdict = (
            task.action_type == ActionType.MODULE_TYPE
            and task.resolved_action
            and not task.resolved_action.startswith("ansible.builtin.")
        )

        detail = {
            "fqcn": task.resolved_name,
        }

        return RuleResult(verdict=verdict, detail=detail, file=task.file_info(), rule=self.get_metadata())
