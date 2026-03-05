"""Pytest configuration and shared fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def repo_root():
    """Project root (ansible-forward)."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def opa_bundle_path(repo_root):
    """Path to OPA bundle directory (built-in validator bundle)."""
    return repo_root / "src" / "apme_engine" / "validators" / "opa" / "bundle"


@pytest.fixture
def sample_hierarchy_payload():
    """Minimal valid OPA input (hierarchy payload)."""
    return {
        "scan_id": "test-scan-1",
        "hierarchy": [
            {
                "root_key": "playbook :/examples/pb.yml",
                "root_type": "playbook",
                "root_path": "/examples/pb.yml",
                "nodes": [
                    {
                        "type": "playcall",
                        "key": "playcall#x",
                        "file": "/examples/pb.yml",
                        "line": [1, 3],
                        "defined_in": "/examples/pb.yml",
                        "name": "",
                        "options": {},
                    },
                    {
                        "type": "taskcall",
                        "key": "taskcall#y",
                        "file": "/examples/pb.yml",
                        "line": [5, 7],
                        "defined_in": "/examples/pb.yml",
                        "module": "ansible.builtin.shell",
                        "annotations": [],
                        "name": "",
                        "options": {},
                        "module_options": {},
                    },
                ],
            },
        ],
        "metadata": {"type": "playbook", "name": "/examples/pb.yml", "collection_name": "", "role_name": ""},
    }


@pytest.fixture
def opa_eval_result_with_violations():
    """OPA eval JSON output format with a list of violations."""
    return {
        "result": [
            {
                "expressions": [
                    {
                        "value": [
                            {"rule_id": "task-name", "level": "warning", "message": "Task using shell module should have a name", "file": "/examples/pb.yml", "line": 5, "path": "taskcall#y"},
                        ]
                    }
                ]
            }
        ]
    }


@pytest.fixture
def opa_eval_result_empty():
    """OPA eval JSON with empty violations."""
    return {"result": [{"expressions": [{"value": []}]}]}
