"""ScanContext and Validator protocol for all validation backends."""

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass
class ScanContext:
    """What validators receive. Extensible so different backends get what they need."""

    hierarchy_payload: dict
    scandata: Any = None
    root_dir: str = ""


@runtime_checkable
class Validator(Protocol):
    """Any backend that can produce violations from a scan."""

    def run(self, context: ScanContext) -> list[dict[str, Any]]:
        """Return list of violation dicts (rule_id, level, message, file, line, path)."""
        ...
