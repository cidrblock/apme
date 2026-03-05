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
class InlineEnvVarRule(Rule):
    rule_id: str = "L045"
    description: str = "Avoid inline environment variables in tasks; use env file or role vars"
    enabled: bool = True
    name: str = "InlineEnvVar"
    version: str = "v0.0.1"
    severity: Severity = Severity.VERY_LOW
    tags: tuple = Tag.CODING

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current
        options = getattr(task.spec, "options", None) or {}
        has_env = "environment" in options and options.get("environment")
        verdict = bool(has_env)
        detail = {}
        if verdict:
            detail["message"] = "task uses inline environment; consider env file or variables"
        return RuleResult(verdict=verdict, detail=detail, file=task.file_info(), rule=self.get_metadata())
