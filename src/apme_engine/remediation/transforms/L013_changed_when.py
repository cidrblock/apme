"""L013: Add changed_when: false to command/shell/raw tasks missing it."""

from __future__ import annotations

from apme_engine.engine.models import ViolationDict
from apme_engine.engine.yaml_utils import FormattedYAML
from apme_engine.remediation.registry import TransformResult
from apme_engine.remediation.transforms._helpers import find_task_at_line, get_module_key, violation_line_to_int

_CMD_MODULES = frozenset(
    {
        "ansible.builtin.command",
        "ansible.builtin.shell",
        "ansible.builtin.raw",
        "ansible.legacy.command",
        "ansible.legacy.shell",
        "ansible.legacy.raw",
        "command",
        "shell",
        "raw",
    }
)


def fix_changed_when(content: str, violation: ViolationDict) -> TransformResult:
    """Add ``changed_when: false`` to command/shell/raw tasks.

    This is a conservative default — the task may actually change state,
    but the user should audit and adjust the condition.

    Args:
        content: YAML file content.
        violation: Violation dict with line.

    Returns:
        TransformResult with modified content if applied.
    """
    yaml = FormattedYAML(typ="rt", pure=True, version=(1, 1))

    try:
        data = yaml.load(content)
    except Exception:
        return TransformResult(content=content, applied=False)

    line = violation_line_to_int(violation)
    task = find_task_at_line(data, line)
    if task is None:
        return TransformResult(content=content, applied=False)

    module_key = get_module_key(task)
    if module_key is None or module_key not in _CMD_MODULES:
        return TransformResult(content=content, applied=False)

    if "changed_when" in task:
        return TransformResult(content=content, applied=False)

    module_args = task.get(module_key)
    if isinstance(module_args, dict) and ("creates" in module_args or "removes" in module_args):
        return TransformResult(content=content, applied=False)

    task["changed_when"] = False
    return TransformResult(content=yaml.dumps(data), applied=True)
