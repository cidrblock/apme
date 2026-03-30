"""GraphRule L034: variable override ineffective due to low precedence.

Graph-aware port of ``L034_unused_override.py``.  Uses
``VariableProvenanceResolver`` to compare variable precedence across
scopes, replacing the flat ``variable_set`` precedence check with
provenance-aware ordering.
"""

from __future__ import annotations

from dataclasses import dataclass

from apme_engine.engine.content_graph import ContentGraph, NodeType
from apme_engine.engine.models import RuleTag as Tag
from apme_engine.engine.models import Severity, YAMLDict, YAMLValue
from apme_engine.engine.variable_provenance import (
    ProvenanceSource,
    VariableProvenanceResolver,
)
from apme_engine.validators.native.rules.graph_rule_base import GraphRule, GraphRuleResult

_TASK_TYPES = frozenset({NodeType.TASK, NodeType.HANDLER})

_PRECEDENCE_ORDER: dict[ProvenanceSource, int] = {
    ProvenanceSource.ROLE_DEFAULT: 1,
    ProvenanceSource.INVENTORY_FILE: 2,
    ProvenanceSource.VARS_FILE: 3,
    ProvenanceSource.PLAYBOOK: 4,
    ProvenanceSource.PLAY: 5,
    ProvenanceSource.BLOCK: 6,
    ProvenanceSource.ROLE_VAR: 7,
    ProvenanceSource.LOCAL: 8,
    ProvenanceSource.RUNTIME: 9,
    ProvenanceSource.EXTERNAL: 0,
}

_SET_FACT_FQCNS = frozenset(
    {
        "set_fact",
        "ansible.builtin.set_fact",
        "ansible.legacy.set_fact",
    }
)


def _locally_defined_var_names(graph: ContentGraph, node_id: str) -> list[str]:
    """Collect variable names this node defines.

    Args:
        graph: ContentGraph to query.
        node_id: Node to inspect.

    Returns:
        List of variable names defined by this node.
    """
    node = graph.get_node(node_id)
    if node is None:
        return []
    names: list[str] = []
    if node.register:
        names.append(node.register)
    names.extend(k for k in node.set_facts if k != "cacheable")
    return names


def _defines_variables(graph: ContentGraph, node_id: str) -> bool:
    """Return True if the node defines variables via set_fact or register.

    Args:
        graph: ContentGraph to query.
        node_id: Node to inspect.

    Returns:
        True if the node registers output or uses set_fact.
    """
    node = graph.get_node(node_id)
    if node is None:
        return False
    if node.register:
        return True
    if node.resolved_module_name in _SET_FACT_FQCNS or node.module in _SET_FACT_FQCNS:
        return True
    return bool(node.set_facts)


@dataclass
class UnusedOverrideGraphRule(GraphRule):
    """Detect variable overrides that are ineffective due to precedence.

    Uses ``VariableProvenanceResolver`` to find the existing definition
    of a variable and compare its precedence against the local task scope.
    If the task's scope has lower precedence, the override is flagged.

    Attributes:
        rule_id: Rule identifier.
        description: Rule description.
        enabled: Whether the rule is enabled.
        name: Rule name.
        version: Rule version.
        severity: Severity level.
        tags: Rule tags.
    """

    rule_id: str = "L034"
    description: str = "A variable is not successfully re-defined because of low precedence"
    enabled: bool = True
    name: str = "UnusedOverride"
    version: str = "v0.0.2"
    severity: str = Severity.VERY_LOW
    tags: tuple[str, ...] = (Tag.VARIABLE,)

    def match(self, graph: ContentGraph, node_id: str) -> bool:
        """Match tasks that define variables.

        Args:
            graph: The full ContentGraph.
            node_id: ID of the node to check.

        Returns:
            True if the node is a task/handler that defines variables.
        """
        node = graph.get_node(node_id)
        if node is None:
            return False
        if node.node_type not in _TASK_TYPES:
            return False
        return _defines_variables(graph, node_id)

    def process(self, graph: ContentGraph, node_id: str) -> GraphRuleResult | None:
        """Check for ineffective overrides via precedence comparison.

        Resolves all variables in scope and compares the existing
        definition's precedence against the local task's precedence.

        Args:
            graph: The full ContentGraph.
            node_id: ID of the node to evaluate.

        Returns:
            GraphRuleResult with variables detail if overrides are ineffective.
        """
        node = graph.get_node(node_id)
        if node is None:
            return None

        local_names = _locally_defined_var_names(graph, node_id)
        if not local_names:
            return GraphRuleResult(
                verdict=False,
                node_id=node_id,
                file=(node.file_path, node.line_start),
            )

        resolver = VariableProvenanceResolver(graph)
        all_vars = resolver.resolve_variables(node_id)

        local_prec = _PRECEDENCE_ORDER.get(ProvenanceSource.RUNTIME, 9)
        ineffective: list[YAMLValue] = []

        for var_name in local_names:
            prov = all_vars.get(var_name)
            if prov is None or prov.defining_node_id == node_id:
                continue
            existing_prec = _PRECEDENCE_ORDER.get(prov.source, 0)
            if local_prec < existing_prec:
                entry: YAMLDict = {
                    "name": var_name,
                    "prev_precedence": prov.source.value,
                    "new_precedence": "runtime",
                    "prev_defined_at": prov.defining_node_id,
                }
                ineffective.append(entry)

        verdict = len(ineffective) > 0
        detail: YAMLDict = {"variables": ineffective}

        return GraphRuleResult(
            verdict=verdict,
            detail=detail,
            node_id=node_id,
            file=(node.file_path, node.line_start),
        )
