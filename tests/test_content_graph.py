"""Tests for ContentGraph, ContentNode, NodeIdentity, and GraphBuilder (ADR-044 Phase 1)."""

from __future__ import annotations

import pytest

from apme_engine.engine.content_graph import (
    ContentGraph,
    ContentNode,
    EdgeType,
    GraphBuilder,
    NodeIdentity,
    NodeScope,
    NodeType,
)


# ---------------------------------------------------------------------------
# NodeIdentity
# ---------------------------------------------------------------------------


class TestNodeIdentity:
    def test_str_representation(self) -> None:
        nid = NodeIdentity(path="site.yml/plays[0]/tasks[1]", node_type=NodeType.TASK)
        assert str(nid) == "site.yml/plays[0]/tasks[1]"

    def test_parent_path(self) -> None:
        nid = NodeIdentity(path="site.yml/plays[0]/tasks[1]", node_type=NodeType.TASK)
        assert nid.parent_path == "site.yml/plays[0]"

    def test_parent_path_root(self) -> None:
        nid = NodeIdentity(path="site.yml", node_type=NodeType.PLAYBOOK)
        assert nid.parent_path is None

    def test_equality(self) -> None:
        a = NodeIdentity(path="site.yml/plays[0]", node_type=NodeType.PLAY)
        b = NodeIdentity(path="site.yml/plays[0]", node_type=NodeType.PLAY)
        assert a == b
        assert hash(a) == hash(b)

    def test_frozen(self) -> None:
        nid = NodeIdentity(path="site.yml", node_type=NodeType.PLAYBOOK)
        with pytest.raises(AttributeError):
            nid.path = "other.yml"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ContentNode
# ---------------------------------------------------------------------------


class TestContentNode:
    def test_node_type_property(self) -> None:
        identity = NodeIdentity(path="site.yml", node_type=NodeType.PLAYBOOK)
        node = ContentNode(identity=identity, file_path="site.yml")
        assert node.node_type == NodeType.PLAYBOOK

    def test_node_id_property(self) -> None:
        identity = NodeIdentity(path="site.yml/plays[0]", node_type=NodeType.PLAY)
        node = ContentNode(identity=identity)
        assert node.node_id == "site.yml/plays[0]"

    def test_default_scope(self) -> None:
        identity = NodeIdentity(path="t.yml", node_type=NodeType.TASK)
        node = ContentNode(identity=identity)
        assert node.scope == NodeScope.OWNED


# ---------------------------------------------------------------------------
# ContentGraph
# ---------------------------------------------------------------------------


def _make_graph() -> ContentGraph:
    """Build a small graph for testing.

    Returns:
        ContentGraph with nodes and edges.
    """
    g = ContentGraph()

    pb = ContentNode(
        identity=NodeIdentity(path="site.yml", node_type=NodeType.PLAYBOOK),
        file_path="site.yml",
        name="site",
        ari_key="playbook playbook:site.yml",
    )
    g.add_node(pb)

    play = ContentNode(
        identity=NodeIdentity(path="site.yml/plays[0]", node_type=NodeType.PLAY),
        file_path="site.yml",
        name="Setup play",
    )
    g.add_node(play)
    g.add_edge("site.yml", "site.yml/plays[0]", EdgeType.CONTAINS, position=0)

    task0 = ContentNode(
        identity=NodeIdentity(path="site.yml/plays[0]/tasks[0]", node_type=NodeType.TASK),
        file_path="site.yml",
        name="Install nginx",
        module="ansible.builtin.package",
        register="pkg_result",
    )
    g.add_node(task0)
    g.add_edge("site.yml/plays[0]", "site.yml/plays[0]/tasks[0]", EdgeType.CONTAINS, position=0)

    task1 = ContentNode(
        identity=NodeIdentity(path="site.yml/plays[0]/tasks[1]", node_type=NodeType.TASK),
        file_path="site.yml",
        name="Verify install",
        notify=["restart nginx"],
    )
    g.add_node(task1)
    g.add_edge("site.yml/plays[0]", "site.yml/plays[0]/tasks[1]", EdgeType.CONTAINS, position=1)

    handler = ContentNode(
        identity=NodeIdentity(path="site.yml/plays[0]/handlers[0]", node_type=NodeType.HANDLER),
        file_path="site.yml",
        name="restart nginx",
    )
    g.add_node(handler)
    g.add_edge("site.yml/plays[0]", "site.yml/plays[0]/handlers[0]", EdgeType.CONTAINS, position=2)
    g.add_edge("site.yml/plays[0]/tasks[1]", "site.yml/plays[0]/handlers[0]", EdgeType.NOTIFY)

    g.add_edge("site.yml/plays[0]/tasks[0]", "site.yml/plays[0]/tasks[1]", EdgeType.DATA_FLOW)

    return g


