# -*- mode:python; coding:utf-8 -*-
# L052: Galaxy version in meta should follow semantic version format

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

GALAXY_VERSION_PATTERN = re.compile(r"^\d+\.\d+(\.\d+)?$")


@dataclass
class GalaxyVersionIncorrectRule(Rule):
    rule_id: str = "L052"
    description: str = "Galaxy version in meta should follow semantic version format (x.y.z)"
    enabled: bool = True
    name: str = "GalaxyVersionIncorrect"
    version: str = "v0.0.1"
    severity: Severity = Severity.LOW
    tags: tuple = Tag.DEPENDENCY

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Role

    def process(self, ctx: AnsibleRunContext):
        role = ctx.current
        metadata = getattr(role.spec, "metadata", None) or {}
        gi = metadata.get("galaxy_info")
        galaxy_info = gi if isinstance(gi, dict) else {}
        version = galaxy_info.get("version") if galaxy_info else None
        if version is None:
            return RuleResult(verdict=False, file=role.file_info(), rule=self.get_metadata())
        vs = str(version).strip()
        verdict = not bool(GALAXY_VERSION_PATTERN.match(vs))
        detail = {}
        if verdict:
            detail["version"] = vs
            detail["message"] = "galaxy version should be semantic (e.g. 1.0.0)"
        return RuleResult(verdict=verdict, detail=detail, file=role.file_info(), rule=self.get_metadata())
