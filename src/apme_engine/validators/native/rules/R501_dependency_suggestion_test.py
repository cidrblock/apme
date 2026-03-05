# Colocated tests for R501 (DependencySuggestionRule).

from apme_engine.validators.native.rules._test_helpers import (
    make_task_spec,
    make_task_call,
    make_context,
)
from apme_engine.validators.native.rules.R501_dependency_suggestion import DependencySuggestionRule


def test_R501_fires_when_possible_candidates():
    spec = make_task_spec(
        module="ansible.builtin.some_unknown",
        possible_candidates=[
            ("ansible.builtin.copy", {"type": "galaxy", "name": "ansible.builtin", "version": "2.0.0"}),
        ],
    )
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = DependencySuggestionRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result.verdict is True
    assert result.rule.rule_id == "R501"
    assert result.detail.get("fqcn") == "ansible.builtin.copy"
    assert "suggestion" in result.detail


def test_R501_does_not_fire_when_no_possible_candidates():
    spec = make_task_spec(module="ansible.builtin.copy", resolved_name="ansible.builtin.copy")
    task = make_task_call(spec)
    ctx = make_context(task)
    rule = DependencySuggestionRule()
    assert rule.match(ctx)
    result = rule.process(ctx)
    assert result.verdict is False
