from dataclasses import dataclass

from apme_engine.engine.models import (
    AnsibleRunContext,
    RunTargetType,
    Rule,
    Severity,
    RuleTag as Tag,
    RuleResult,
)

# Default threshold: play/block with more than this many tasks may be considered complex
DEFAULT_TASK_COUNT_THRESHOLD = 20


@dataclass
class ComplexityRule(Rule):
    rule_id: str = "L042"
    description: str = "Play or block has high task count (complexity)"
    enabled: bool = True
    name: str = "Complexity"
    version: str = "v0.0.1"
    severity: Severity = Severity.VERY_LOW
    tags: tuple = Tag.DEPENDENCY

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current
        sequence = getattr(ctx.sequence, "items", []) or []
        task_count = sum(1 for t in sequence if getattr(t, "type", "") == RunTargetType.Task)
        threshold = getattr(self, "task_count_threshold", None) or DEFAULT_TASK_COUNT_THRESHOLD
        verdict = task_count > threshold
        detail = {}
        if verdict:
            detail["task_count"] = task_count
            detail["threshold"] = threshold
        return RuleResult(verdict=verdict, detail=detail, file=task.file_info(), rule=self.get_metadata())
