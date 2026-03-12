# Colocated tests for L039 (UndefinedVariableRule / R306).

from apme_engine.engine.models import Variable, VariableType
from apme_engine.validators.native.rules._test_helpers import (
    make_context,
    make_task_call,
    make_task_spec,
)
from apme_engine.validators.native.rules.L039_undefined_variable import UndefinedVariableRule


def test_L039_does_not_fire_when_no_variable_use():
    spec = make_task_spec(module="ansible.builtin.copy")
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = UndefinedVariableRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result.verdict is False
    assert result.rule.rule_id == "L039"


def test_L039_fires_when_variable_use_has_unknown():
    spec = make_task_spec(module="ansible.builtin.copy")
    task = make_task_call(spec)
    v = Variable(name="unknown_var", value="", type=VariableType.Unknown)
    task.variable_use["unknown_var"] = [v]
    ctx = make_context(task)
    rule = UndefinedVariableRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result.verdict is True
    assert "undefined_variables" in result.detail
    assert "unknown_var" in result.detail["undefined_variables"]
