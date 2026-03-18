"""Finding partition — routes violations to Tier 1, 2, or 3."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apme_engine.engine.models import ViolationDict
from apme_engine.engine.models import RemediationClass
from apme_engine.remediation.registry import TransformRegistry


def normalize_rule_id(rule_id: str) -> str:
    """Strip validator-specific prefixes from a rule ID for registry lookup.

    Args:
        rule_id: Raw rule ID, possibly prefixed (e.g. ``native:L021``).

    Returns:
        Bare rule ID suitable for registry lookup (e.g. ``L021``).
    """
    if rule_id.startswith("native:"):
        rule_id = rule_id[len("native:") :]
    return rule_id


def is_finding_resolvable(violation: ViolationDict, registry: TransformRegistry) -> bool:
    """Return True if the violation has a registered deterministic transform (Tier 1).

    Args:
        violation: Violation dict with rule_id.
        registry: Transform registry to check for rule.

    Returns:
        True if rule_id has a registered transform.
    """
    return normalize_rule_id(str(violation.get("rule_id", ""))) in registry


def partition_violations(
    violations: list[ViolationDict],
    registry: TransformRegistry,
) -> tuple[list[ViolationDict], list[ViolationDict], list[ViolationDict]]:
    """Split violations into (tier1_fixable, tier2_ai, tier3_manual).

    Tier 1: deterministic transform exists in registry.
    Tier 2: no transform, but ai_proposable (default True if not set).
    Tier 3: no transform, ai_proposable explicitly False.

    Args:
        violations: List of violation dicts.
        registry: Transform registry for Tier 1 lookup.

    Returns:
        Tuple of (tier1_fixable, tier2_ai, tier3_manual).
    """
    tier1: list[ViolationDict] = []
    tier2: list[ViolationDict] = []
    tier3: list[ViolationDict] = []

    for v in violations:
        if is_finding_resolvable(v, registry):
            tier1.append(v)
        elif v.get("ai_proposable", True):
            tier2.append(v)
        else:
            tier3.append(v)

    return tier1, tier2, tier3


def classify_violation(violation: ViolationDict, registry: TransformRegistry) -> str:
    """Return remediation class: auto-fixable, ai-candidate, or manual-review.

    Args:
        violation: Violation dict with rule_id.
        registry: Transform registry to check for deterministic transforms.

    Returns:
        One of RemediationClass.AUTO_FIXABLE, AI_CANDIDATE, or MANUAL_REVIEW.
    """
    if is_finding_resolvable(violation, registry):
        return RemediationClass.AUTO_FIXABLE
    elif violation.get("ai_proposable", True):
        return RemediationClass.AI_CANDIDATE
    else:
        return RemediationClass.MANUAL_REVIEW


def add_classification_to_violations(
    violations: list[ViolationDict],
    registry: TransformRegistry,
) -> list[ViolationDict]:
    """Add remediation_class field to each violation.

    Args:
        violations: List of violation dicts.
        registry: Transform registry for Tier 1 lookup.

    Returns:
        Same list with remediation_class field added to each violation.
    """
    for v in violations:
        v["remediation_class"] = classify_violation(v, registry)
    return violations


def count_by_remediation_class(violations: list[ViolationDict]) -> dict[str, int]:
    """Count violations by remediation class.

    Args:
        violations: List of violations with remediation_class field.

    Returns:
        Dict with counts keyed by remediation class.
    """
    counts = {
        RemediationClass.AUTO_FIXABLE: 0,
        RemediationClass.AI_CANDIDATE: 0,
        RemediationClass.MANUAL_REVIEW: 0,
    }
    for v in violations:
        rc_raw = v.get("remediation_class", RemediationClass.AI_CANDIDATE)
        rc = str(rc_raw) if rc_raw else RemediationClass.AI_CANDIDATE
        if rc in counts:
            counts[rc] += 1
        else:
            counts[RemediationClass.AI_CANDIDATE] += 1
    return counts
