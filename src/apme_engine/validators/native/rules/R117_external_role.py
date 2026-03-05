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
class ExternalRoleRuleResult(RuleResult):
    pass


@dataclass
class ExternalRoleRule(Rule):
    rule_id: str = "R117"
    description: str = "An external role is used"
    enabled: bool = True
    name: str = "ExternalRole"
    version: str = "v0.0.1"
    severity: Severity = Severity.VERY_LOW
    tags: tuple = Tag.DEPENDENCY
    result_type: type = ExternalRoleRuleResult

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Role

    def process(self, ctx: AnsibleRunContext):
        role = ctx.current

        verdict = (
            not ctx.is_begin(role) and role.spec.metadata and isinstance(role.spec.metadata, dict) and role.spec.metadata.get("galaxy_info", None)
        )

        return RuleResult(verdict=verdict, file=role.file_info(), rule=self.get_metadata())
