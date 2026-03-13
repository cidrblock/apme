from dataclasses import dataclass
from typing import cast

from apme_engine.engine.models import (
    AnsibleRunContext,
    Rule,
    RuleResult,
    RunTargetType,
    Severity,
    YAMLDict,
)
from apme_engine.engine.models import (
    RuleTag as Tag,
)


@dataclass
class MetaIncorrectRule(Rule):
    rule_id: str = "L053"
    description: str = "Role meta should have valid structure (galaxy_info, dependencies)"
    enabled: bool = True
    name: str = "MetaIncorrect"
    version: str = "v0.0.1"
    severity: str = Severity.LOW
    tags: tuple[str, ...] = (Tag.DEPENDENCY,)

    def match(self, ctx: AnsibleRunContext) -> bool:
        if ctx.current is None:
            return False
        return bool(ctx.current.type == RunTargetType.Role)

    def process(self, ctx: AnsibleRunContext) -> RuleResult | None:
        role = ctx.current
        if role is None:
            return None
        metadata = getattr(role.spec, "metadata", None) or {}
        file_info = cast("tuple[str | int, ...] | None", role.file_info())
        if not isinstance(metadata, dict):
            return RuleResult(
                verdict=True,
                detail=cast(YAMLDict | None, {"message": "metadata must be a dict"}),
                file=file_info,
                rule=self.get_metadata(),
            )
        galaxy_info = metadata.get("galaxy_info")
        if galaxy_info is not None and not isinstance(galaxy_info, dict):
            return RuleResult(
                verdict=True,
                detail=cast(YAMLDict | None, {"message": "galaxy_info must be a dict"}),
                file=file_info,
                rule=self.get_metadata(),
            )
        deps = metadata.get("dependencies")
        if deps is not None and not isinstance(deps, list):
            return RuleResult(
                verdict=True,
                detail=cast(YAMLDict | None, {"message": "dependencies must be a list"}),
                file=file_info,
                rule=self.get_metadata(),
            )
        return RuleResult(verdict=False, file=file_info, rule=self.get_metadata())
