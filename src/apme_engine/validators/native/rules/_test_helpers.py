# Test helpers for colocated native rule tests. Build minimal Python context/task objects.

from apme_engine.engine.models import (
    Task,
    TaskCall,
    Role,
    RoleCall,
    AnsibleRunContext,
    RunTargetType,
    ExecutableType,
)


def make_task_spec(
    name=None,
    module="",
    executable="",
    executable_type=ExecutableType.MODULE_TYPE,
    resolved_name="",
    options=None,
    module_options=None,
    defined_in="tasks/main.yml",
    line_num_in_file=None,
    key=None,
    possible_candidates=None,
):
    """Build a minimal Task spec for rule tests."""
    # Key must be "type rest" (space-separated) for set_call_object_key.
    if key is None:
        key = "task task:{}:[0]".format(defined_in.replace("/", ":"))
    spec = Task(
        name=name or "",
        module=module or executable or "",
        executable=executable or module or "",
        executable_type=executable_type,
        resolved_name=resolved_name or module or executable or "",
        options=options or {},
        module_options=module_options or {},
        defined_in=defined_in,
        line_num_in_file=line_num_in_file or [1, 2],
        key=key,
    )
    if possible_candidates is not None:
        spec.possible_candidates = possible_candidates
    return spec


def make_task_call(spec):
    """Build a TaskCall from a Task spec."""
    return TaskCall.from_spec(spec, None, 0)


def make_role_spec(name="", defined_in="roles/foo/meta/main.yml", key=None, metadata=None):
    """Build a minimal Role spec for rule tests."""
    # Key must be "type rest" (space-separated) for set_call_object_key.
    if key is None:
        key = "role role:{}".format(name or "test")
    return Role(
        name=name,
        defined_in=defined_in,
        key=key,
        metadata=metadata if metadata is not None else {},
    )


def make_role_call(spec):
    """Build a RoleCall from a Role spec."""
    return RoleCall.from_spec(spec, None, 0)


def make_context(current, sequence=None):
    """Build an AnsibleRunContext with current set (task or role). Optionally set sequence for is_begin/is_end."""
    ctx = AnsibleRunContext(root_key="playbook.yml")
    ctx.current = current
    if sequence is not None:
        ctx.sequence.items = list(sequence)
    return ctx
