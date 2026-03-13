"""Tests for native rule R106."""

from apme_engine.validators.native.rules._test_helpers import make_context, make_task_call, make_task_spec
from apme_engine.validators.native.rules.R106_inbound_transfer import InboundTransferRule


def test_R106_does_not_fire_when_no_annotation() -> None:
    """Verify R106 does not fire when no annotation."""
    spec = make_task_spec(module="get_url", resolved_name="ansible.builtin.get_url")
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = InboundTransferRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result is not None
    assert result.verdict is False
