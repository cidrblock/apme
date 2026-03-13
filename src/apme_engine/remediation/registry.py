"""Transform registry — maps rule IDs to deterministic fix functions."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import NamedTuple

from apme_engine.engine.models import ViolationDict


class TransformResult(NamedTuple):
    """Result of applying a transform to file content.

    Attributes:
        content: File content (possibly modified).
        applied: True if the transform made a change.
    """

    content: str
    applied: bool


TransformFn = Callable[[str, ViolationDict], TransformResult]


class TransformRegistry:
    """Maps rule IDs to deterministic fix functions.

    A transform receives (file_content, violation_dict) and returns a
    TransformResult with the (possibly modified) content and a flag
    indicating whether a change was made.
    """

    def __init__(self) -> None:
        """Initialize an empty transform registry."""
        self._transforms: dict[str, TransformFn] = {}

    def register(self, rule_id: str, fn: TransformFn) -> None:
        """Register a transform function for a rule ID.

        Args:
            rule_id: Rule identifier (e.g. L007, M001).
            fn: Transform function (content, violation) -> TransformResult.
        """
        self._transforms[rule_id] = fn

    def __contains__(self, rule_id: str) -> bool:
        """Check if a rule has a registered transform.

        Args:
            rule_id: Rule identifier to look up.

        Returns:
            True if rule_id is registered.
        """
        return rule_id in self._transforms

    def __len__(self) -> int:
        """Return the number of registered transforms.

        Returns:
            Count of registered rule IDs.
        """
        return len(self._transforms)

    def __iter__(self) -> Iterator[str]:
        """Iterate over registered rule IDs.

        Returns:
            Iterator of rule ID strings.
        """
        return iter(self._transforms)

    @property
    def rule_ids(self) -> list[str]:
        """Return sorted list of registered rule IDs.

        Returns:
            Sorted list of rule ID strings.
        """
        return sorted(self._transforms)

    def apply(self, rule_id: str, content: str, violation: ViolationDict) -> TransformResult:
        """Apply the transform for a rule to content.

        Args:
            rule_id: Rule identifier.
            content: File content string.
            violation: Violation dict for context.

        Returns:
            TransformResult with possibly modified content and applied flag.
        """
        fn = self._transforms.get(rule_id)
        if fn is None:
            return TransformResult(content=content, applied=False)
        return fn(content, violation)
