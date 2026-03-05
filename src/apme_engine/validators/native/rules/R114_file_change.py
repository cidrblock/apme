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
class FileChangeRule(Rule):
    rule_id: str = "R114"
    description: str = "Parameterized file change is found"
    enabled: bool = True
    name: str = "ConfigChange"
    version: str = "v0.0.1"
    severity: Severity = Severity.LOW
    tags: tuple = Tag.SYSTEM

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current

        ac = AnnotationCondition().risk_type(RiskType.FILE_CHANGE).attr("is_mutable_path", True)
        ac2 = AnnotationCondition().risk_type(RiskType.FILE_CHANGE).attr("is_mutable_src", True)
        verdict = False
        detail = {}
        if task.has_annotation_by_condition(ac):
            verdict = True
            anno = task.get_annotation_by_condition(ac)
            if anno:
                detail["path"] = anno.path.value

        if task.has_annotation_by_condition(ac2):
            verdict = True
            anno = task.get_annotation_by_condition(ac2)
            if anno:
                detail["src"] = anno.src.value

        return RuleResult(verdict=verdict, detail=detail, file=task.file_info(), rule=self.get_metadata())
