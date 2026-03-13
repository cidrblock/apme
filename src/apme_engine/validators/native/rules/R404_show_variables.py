"""Native rule R404: show all variables."""

from dataclasses import dataclass
from typing import cast

from apme_engine.engine.models import (
    AnsibleRunContext,
    Rule,
    RuleResult,
    RunTargetType,
    Severity,
    TaskCall,
    Variable,
    VariableDict,
    YAMLDict,
)
from apme_engine.engine.models import RuleTag as Tag


@dataclass
class ShowVariablesRule(Rule):
    """Rule to show all variables.

    Attributes:
        rule_id: Rule identifier.
        description: Rule description.
        enabled: Whether the rule is enabled.
        name: Rule name.
        version: Rule version.
        severity: Severity level.
        tags: Rule tags.
    """

    rule_id: str = "R404"
    description: str = "Show all variables"
    enabled: bool = False
    name: str = "ShowVariables"
    version: str = "v0.0.1"
    severity: str = Severity.NONE
    tags: tuple[str, ...] = (Tag.VARIABLE,)

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
        """Show variables and return result.

        Args:
            ctx: AnsibleRunContext to process.

        Returns:
            RuleResult with variables detail, or None.
        """
        task = ctx.current
        if task is None:
            return None

        verdict = True
        variables: YAMLDict = {}
        if isinstance(task, TaskCall):
            variables = task.variable_set
        detail: YAMLDict = {"variables": variables}

        return RuleResult(
            verdict=verdict,
            detail=detail,
            file=cast("tuple[str | int, ...] | None", task.file_info()),
            rule=self.get_metadata(),
        )

    def print(self, result: RuleResult) -> str:
        """Format rule result as string for display.

        Args:
            result: RuleResult to format.

        Returns:
            Formatted string representation.
        """
        variables = result.detail.get("variables") if result.detail is not None else None
        var_table: str = "None"
        if variables and isinstance(variables, dict):
            var_table = "\n" + VariableDict.print_table(cast(dict[str, list[Variable]], variables))
        output = f"ruleID={self.rule_id}, \
            severity={self.severity}, \
            description={self.description}, \
            verdict={result.verdict}, \
            file={result.file}, \
            variables={var_table}\n"
        return output
