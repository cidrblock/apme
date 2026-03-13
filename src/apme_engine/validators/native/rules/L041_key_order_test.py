"""Tests for native rule L041."""

from apme_engine.validators.native.rules._test_helpers import (
    make_context,
    make_task_call,
    make_task_spec,
)
from apme_engine.validators.native.rules.L041_key_order import KeyOrderRule


def test_L041_fires_when_name_after_action() -> None:
    """Verify L041 fires when name appears after action key."""
    spec = make_task_spec(module="ansible.builtin.copy")
    spec.yaml_lines = "copy:\n  src: a\n  dest: b\nname: Copy file"
    spec.module = "copy"
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = KeyOrderRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result is not None
    assert result.verdict is True
    assert result.rule is not None and result.rule.rule_id == "L041"
    assert result.detail is not None
    assert "keys_order" in result.detail


def test_L041_does_not_fire_when_name_before_action() -> None:
    """Verify L041 does not fire when name appears before action."""
    spec = make_task_spec(name="Copy", module="ansible.builtin.copy")
    spec.yaml_lines = "name: Copy\ncopy:\n  src: a\n  dest: b"
    spec.module = "copy"
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = KeyOrderRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result is not None
    assert result.verdict is False


def test_L041_does_not_fire_for_role() -> None:
    """Verify L041 does not fire for role targets."""
    from apme_engine.validators.native.rules._test_helpers import make_role_call, make_role_spec

    role = make_role_call(make_role_spec(name="foo"))
    ctx = make_context(role)
    rule = KeyOrderRule()
    assert not rule.match(ctx)
