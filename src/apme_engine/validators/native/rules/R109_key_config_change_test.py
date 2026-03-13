"""Tests for native rule R109."""

from apme_engine.validators.native.rules._test_helpers import make_context, make_task_call, make_task_spec
from apme_engine.validators.native.rules.R109_key_config_change import KeyConfigChangeRule


def test_R109_does_not_fire_when_no_annotation() -> None:
    """Verify R109 does not fire when no annotation."""
    spec = make_task_spec(module="lineinfile", resolved_name="ansible.builtin.lineinfile")
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = KeyConfigChangeRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result is not None
    assert result.verdict is False
