"""Tests for apme_engine.engine.scanner (AnsibleProjectLoader + SingleScan)."""

from __future__ import annotations

from apme_engine.engine.models import (
    LoadType,
)
from apme_engine.engine.scanner import SingleScan


class TestSingleScanInit:
    """Tests for SingleScan initialization."""

    def test_collection_type_sets_paths(self) -> None:
        """Collection type sets type and name."""
        ss = SingleScan(
            type=LoadType.COLLECTION,
            name="ns.col",
            root_dir="/tmp/apme-data",
        )
        assert ss.type == LoadType.COLLECTION
        assert ss.name == "ns.col"

    def test_role_type_sets_paths(self) -> None:
        """Role type sets type and name."""
        ss = SingleScan(
            type=LoadType.ROLE,
            name="myrole",
            root_dir="/tmp/apme-data",
        )
        assert ss.type == LoadType.ROLE

    def test_project_type(self) -> None:
        """Project type sets type and name."""
        ss = SingleScan(
            type=LoadType.PROJECT,
            name="https://github.com/org/repo",
            root_dir="/tmp/apme-data",
        )
        assert ss.type == LoadType.PROJECT

    def test_playbook_type_with_yaml(self) -> None:
        """Playbook type with yaml sets playbook_yaml and target."""
        ss = SingleScan(
            type=LoadType.PLAYBOOK,
            name="myplaybook",
            playbook_yaml="---\n- hosts: all\n  tasks: []\n",
            playbook_only=True,
            root_dir="/tmp/apme-data",
        )
        assert ss.type == LoadType.PLAYBOOK
        assert ss.playbook_yaml != ""
        assert ss.target_playbook_name == "myplaybook"

    def test_taskfile_type_with_yaml(self) -> None:
        """Taskfile type with yaml sets taskfile_yaml and target."""
        ss = SingleScan(
            type=LoadType.TASKFILE,
            name="mytaskfile",
            taskfile_yaml="---\n- name: Test\n  ansible.builtin.debug:\n    msg: hello\n",
            taskfile_only=True,
            root_dir="/tmp/apme-data",
        )
        assert ss.type == LoadType.TASKFILE
        assert ss.target_taskfile_name == "mytaskfile"

    def test_default_fields(self) -> None:
        """SingleScan has empty findings by default."""
        ss = SingleScan(
            type=LoadType.COLLECTION,
            name="test",
            root_dir="/tmp/data",
        )
        assert ss.findings is None
        assert ss.hierarchy_payload == {}
