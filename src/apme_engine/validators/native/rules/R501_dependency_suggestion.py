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
class DependencySuggestionRule(Rule):
    rule_id: str = "R501"
    description: str = "Suggest dependencies for unresolved modules/roles"
    enabled: bool = True
    name: str = "DependencySuggestion"
    version: str = "v0.0.1"
    severity: Severity = Severity.NONE
    tags: tuple = Tag.DEPENDENCY

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current

        verdict = False
        detail = {}
        if task.spec.possible_candidates:
            verdict = True
            detail["type"] = task.spec.executable_type.lower()
            detail["fqcn"] = task.spec.possible_candidates[0][0]
            req_info = task.spec.possible_candidates[0][1]
            detail["suggestion"] = {}
            detail["suggestion"]["type"] = req_info.get("type", "")
            detail["suggestion"]["name"] = req_info.get("name", "")
            detail["suggestion"]["version"] = req_info.get("version", "")

        return RuleResult(verdict=verdict, detail=detail, file=task.file_info(), rule=self.get_metadata())
