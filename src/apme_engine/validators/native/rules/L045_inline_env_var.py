"""Native rule L045: detect inline environment variables in tasks."""

from dataclasses import dataclass
from typing import cast

from apme_engine.engine.models import (
    AnsibleRunContext,
    Rule,
    RuleResult,
    RunTargetType,
    Severity,
    YAMLDict,
)
from apme_engine.engine.models import (
    RuleTag as Tag,
)


@dataclass
class InlineEnvVarRule(Rule):
    """Rule for avoiding inline environment variables in tasks.

    Attributes:
        rule_id: Rule identifier.
        description: Rule description.
        enabled: Whether the rule is enabled.
        name: Rule name.
        version: Rule version.
        severity: Severity level.
        tags: Rule tags.
    """

    rule_id: str = "L045"
    description: str = "Avoid inline environment variables in tasks; use env file or role vars"
    enabled: bool = True
    name: str = "InlineEnvVar"
    version: str = "v0.0.1"
    severity: str = Severity.VERY_LOW
    tags: tuple[str, ...] = (Tag.CODING,)

    def match(self, ctx: AnsibleRunContext) -> bool:
        """Check if context has a task target.

        Args:
            ctx: AnsibleRunContext to evaluate.

        Returns:
            True if current target is a task.
        """
        if ctx.current is None:
            return False
        return bool(ctx.current.type == RunTargetType.Task)

    def process(self, ctx: AnsibleRunContext) -> RuleResult | None:
        """Check for inline environment and return result.

        Args:
            ctx: AnsibleRunContext to process.

        Returns:
            RuleResult with message detail, or None.
        """
        task = ctx.current
        if task is None:
            return None
        options = getattr(task.spec, "options", None) or {}
        has_env = "environment" in options and options.get("environment")
        verdict = bool(has_env)
        detail = {}
        if verdict:
            detail["message"] = "task uses inline environment; consider env file or variables"
        return RuleResult(
            verdict=verdict,
            detail=cast("YAMLDict | None", detail),
            file=cast("tuple[str | int, ...] | None", task.file_info()),
            rule=self.get_metadata(),
        )
