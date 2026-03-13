"""Tests for native rule L033."""

from typing import cast

from apme_engine.engine.models import YAMLValue
from apme_engine.validators.native.rules._test_helpers import (
    make_context,
    make_task_call,
    make_task_spec,
)
from apme_engine.validators.native.rules.L033_unconditional_override import UnconditionalOverrideRule


def test_L033_does_not_fire_when_no_defined_vars() -> None:
    """Verify L033 does not fire when no defined vars."""
    spec = make_task_spec(module="ansible.builtin.copy")
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = UnconditionalOverrideRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result is not None
    assert result.verdict is False
    assert result.rule is not None and result.rule.rule_id == "L033"


def test_L033_does_not_fire_when_task_has_tags() -> None:
    """Verify L033 does not fire when task has tags."""
    spec = make_task_spec(module="ansible.builtin.set_fact", options={"tags": ["config"]})
    spec.set_facts = {"x": "y"}
    task = make_task_call(spec)
    task.variable_set["x"] = cast("list[YAMLValue]", [object(), object()])
    ctx = make_context(task)
    rule = UnconditionalOverrideRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result is not None
    assert result.verdict is False
