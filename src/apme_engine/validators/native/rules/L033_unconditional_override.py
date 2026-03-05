from dataclasses import dataclass

from apme_engine.engine.models import (
    AnsibleRunContext,
    RunTargetType,
    Rule,
    Severity,
    RuleTag as Tag,
    RuleResult,
)


@dataclass
class UnconditionalOverrideRule(Rule):
    rule_id: str = "L033"
    description: str = "A variable is re-defined without any conditions"
    enabled: bool = True
    name: str = "UnconditionalOverride"
    version: str = "v0.0.1"
    severity: Severity = Severity.VERY_LOW
    tags: tuple = Tag.VARIABLE

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current

        verdict = False
        detail = {"variables": []}
        if not task.spec.tags and not task.spec.when:
            if task.spec.defined_vars:
                for v in task.spec.defined_vars:
                    all_definitions = task.variable_set.get(v, [])
                    if len(all_definitions) > 1:
                        detail["variables"].append(
                            {
                                "name": v,
                                "defined_by": [d.setter for d in all_definitions],
                                "type": [d.type for d in all_definitions],
                            }
                        )
                        verdict = True

        return RuleResult(verdict=verdict, detail=detail, file=task.file_info(), rule=self.get_metadata())
