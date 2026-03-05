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
class MetaIncorrectRule(Rule):
    rule_id: str = "L053"
    description: str = "Role meta should have valid structure (galaxy_info, dependencies)"
    enabled: bool = True
    name: str = "MetaIncorrect"
    version: str = "v0.0.1"
    severity: Severity = Severity.LOW
    tags: tuple = Tag.DEPENDENCY

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Role

    def process(self, ctx: AnsibleRunContext):
        role = ctx.current
        metadata = getattr(role.spec, "metadata", None) or {}
        if not isinstance(metadata, dict):
            return RuleResult(verdict=True, detail={"message": "metadata must be a dict"}, file=role.file_info(), rule=self.get_metadata())
        galaxy_info = metadata.get("galaxy_info")
        if galaxy_info is not None and not isinstance(galaxy_info, dict):
            return RuleResult(verdict=True, detail={"message": "galaxy_info must be a dict"}, file=role.file_info(), rule=self.get_metadata())
        deps = metadata.get("dependencies")
        if deps is not None and not isinstance(deps, list):
            return RuleResult(verdict=True, detail={"message": "dependencies must be a list"}, file=role.file_info(), rule=self.get_metadata())
        return RuleResult(verdict=False, file=role.file_info(), rule=self.get_metadata())