class TestContentGraph:
    def test_node_count(self) -> None:
        g = _make_graph()
        assert g.node_count() == 5

    def test_get_node(self) -> None:
        g = _make_graph()
        node = g.get_node("site.yml/plays[0]")
        assert node is not None
        assert node.name == "Setup play"

    def test_get_node_missing(self) -> None:
        g = _make_graph()
        assert g.get_node("nonexistent") is None

    def test_get_node_by_ari_key(self) -> None:
        g = _make_graph()
        node = g.get_node_by_ari_key("playbook playbook:site.yml")
        assert node is not None
        assert node.node_id == "site.yml"

    def test_nodes_filtered(self) -> None:
        g = _make_graph()
        tasks = list(g.nodes(NodeType.TASK))
        assert len(tasks) == 2

    def test_edges_from(self) -> None:
        g = _make_graph()
        contains = g.edges_from("site.yml/plays[0]", EdgeType.CONTAINS)
        assert len(contains) == 3

    def test_edges_to(self) -> None:
        g = _make_graph()
        incoming = g.edges_to("site.yml/plays[0]/handlers[0]", EdgeType.NOTIFY)
        assert len(incoming) == 1
        assert incoming[0][0] == "site.yml/plays[0]/tasks[1]"

    def test_ancestors(self) -> None:
        g = _make_graph()
        ancs = g.ancestors("site.yml/plays[0]/tasks[0]")
        assert len(ancs) == 2
        assert ancs[0].node_id == "site.yml/plays[0]"
        assert ancs[1].node_id == "site.yml"

    def test_children(self) -> None:
        g = _make_graph()
        kids = g.children("site.yml/plays[0]")
        assert len(kids) == 3

    def test_descendants(self) -> None:
        g = _make_graph()
        desc = g.descendants("site.yml")
        assert len(desc) == 4

    def test_subgraph(self) -> None:
        g = _make_graph()
        sub = g.subgraph("site.yml/plays[0]")
        assert sub.node_count() == 4

    def test_topological_order(self) -> None:
        g = _make_graph()
        order = g.topological_order()
        assert order[0] == "site.yml"

    def test_is_acyclic(self) -> None:
        g = _make_graph()
        assert g.is_acyclic()

    def test_edge_attributes(self) -> None:
        g = ContentGraph()
        n1 = ContentNode(identity=NodeIdentity(path="a", node_type=NodeType.PLAY))
        n2 = ContentNode(identity=NodeIdentity(path="b", node_type=NodeType.TASK))
        g.add_node(n1)
        g.add_node(n2)
        g.add_edge("a", "b", EdgeType.INCLUDE, conditional=True, dynamic=True, when_expr="x is defined")

        edges = g.edges_from("a", EdgeType.INCLUDE)
        assert len(edges) == 1
        _, attrs = edges[0]
        assert attrs["conditional"] is True
        assert attrs["dynamic"] is True
        assert attrs["when_expr"] == "x is defined"


# ---------------------------------------------------------------------------
# GraphBuilder smoke test (requires ARI model stubs)
# ---------------------------------------------------------------------------


class TestGraphBuilderMinimal:
    """Minimal GraphBuilder tests using hand-crafted definition dicts.

    These don't use real ARI parsing — they verify that GraphBuilder
    correctly processes the definition structures.
    """

    def test_empty_definitions(self) -> None:
        builder = GraphBuilder({}, {})
        graph = builder.build()
        assert graph.node_count() == 0

    def test_definitions_with_empty_mappings(self) -> None:
        defs: dict[str, object] = {"definitions": {}, "mappings": None}
        builder = GraphBuilder(defs, {})
        graph = builder.build()
        assert graph.node_count() == 0
