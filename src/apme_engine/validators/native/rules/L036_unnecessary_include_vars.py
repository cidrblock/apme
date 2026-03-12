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
class UnnecessaryIncludeVarsRule(Rule):
    rule_id: str = "L036"
    description: str = "include_vars is used without any condition"
    enabled: bool = True
    name: str = "UnnecessaryIncludeVars"
    version: str = "v0.0.1"
    severity: Severity = Severity.VERY_LOW
    tags: tuple = Tag.VARIABLE

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current

        verdict = (
            task.action_type == ActionType.MODULE_TYPE
            and task.resolved_action
            and task.resolved_action == "ansible.builtin.include_vars"
            and not task.spec.tags
            and not task.spec.when
        )

        return RuleResult(verdict=verdict, file=task.file_info(), rule=self.get_metadata())
