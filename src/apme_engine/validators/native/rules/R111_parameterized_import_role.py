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
class ParameterizedImportRoleRule(Rule):
    rule_id: str = "R111"
    description: str = "Import/include a parameterized name of role"
    enabled: bool = True
    name: str = "ParameterizedImportRole"
    version: str = "v0.0.1"
    severity: Severity = Severity.HIGH
    tags: tuple = Tag.DEPENDENCY

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current

        role_ref_arg = task.args.get("name")
        verdict = task.action_type == ActionType.ROLE_TYPE and role_ref_arg and role_ref_arg.is_mutable
        role_ref = role_ref_arg.raw if role_ref_arg else None
        detail = {
            "role": role_ref,
        }

        return RuleResult(verdict=verdict, detail=detail, file=task.file_info(), rule=self.get_metadata())
