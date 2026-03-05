from dataclasses import dataclass

from apme_engine.engine.models import (
    AnsibleRunContext,
    RunTargetType,
    DefaultRiskType as RiskType,
    AnnotationCondition,
    Rule,
    Severity,
    RuleTag as Tag,
    RuleResult,
)


@dataclass
class FilePermissionRule(Rule):
    rule_id: str = "L031"
    description: str = "File permission is not secure."
    enabled: bool = False
    name: str = "FilePermissionRule"
    version: str = "v0.0.1"
    severity: Severity = Severity.MEDIUM
    tags: tuple = Tag.SYSTEM

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current

        # define a condition for this rule here
        ac = AnnotationCondition().risk_type(RiskType.FILE_CHANGE).attr("is_insecure_permissions", True)
        verdict = task.has_annotation_by_condition(ac)

        return RuleResult(verdict=verdict, file=task.file_info(), rule=self.get_metadata())
