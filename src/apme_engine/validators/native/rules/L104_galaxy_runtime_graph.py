"""GraphRule L104: collection should have meta/runtime.yml."""

from __future__ import annotations

import os
from dataclasses import dataclass

from apme_engine.engine.content_graph import ContentGraph, NodeType
from apme_engine.engine.models import RuleTag as Tag
from apme_engine.engine.models import Severity, YAMLDict
from apme_engine.validators.native.rules.graph_rule_base import GraphRule, GraphRuleResult


def _has_meta_runtime(files: list[str]) -> bool:
    """Return True if ``meta/runtime.yml`` or ``meta/runtime.yaml`` is listed.

    Matches normalized relative paths and ``meta``/basename combinations
    (case-insensitive).

    Args:
        files: Relative paths within the collection root.

    Returns:
        True when a runtime file path is recognized.
    """
    for raw in files:
        norm = raw.replace("\\", "/")
        lower = norm.lower()
        if lower == "meta/runtime.yml" or lower == "meta/runtime.yaml":
            return True
        if lower.endswith("/meta/runtime.yml") or lower.endswith("/meta/runtime.yaml"):
            return True
        base = os.path.basename(norm)
        if base.lower() in ("runtime.yml", "runtime.yaml"):
            parent = os.path.dirname(norm)
            if os.path.basename(parent).lower() == "meta":
                return True
    return False


@dataclass
class GalaxyRuntimeGraphRule(GraphRule):
    """Flag collections missing ``meta/runtime.yml`` (or ``.yaml``).

    Attributes:
        rule_id: Rule identifier.
        description: Rule description.
        enabled: Whether the rule is enabled.
        name: Rule name.
        version: Rule version.
        severity: Severity level.
        tags: Rule tags.
    """

    rule_id: str = "L104"
    description: str = "Collection should have meta/runtime.yml"
    enabled: bool = True
    name: str = "GalaxyRuntime"
    version: str = "v0.0.1"
    severity: str = Severity.MEDIUM
    tags: tuple[str, ...] = (Tag.QUALITY,)

    def match(self, graph: ContentGraph, node_id: str) -> bool:
        """Match COLLECTION nodes that carry a non-empty file listing.

        Args:
            graph: The full ContentGraph.
            node_id: ID of the node to check.

        Returns:
            True when the node is a COLLECTION with ``collection_files`` populated.
        """
        node = graph.get_node(node_id)
        if node is None or node.node_type != NodeType.COLLECTION:
            return False
        return bool(node.collection_files)

    def process(self, graph: ContentGraph, node_id: str) -> GraphRuleResult | None:
        """Report a violation when ``meta/runtime.yml`` is not in the file listing.

        Args:
            graph: The full ContentGraph.
            node_id: ID of the node to evaluate.

        Returns:
            ``GraphRuleResult`` with ``verdict`` True when runtime file is missing,
            ``verdict`` False when present, or None if the node is not applicable.
        """
        node = graph.get_node(node_id)
        if node is None or node.node_type != NodeType.COLLECTION or not node.collection_files:
            return None
        files = list(node.collection_files)
        if _has_meta_runtime(files):
            return GraphRuleResult(
                verdict=False,
                node_id=node_id,
                file=(node.file_path, node.line_start),
            )
        detail: YAMLDict = {
            "issue": "meta/runtime.yml (or meta/runtime.yaml) not found in collection file listing",
            "expected_paths": ["meta/runtime.yml", "meta/runtime.yaml"],
        }
        return GraphRuleResult(
            verdict=True,
            detail=detail,
            node_id=node_id,
            file=(node.file_path, node.line_start),
        )
