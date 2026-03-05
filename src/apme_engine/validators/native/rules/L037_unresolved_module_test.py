# Colocated tests for L037 (UnresolvedModuleRule).

from apme_engine.validators.native.rules._test_helpers import (
    make_task_spec,
    make_task_call,
    make_context,
)
from apme_engine.validators.native.rules.L037_unresolved_module import UnresolvedModuleRule
from apme_engine.engine.models import ExecutableType


def test_L037_fires_when_module_unresolved():
    spec = make_task_spec(
        module="unknown_module",
        executable_type=ExecutableType.MODULE_TYPE,
        resolved_name="",
    )
    spec.resolved_name = ""  # override helper fallback so module stays unresolved
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = UnresolvedModuleRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result.verdict is True
    assert result.rule.rule_id == "L037"


def test_L037_does_not_fire_when_module_resolved():
    spec = make_task_spec(
        module="copy",
        executable_type=ExecutableType.MODULE_TYPE,
        resolved_name="ansible.builtin.copy",
    )
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = UnresolvedModuleRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result.verdict is False
