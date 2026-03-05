from dataclasses import dataclass

from apme_engine.engine.models import (
    AnsibleRunContext,
    RunTargetType,
    ExecutableType as ActionType,
    Rule,
    Severity,
    RuleTag as Tag,
    RuleResult,
)

FREE_FORM_ACTIONS = frozenset(
    {
        "ansible.builtin.raw",
        "ansible.builtin.command",
        "ansible.builtin.shell",
        "ansible.legacy.raw",
        "ansible.legacy.command",
        "ansible.legacy.shell",
    }
)


@dataclass
class NoFreeFormRule(Rule):
    rule_id: str = "L046"
    description: str = "Avoid raw/command/shell without explicit args (use args: key)"
    enabled: bool = True
    name: str = "NoFreeForm"
    version: str = "v0.0.1"
    severity: Severity = Severity.LOW
    tags: tuple = Tag.COMMAND

    def match(self, ctx: AnsibleRunContext) -> bool:
        return ctx.current.type == RunTargetType.Task

    def process(self, ctx: AnsibleRunContext):
        task = ctx.current
        if task.action_type != ActionType.MODULE_TYPE:
            return RuleResult(verdict=False, file=task.file_info(), rule=self.get_metadata())
        resolved = getattr(task.spec, "resolved_name", "") or ""
        if resolved not in FREE_FORM_ACTIONS:
            return RuleResult(verdict=False, file=task.file_info(), rule=self.get_metadata())
        raw = getattr(task.args, "raw", None)
        # Free-form: args passed as a single string (no structured key)
        is_free_form = isinstance(raw, str) and raw.strip() != ""
        verdict = is_free_form
        detail = {}
        if verdict:
            detail["module"] = resolved
            detail["message"] = "use args: with a list or cmd: key instead of free-form string"
        return RuleResult(verdict=verdict, detail=detail, file=task.file_info(), rule=self.get_metadata())
