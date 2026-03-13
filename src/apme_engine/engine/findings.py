"""Container for scan results, definitions, and rule evaluation output."""

from __future__ import annotations

import os
from copy import deepcopy
from dataclasses import dataclass, field

import jsonpickle

from .models import YAMLDict, YAMLList
from .utils import (
    lock_file,
    remove_lock_file,
    unlock_file,
)


@dataclass
class Findings:
    """Container for scan results, definitions, and rule evaluation output.

    Attributes:
        metadata: Scan metadata (e.g. target info).
        dependencies: Dependency list.
        root_definitions: Root-level definitions.
        ext_definitions: External definitions.
        extra_requirements: Additional requirements.
        resolve_failures: FQCN resolution failures.
        prm: PRM (policy/risk model) data.
        report: Rule evaluation report including ari_result.
        summary_txt: Human-readable summary.
        scan_time: Timestamp of the scan.
    """

    metadata: YAMLDict = field(default_factory=dict)
    dependencies: YAMLList = field(default_factory=list)

    root_definitions: YAMLDict = field(default_factory=dict)
    ext_definitions: YAMLDict = field(default_factory=dict)
    extra_requirements: YAMLList = field(default_factory=list)
    resolve_failures: YAMLDict = field(default_factory=dict)

    prm: YAMLDict = field(default_factory=dict)
    report: YAMLDict = field(default_factory=dict)

    summary_txt: str = ""
    scan_time: str = ""

    def simple(self) -> YAMLDict:
        """Return a reduced copy of the report with metadata and dependencies.

        Returns:
            Dict with report, metadata, and dependencies keys.
        """
        d = self.report.copy()
        d["metadata"] = self.metadata
        d["dependencies"] = self.dependencies
        return d

    def dump(self, fpath: str = "") -> str:
        """Serialize findings to JSON, optionally writing to a file.

        Omits report and summary_txt when saving to reduce file size.
        Uses file locking when writing to disk.

        Args:
            fpath: Optional path to write the JSON. If empty, only returns string.

        Returns:
            JSON string of the serialized findings.
        """
        f = deepcopy(self)
        # omit report and summary_txt when the findings are saved
        # to reduce unnecessary file write
        f.report = {}
        f.summary_txt = ""
        json_str = jsonpickle.encode(f, make_refs=False)
        if fpath:
            lock = lock_file(fpath)
            try:
                with open(fpath, "w") as file:
                    file.write(json_str)
            finally:
                unlock_file(lock)
                remove_lock_file(lock)
        return str(json_str)

    def save_rule_result(self, fpath: str = "") -> str:
        """Save only the ari_result from report as JSON to a file.

        Creates parent directories if needed. Uses standard JSON (not jsonpickle).

        Args:
            fpath: Path to write the rule result JSON. If empty, only returns string.

        Returns:
            JSON string of the ari_result.
        """
        json_str: str = jsonpickle.encode(self.report.get("ari_result", {}), make_refs=False, unpicklable=False)
        if fpath:
            rule_result_dir = os.path.dirname(fpath)
            if not os.path.exists(rule_result_dir):
                os.makedirs(rule_result_dir, exist_ok=True)
            with open(fpath, "w") as file:
                file.write(json_str)
        return json_str

    @staticmethod
    def load(fpath: str = "", json_str: str = "") -> Findings:
        """Load Findings from a file or JSON string.

        Args:
            fpath: Path to load from. If provided, json_str is ignored.
            json_str: JSON string to decode. Used when fpath is empty.

        Returns:
            Deserialized Findings instance.
        """
        if fpath:
            with open(fpath) as file:
                json_str = file.read()
        findings: Findings = jsonpickle.decode(json_str)
        return findings
