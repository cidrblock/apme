from dataclasses import dataclass
import re

from apme_engine.engine.models import (
    AnsibleRunContext,
    RunTargetType,
    Rule,
    Severity,
    RuleTag as Tag,
    RuleResult,
)

URL_PATTERN = re.compile(r"^https?://\S+$")


@dataclass
class MetaVideoLinksRule(Rule):
    rule_id: str = "L055"
    description: str = "Role meta video_links should be valid URLs"
    enabled: bool = True
    name: str = "MetaVideoLinks"
    version: str = "v0.0.1"
    severity: Severity = Severity.VERY_LOW
    tags: tuple = Tag.DEPENDENCY

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Role

    def process(self, ctx: AnsibleRunContext):
        role = ctx.current
        metadata = getattr(role.spec, "metadata", None) or {}
        galaxy_info = metadata.get("galaxy_info") if isinstance(metadata.get("galaxy_info"), dict) else {}
        video_links = galaxy_info.get("video_links") if galaxy_info else None
        if not video_links:
            return RuleResult(verdict=False, file=role.file_info(), rule=self.get_metadata())
        if not isinstance(video_links, list):
            return RuleResult(verdict=True, detail={"message": "video_links must be a list"}, file=role.file_info(), rule=self.get_metadata())
        invalid = [u for u in video_links if not (isinstance(u, str) and URL_PATTERN.match(u.strip()))]
        verdict = len(invalid) > 0
        detail = {}
        if invalid:
            detail["invalid_links"] = invalid[:10]
        return RuleResult(verdict=verdict, detail=detail, file=role.file_info(), rule=self.get_metadata())
