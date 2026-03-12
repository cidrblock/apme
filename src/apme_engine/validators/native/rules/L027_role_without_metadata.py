from dataclasses import dataclass

from apme_engine.engine.models import (
    AnsibleRunContext,
    Rule,
    RuleResult,
    RunTargetType,
    Severity,
)
from apme_engine.engine.models import (
    RuleTag as Tag,
)


@dataclass
class RoleWithoutMetadataRule(Rule):
    rule_id: str = "L027"
    description: str = "A role without metadata is used"
    enabled: bool = True
    name: str = "RoleWithoutMetadata"
    version: str = "v0.0.1"
    severity: Severity = Severity.LOW
    tags: tuple = Tag.DEPENDENCY

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Role

    def process(self, ctx: AnsibleRunContext):
        role = ctx.current

        verdict = not role.spec.metadata

        return RuleResult(verdict=verdict, file=role.file_info(), rule=self.get_metadata())
