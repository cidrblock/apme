"""Tests for native rule L039."""

from typing import cast

from apme_engine.engine.models import Variable, VariableType, YAMLValue
from apme_engine.validators.native.rules._test_helpers import (
    make_context,
    make_task_call,
    make_task_spec,
)
from apme_engine.validators.native.rules.L039_undefined_variable import UndefinedVariableRule


def test_L039_does_not_fire_when_no_variable_use() -> None:
    """Verify L039 does not fire when no variable use."""
    spec = make_task_spec(module="ansible.builtin.copy")
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = UndefinedVariableRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result is not None
    assert result.verdict is False
    assert result.rule is not None and result.rule.rule_id == "L039"


def test_L039_fires_when_variable_use_has_unknown() -> None:
    """Verify L039 fires when variable use has unknown type."""
    spec = make_task_spec(module="ansible.builtin.copy")
    task = make_task_call(spec)
    v = Variable(name="unknown_var", value="", type=VariableType.Unknown)
    task.variable_use["unknown_var"] = cast("list[YAMLValue]", [v])
    ctx = make_context(task)
    rule = UndefinedVariableRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result is not None
    assert result.verdict is True
    assert result.detail is not None
    assert "undefined_variables" in result.detail
    uv: YAMLValue = result.detail["undefined_variables"]
    assert isinstance(uv, list)
    assert "unknown_var" in uv
