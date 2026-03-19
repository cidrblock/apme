"""M001/M003: Rewrite short module names to FQCN.

M001 violations carry ``resolved_fqcn`` from ansible-core's plugin loader.
Falls back to a static builtin map when resolved_fqcn is not available.
After resolving, follows known redirects from ``ansible_builtin_runtime.yml``
so the final FQCN is the canonical target.
"""

from __future__ import annotations

from apme_engine.engine.models import ViolationDict
from apme_engine.remediation.structured import StructuredFile
from apme_engine.remediation.transforms._helpers import (
    get_module_key,
    rename_key,
    violation_line_to_int,
)

_BUILTIN_FQCN: dict[str, str] = {
    "debug": "ansible.builtin.debug",
    "command": "ansible.builtin.command",
    "shell": "ansible.builtin.shell",
    "raw": "ansible.builtin.raw",
    "script": "ansible.builtin.script",
    "copy": "ansible.builtin.copy",
    "file": "ansible.builtin.file",
    "template": "ansible.builtin.template",
    "yum": "ansible.builtin.yum",
    "apt": "ansible.builtin.apt",
    "pip": "ansible.builtin.pip",
    "service": "ansible.builtin.service",
    "systemd": "ansible.builtin.systemd",
    "user": "ansible.builtin.user",
    "group": "ansible.builtin.group",
    "cron": "ansible.builtin.cron",
    "git": "ansible.builtin.git",
    "get_url": "ansible.builtin.get_url",
    "uri": "ansible.builtin.uri",
    "unarchive": "ansible.builtin.unarchive",
    "lineinfile": "ansible.builtin.lineinfile",
    "replace": "ansible.builtin.replace",
    "blockinfile": "ansible.builtin.blockinfile",
    "stat": "ansible.builtin.stat",
    "find": "ansible.builtin.find",
    "fetch": "ansible.builtin.fetch",
    "synchronize": "ansible.posix.synchronize",
    "authorized_key": "ansible.posix.authorized_key",
    "package": "ansible.builtin.package",
    "dnf": "ansible.builtin.dnf",
    "setup": "ansible.builtin.setup",
    "ping": "ansible.builtin.ping",
    "assert": "ansible.builtin.assert",
    "fail": "ansible.builtin.fail",
    "set_fact": "ansible.builtin.set_fact",
    "pause": "ansible.builtin.pause",
    "wait_for": "ansible.builtin.wait_for",
    "wait_for_connection": "ansible.builtin.wait_for_connection",
    "include_tasks": "ansible.builtin.include_tasks",
    "import_tasks": "ansible.builtin.import_tasks",
    "include_role": "ansible.builtin.include_role",
    "import_role": "ansible.builtin.import_role",
    "include_vars": "ansible.builtin.include_vars",
    "add_host": "ansible.builtin.add_host",
    "group_by": "ansible.builtin.group_by",
    "hostname": "ansible.builtin.hostname",
    "iptables": "ansible.builtin.iptables",
    "known_hosts": "ansible.builtin.known_hosts",
    "mount": "ansible.builtin.mount",
    "reboot": "ansible.builtin.reboot",
    "tempfile": "ansible.builtin.tempfile",
    "meta": "ansible.builtin.meta",
    "async_status": "ansible.builtin.async_status",
    "gather_facts": "ansible.builtin.gather_facts",
    "package_facts": "ansible.builtin.package_facts",
    "slurp": "ansible.builtin.slurp",
}

_BUILTIN_REDIRECTS: dict[str, str] = {}


def _follow_redirects(fqcn: str) -> str:
    """Follow builtin redirect chains to the canonical module FQCN.

    Args:
        fqcn: Resolved FQCN that may have a redirect entry.

    Returns:
        Canonical FQCN after following all redirects.
    """
    seen: set[str] = set()
    while fqcn in _BUILTIN_REDIRECTS and fqcn not in seen:
        seen.add(fqcn)
        fqcn = _BUILTIN_REDIRECTS[fqcn]
    return fqcn


def _resolve_fqcn(violation: ViolationDict, current_key: str) -> str | None:
    """Get the target FQCN from the violation or fall back to the static map.

    Checks ``resolved_fqcn`` (from Ansible validator M001) and ``fqcn``
    (from native validator L026).  After resolution, follows known redirects
    so the returned FQCN is the canonical target.

    Args:
        violation: Violation dict (may have resolved_fqcn or fqcn).
        current_key: Current short module name.

    Returns:
        FQCN string, or None if not resolvable.
    """
    for field in ("resolved_fqcn", "fqcn"):
        fqcn = violation.get(field)
        if fqcn is not None and str(fqcn) != current_key and "." in str(fqcn):
            return _follow_redirects(str(fqcn))
    base = _BUILTIN_FQCN.get(current_key)
    if base is not None:
        return _follow_redirects(base)
    return None


def fix_fqcn(sf: StructuredFile, violation: ViolationDict) -> bool:
    """Rename a short module name to its FQCN.

    Args:
        sf: Parsed YAML file to modify in-place.
        violation: Violation dict with line and optional resolved_fqcn.

    Returns:
        True if a change was applied.
    """
    task = sf.find_task(violation_line_to_int(violation), violation)
    if task is None:
        return False

    module_key = get_module_key(task)
    if module_key is None:
        return False

    fqcn = _resolve_fqcn(violation, module_key)
    if fqcn is None or fqcn == module_key:
        return False

    rename_key(task, module_key, fqcn)
    return True
