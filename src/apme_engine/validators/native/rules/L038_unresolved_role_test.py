# Colocated tests for L038 (UnresolvedRoleRule).

from apme_engine.validators.native.rules._test_helpers import (
    make_task_spec,
    make_task_call,
    make_context,
)
from apme_engine.validators.native.rules.L038_unresolved_role import UnresolvedRoleRule
from apme_engine.engine.models import ExecutableType


def test_L038_fires_when_role_unresolved():
    spec = make_task_spec(
        module="some_role",
        executable="some_role",
        executable_type=ExecutableType.ROLE_TYPE,
        resolved_name="",  # unresolved
    )
    spec.resolved_name = ""  # override helper fallback so role stays unresolved
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = UnresolvedRoleRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result.verdict is True
    assert result.rule.rule_id == "L038"


def test_L038_does_not_fire_when_role_resolved():
    spec = make_task_spec(
        module="geerlingguy.docker",
        executable_type=ExecutableType.ROLE_TYPE,
        resolved_name="geerlingguy.docker",
    )
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = UnresolvedRoleRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result.verdict is False


def test_L038_does_not_fire_for_module_task():
    spec = make_task_spec(module="copy", executable_type=ExecutableType.MODULE_TYPE)
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = UnresolvedRoleRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result.verdict is False
