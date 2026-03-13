"""AWX-derived utilities for playbook detection and directory filtering."""

import codecs
import os
import re

valid_playbook_re = re.compile(r"^\s*?-?\s*?(?:hosts|include|import_playbook):\s*?.*?$")


# this method is based on awx code
# awx/main/utils/ansible.py#L42-L64 in ansible/awx
def could_be_playbook(fpath: str) -> bool:
    """Check if a file might be an Ansible playbook based on extension and content.

    Uses regex to detect hosts/include/import_playbook at top level or vault header,
    allowing files with invalid YAML to be identified as potential playbooks.

    Args:
        fpath: Path to the file to check.

    Returns:
        True if the file has .yml/.yaml extension and appears playbook-like.
    """
    basename, ext = os.path.splitext(fpath)
    if ext not in [".yml", ".yaml"]:
        return False
    # Filter files that do not have either hosts or top-level
    # includes. Use regex to allow files with invalid YAML to
    # show up.
    matched = False
    try:
        with codecs.open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            for n, line in enumerate(f):
                if valid_playbook_re.match(line) or n == 0 and line.startswith("$ANSIBLE_VAULT;"):
                    matched = True
                    break
    except OSError:
        return False
    return matched


# this method is based on awx code
# awx/main/models/projects.py#L206-L217 in ansible/awx
def search_playbooks(root_path: str) -> list[str]:
    """Recursively find all files that could be Ansible playbooks under a root path.

    Walks the directory tree, skipping directories per skip_directory, and returns
    paths to files that pass could_be_playbook.

    Args:
        root_path: Root directory to search.

    Returns:
        Sorted list of playbook file paths (case-insensitive sort).
    """
    results = []
    if root_path and os.path.exists(root_path):
        for dirpath, _dirnames, filenames in os.walk(root_path, followlinks=False):
            if skip_directory(dirpath):
                continue
            for filename in filenames:
                fpath = os.path.join(dirpath, filename)
                if could_be_playbook(fpath):
                    results.append(fpath)
    return sorted(results, key=lambda x: x.lower())


# this method is based on awx code
# awx/main/utils/ansible.py#L24-L39 in ansible/awx
def skip_directory(relative_directory_path: str) -> bool:
    """Determine if a directory should be excluded from playbook search.

    Skips roles, tasks, molecule, tests/integration, dot-prefixed paths,
    group_vars, and host_vars directories.

    Args:
        relative_directory_path: Path of the directory to check.

    Returns:
        True if the directory should be skipped.
    """
    path_elements = relative_directory_path.split(os.sep)
    # Exclude files in a roles subdirectory.
    if "roles" in path_elements:
        return True
    # Filter files in a tasks subdirectory.
    if "tasks" in path_elements:
        return True
    # Filter files in a molecule subdirectory.
    if "molecule" in path_elements:
        return True
    # Filter files in a tests/integration subdirectory.
    if "tests" in path_elements and "integration" in path_elements:
        return True
    for element in path_elements:
        # Do not include dot files or dirs
        if element.startswith("."):
            return True
    # Exclude anything inside of group or host vars directories
    return bool("group_vars" in path_elements or "host_vars" in path_elements)
