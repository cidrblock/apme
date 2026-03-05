# Colocated tests for L026 (NonFQCNUseRule). Uses Python-object context from _test_helpers.

import pytest

from apme_engine.validators.native.rules._test_helpers import (
    make_task_spec,
    make_task_call,
    make_context,
)
from apme_engine.validators.native.rules.L026_non_fqcn_use import NonFQCNUseRule
from apme_engine.engine.models import ExecutableType


def test_L026_fires_when_short_module_not_builtin():
    spec = make_task_spec(
        module="copy",
        executable="copy",
        executable_type=ExecutableType.MODULE_TYPE,
        resolved_name="community.general.copy",
    )
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = NonFQCNUseRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result.verdict is True
    assert result.rule.rule_id == "L026"


def test_L026_does_not_fire_when_fqcn_builtin():
    spec = make_task_spec(
        module="ansible.builtin.copy",
        executable="ansible.builtin.copy",
        executable_type=ExecutableType.MODULE_TYPE,
        resolved_name="ansible.builtin.copy",
    )
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = NonFQCNUseRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result.verdict is False


def test_L026_does_not_fire_for_non_task():
    from apme_engine.validators.native.rules._test_helpers import make_role_spec, make_role_call
    role_spec = make_role_spec(name="foo")
    role = make_role_call(role_spec)
    ctx = make_context(role)
    rule = NonFQCNUseRule()
    assert not rule.match(ctx)
