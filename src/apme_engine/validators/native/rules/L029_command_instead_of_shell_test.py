# Colocated tests for L029 (UseShellRule). Uses Python-object context from _test_helpers.

import pytest

from apme_engine.validators.native.rules._test_helpers import (
    make_task_spec,
    make_task_call,
    make_context,
)
from apme_engine.validators.native.rules.L029_command_instead_of_shell import UseShellRule
from apme_engine.engine.models import ExecutableType


def test_L029_fires_when_resolved_is_shell():
    spec = make_task_spec(
        module="shell",
        executable="shell",
        executable_type=ExecutableType.MODULE_TYPE,
        resolved_name="ansible.builtin.shell",
    )
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = UseShellRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result.verdict is True
    assert result.rule.rule_id == "L029"


def test_L029_does_not_fire_when_resolved_is_command():
    spec = make_task_spec(
        module="command",
        executable="command",
        executable_type=ExecutableType.MODULE_TYPE,
        resolved_name="ansible.builtin.command",
    )
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = UseShellRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result.verdict is False
