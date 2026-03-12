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
class UnusedOverrideRule(Rule):
    rule_id: str = "L034"
    description: str = "A variable is not successfully re-defined because of low precedence"
    enabled: bool = True
    name: str = "UnusedOverride"
    version: str = "v0.0.1"
    severity: Severity = Severity.VERY_LOW
    tags: tuple = Tag.VARIABLE

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current

        verdict = False
        detail = {"variables": []}
        if task.spec.defined_vars:
            for v in task.spec.defined_vars:
                all_definitions = task.variable_set.get(v, [])
                if len(all_definitions) > 1:
                    prev_prec = all_definitions[-2].type
                    new_prec = all_definitions[-1].type
                    if new_prec < prev_prec:
                        detail["variables"].append(
                            {
                                "name": v,
                                "prev_precedence": prev_prec,
                                "new_precedence": new_prec,
                            }
                        )
                        verdict = True

        return RuleResult(verdict=verdict, detail=detail, file=task.file_info(), rule=self.get_metadata())
