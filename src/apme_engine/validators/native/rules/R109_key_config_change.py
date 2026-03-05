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
class KeyConfigChangeRule(Rule):
    rule_id: str = "R109"
    description: str = "Key configuration is changed"
    enabled: bool = True
    name: str = "ConfigChange"
    version: str = "v0.0.1"
    severity: Severity = Severity.LOW
    tags: tuple = Tag.SYSTEM

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current

        ac = AnnotationCondition().risk_type(RiskType.CONFIG_CHANGE).attr("is_mutable_key", True)
        verdict = task.has_annotation_by_condition(ac)

        detail = {}
        if verdict:
            anno = task.get_annotation_by_condition(ac)
            if anno:
                detail["key"] = anno.key

        return RuleResult(verdict=verdict, detail=detail, file=task.file_info(), rule=self.get_metadata())
