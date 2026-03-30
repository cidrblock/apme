"""Test fixture filter plugin — exercises invokes edges for filters.

GraphBuilder should detect an ``invokes`` edge when a task uses
``testorg.graph_patterns.format_utils`` filter.
"""

from __future__ import annotations


class FilterModule:
    """Custom filters for graph-patterns test collection."""

    def filters(self) -> dict:
        return {
            "to_deploy_label": self.to_deploy_label,
        }

    @staticmethod
    def to_deploy_label(name: str, version: str) -> str:
        """Format a deployment label."""
        return f"{name}:{version}"
