"""Tests for native rule R114."""

from apme_engine.validators.native.rules._test_helpers import make_context, make_task_call, make_task_spec
from apme_engine.validators.native.rules.R114_file_change import FileChangeRule


def test_R114_does_not_fire_when_no_annotation() -> None:
    """Verify R114 does not fire when no annotation."""
    spec = make_task_spec(module="copy", resolved_name="ansible.builtin.copy")
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = FileChangeRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result is not None
    assert result.verdict is False
