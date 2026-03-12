from dataclasses import dataclass

from apme_engine.engine.models import (
    AnnotationCondition,
    AnsibleRunContext,
    Rule,
    RuleResult,
    RunTargetType,
    Severity,
)
from apme_engine.engine.models import DefaultRiskType as RiskType
from apme_engine.engine.models import (
    RuleTag as Tag,
)


@dataclass
class CommandExecRule(Rule):
    rule_id: str = "R101"
    description: str = "A parameterized command execution found"
    enabled: bool = True
    name: str = "CommandExec"
    version: str = "v0.0.1"
    severity: Severity = Severity.LOW
    tags: tuple = Tag.COMMAND

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current

        ac = AnnotationCondition().risk_type(RiskType.CMD_EXEC).attr("is_mutable_cmd", True)
        verdict = task.has_annotation_by_condition(ac)

        detail = {}
        if verdict:
            anno = task.get_annotation_by_condition(ac)
            if anno:
                detail["cmd"] = anno.command.raw

        return RuleResult(verdict=verdict, detail=detail, file=task.file_info(), rule=self.get_metadata())
