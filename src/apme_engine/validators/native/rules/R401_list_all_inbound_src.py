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
class ListAllInboundSrcRule(Rule):
    rule_id: str = "R401"
    description: str = "List all inbound sources"
    enabled: bool = True
    name: str = "ListAllInboundSrcRule"
    version: str = "v0.0.1"
    severity: Severity = Severity.VERY_LOW
    tags: tuple = Tag.DEBUG

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current

        ac = AnnotationCondition().risk_type(RiskType.INBOUND)
        verdict = False
        detail = {}
        src_list = []
        if ctx.is_end(task):
            tasks = ctx.search(ac)
            for t in tasks:
                anno = t.get_annotation_by_condition(ac)
                if anno:
                    src_list.append(anno.src.value)
            if len(src_list) > 0:
                verdict = True
                detail["inbound_src"] = src_list

        return RuleResult(verdict=verdict, detail=detail, file=task.file_info(), rule=self.get_metadata())
