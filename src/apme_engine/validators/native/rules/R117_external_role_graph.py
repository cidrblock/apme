"""GraphRule R117: detect external role usage.

Graph-aware port of ``R117_external_role.py``.  Matches ``ROLE`` nodes
and checks for ``galaxy_info`` in the node's options (metadata).
The old ``ctx.is_begin(role)`` guard is replaced by checking whether the
role node has a parent play — a root-level role being scanned directly
(rather than included from a playbook) is not flagged.
"""

from __future__ import annotations

from dataclasses import dataclass

from apme_engine.engine.content_graph import ContentGraph, NodeType
from apme_engine.engine.models import RuleScope, Severity, YAMLDict
from apme_engine.engine.models import RuleTag as Tag
from apme_engine.validators.native.rules.graph_rule_base import GraphRule, GraphRuleResult


def _has_galaxy_info(graph: ContentGraph, node_id: str) -> bool:
    """Check whether a role node carries ``galaxy_info`` metadata.

    Galaxy-style roles have a ``meta/main.yml`` with ``galaxy_info``.
    The graph builder stores this under ``node.options`` or as an attribute.

    Args:
        graph: ContentGraph to query.
        node_id: Role node to inspect.

    Returns:
        True if ``galaxy_info`` is present.
    """
    node = graph.get_node(node_id)
    if node is None:
        return False
    opts = node.options
    if isinstance(opts, dict) and opts.get("galaxy_info"):
        return True
    return bool(isinstance(node.module_options, dict) and node.module_options.get("galaxy_info"))


def _has_parent_play(graph: ContentGraph, node_id: str) -> bool:
    """Return True if the role has a play ancestor.

    A role being scanned as the root of a standalone role project
    has no play parent and should not be flagged.

    Args:
        graph: ContentGraph to query.
        node_id: Node to inspect.

    Returns:
        True if an ancestor play exists.
    """
    return any(anc.node_type == NodeType.PLAY for anc in graph.ancestors(node_id))


@dataclass
class ExternalRoleGraphRule(GraphRule):
    """Detect external role usage via graph metadata.

    Matches ``ROLE`` nodes with ``galaxy_info`` in their metadata.
    Replaces the ``ctx.is_begin`` + ``RoleCall`` + ``spec.metadata``
    pattern with a graph-native check.

    Attributes:
        rule_id: Rule identifier.
        description: Rule description.
        enabled: Whether the rule is enabled.
        name: Rule name.
        version: Rule version.
        severity: Severity level.
        tags: Rule tags.
        scope: Structural scope.
    """

    rule_id: str = "R117"
    description: str = "An external role is used"
    enabled: bool = True
    name: str = "ExternalRole"
    version: str = "v0.0.2"
    severity: str = Severity.VERY_LOW
    tags: tuple[str, ...] = (Tag.DEPENDENCY,)
    scope: str = RuleScope.ROLE

    def match(self, graph: ContentGraph, node_id: str) -> bool:
        """Match role nodes with galaxy_info that have a play parent.

        Args:
            graph: The full ContentGraph.
            node_id: ID of the node to check.

        Returns:
            True if the node is a role with galaxy metadata under a play.
        """
        node = graph.get_node(node_id)
        if node is None:
            return False
        if node.node_type != NodeType.ROLE:
            return False
        if not _has_parent_play(graph, node_id):
            return False
        return _has_galaxy_info(graph, node_id)

    def process(self, graph: ContentGraph, node_id: str) -> GraphRuleResult | None:
        """Report external role usage.

        Args:
            graph: The full ContentGraph.
            node_id: ID of the node to evaluate.

        Returns:
            GraphRuleResult indicating external role found.
        """
        node = graph.get_node(node_id)
        if node is None:
            return None

        detail: YAMLDict = {}
        if node.role_fqcn:
            detail["role_fqcn"] = node.role_fqcn
        if node.name:
            detail["role_name"] = node.name

        return GraphRuleResult(
            verdict=True,
            detail=detail if detail else None,
            node_id=node_id,
            file=(node.file_path, node.line_start),
        )
