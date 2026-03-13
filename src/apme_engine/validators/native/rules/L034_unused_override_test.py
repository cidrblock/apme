# Colocated tests for L034 (UnusedOverrideRule / R203).

from typing import cast

from apme_engine.engine.models import Variable, VariableType, YAMLDict, YAMLValue
from apme_engine.validators.native.rules._test_helpers import (
    make_context,
    make_task_call,
    make_task_spec,
)
from apme_engine.validators.native.rules.L034_unused_override import UnusedOverrideRule


def test_L034_does_not_fire_when_no_defined_vars() -> None:
    spec = make_task_spec(module="ansible.builtin.copy")
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = UnusedOverrideRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result is not None
    assert result.verdict is False
    assert result.rule is not None and result.rule.rule_id == "L034"


def test_L034_fires_when_new_definition_has_lower_precedence() -> None:
    spec = make_task_spec(module="ansible.builtin.set_fact")
    spec.set_facts = {"my_var": "x"}
    task = make_task_call(spec)
    task.variable_set["my_var"] = cast(
        YAMLValue,
        [
            Variable(name="my_var", value="a", type=VariableType.SetFacts, setter=None),
            Variable(name="my_var", value="b", type=VariableType.RoleDefaults, setter=None),
        ],
    )
    ctx = make_context(task)
    rule = UnusedOverrideRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result is not None
    assert result.verdict is True
    assert result.detail is not None
    variables = result.detail.get("variables")
    assert isinstance(variables, list) and len(variables) == 1
    assert cast(YAMLDict, variables[0]).get("new_precedence") == VariableType.RoleDefaults


def test_L034_does_not_fire_when_single_definition() -> None:
    spec = make_task_spec(module="ansible.builtin.set_fact")
    spec.set_facts = {"my_var": "x"}
    task = make_task_call(spec)
    task.variable_set["my_var"] = cast(
        YAMLValue,
        [Variable(name="my_var", value="x", setter=None)],
    )
    ctx = make_context(task)
    rule = UnusedOverrideRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result is not None
    assert result.verdict is False
