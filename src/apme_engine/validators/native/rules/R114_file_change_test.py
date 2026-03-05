# Colocated tests for R114 (FileChangeRule). Rule uses annotations; test no fire without annotation.

from apme_engine.validators.native.rules._test_helpers import make_task_spec, make_task_call, make_context
from apme_engine.validators.native.rules.R114_file_change import FileChangeRule


def test_R114_does_not_fire_when_no_annotation():
    spec = make_task_spec(module="copy", resolved_name="ansible.builtin.copy")
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = FileChangeRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result.verdict is False
