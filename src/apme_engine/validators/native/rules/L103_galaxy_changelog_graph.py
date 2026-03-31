"""GraphRule L103: collection should have a CHANGELOG file."""

from __future__ import annotations

import os
from dataclasses import dataclass

from apme_engine.engine.content_graph import ContentGraph, NodeType
from apme_engine.engine.models import RuleTag as Tag
from apme_engine.engine.models import Severity, YAMLDict
from apme_engine.validators.native.rules.graph_rule_base import GraphRule, GraphRuleResult


def _has_changelog(files: list[str]) -> bool:
    """Return True if any listed path has a CHANGELOG* basename (case-insensitive).

    Args:
        files: Relative paths within the collection root.

    Returns:
        True when a basename starts with ``changelog`` (case-insensitive).
    """
    for raw in files:
        base = os.path.basename(raw.replace("\\", "/"))
        if base.lower().startswith("changelog"):
            return True
    return False


@dataclass
class GalaxyChangelogGraphRule(GraphRule):
    """Flag collections missing a CHANGELOG file.

    Attributes:
        rule_id: Rule identifier.
        description: Rule description.
        enabled: Whether the rule is enabled.
        name: Rule name.
        version: Rule version.
        severity: Severity level.
        tags: Rule tags.
    """

    rule_id: str = "L103"
    description: str = "Collection should have a CHANGELOG file"
    enabled: bool = True
    name: str = "GalaxyChangelog"
    version: str = "v0.0.1"
    severity: str = Severity.LOW
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
        """Report a violation when no CHANGELOG* file is present.

        Args:
            graph: The full ContentGraph.
            node_id: ID of the node to evaluate.

        Returns:
            ``GraphRuleResult`` with ``verdict`` True when no CHANGELOG is found,
            ``verdict`` False when one is found, or None if the node is not applicable.
        """
        node = graph.get_node(node_id)
        if node is None or node.node_type != NodeType.COLLECTION or not node.collection_files:
            return None
        files = list(node.collection_files)
        if _has_changelog(files):
            return GraphRuleResult(
                verdict=False,
                node_id=node_id,
                file=(node.file_path, node.line_start),
            )
        detail: YAMLDict = {
            "issue": "No CHANGELOG* file found in collection file listing",
            "expected_patterns": ["CHANGELOG*"],
        }
        return GraphRuleResult(
            verdict=True,
            detail=detail,
            node_id=node_id,
            file=(node.file_path, node.line_start),
        )
