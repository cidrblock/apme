# L054: Role meta galaxy_info should include galaxy_tags

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
class MetaNoTagsRule(Rule):
    rule_id: str = "L054"
    description: str = "Role meta galaxy_info should include galaxy_tags"
    enabled: bool = True
    name: str = "MetaNoTags"
    version: str = "v0.0.1"
    severity: Severity = Severity.VERY_LOW
    tags: tuple = Tag.DEPENDENCY

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Role

    def process(self, ctx: AnsibleRunContext):
        role = ctx.current
        metadata = getattr(role.spec, "metadata", None) or {}
        gi = metadata.get("galaxy_info")
        galaxy_info = gi if isinstance(gi, dict) else {}
        if not galaxy_info:
            return RuleResult(verdict=False, file=role.file_info(), rule=self.get_metadata())
        tags = galaxy_info.get("galaxy_tags") or galaxy_info.get("categories")
        verdict = not tags or (isinstance(tags, list) and len(tags) == 0)
        detail = {}
        if verdict:
            detail["message"] = "galaxy_info should include galaxy_tags or categories"
        return RuleResult(verdict=verdict, detail=detail, file=role.file_info(), rule=self.get_metadata())
