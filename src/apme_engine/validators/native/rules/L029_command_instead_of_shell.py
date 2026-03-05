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
class UseShellRule(Rule):
    rule_id: str = "L029"
    description: str = "Use 'command' module instead of 'shell' "
    enabled: bool = True
    name: str = "UseShellRule"
    version: str = "v0.0.1"
    severity: Severity = Severity.VERY_LOW
    tags: tuple = Tag.COMMAND

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current

        # define a condition for this rule here
        verdict = (
            task.action_type == ActionType.MODULE_TYPE
            and task.spec.action
            and task.resolved_action
            and task.resolved_action == "ansible.builtin.shell"
        )

        return RuleResult(verdict=verdict, file=task.file_info(), rule=self.get_metadata())
