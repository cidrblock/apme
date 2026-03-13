"""Base classes for Ansible task annotators."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from apme_engine.engine.context import Context
from apme_engine.engine.models import Annotation, AnsibleRunContext, TaskCall, YAMLValue


class Annotator:
    """Base class for annotators that analyze Ansible tasks.

    Attributes:
        type: Annotator type identifier string.
        context: Optional AnsibleRunContext or Context for variable resolution.

    """

    type: str = ""
    context: AnsibleRunContext | Context | None = None

    def __init__(self, context: AnsibleRunContext | Context | None = None) -> None:
        """Initialize annotator with optional run context.

        Args:
            context: Optional AnsibleRunContext or Context for variable resolution.
        """
        if context is not None:
            self.context = context

    def run(self, task: TaskCall) -> AnnotatorResult | None:
        """Run annotation on a task. Override in subclasses.

        Args:
            task: TaskCall to annotate.

        Returns:
            AnnotatorResult or None if not applicable.

        Raises:
            ValueError: If called on base class (override in subclasses).
        """
        raise ValueError("this is a base class method")


@dataclass
class AnnotatorResult:
    """Result container for annotator output (annotations and optional data).

    Attributes:
        annotations: Sequence of Annotation objects or None.
        data: Optional data payload from the annotator.

    """

    annotations: Sequence[Annotation] | None = field(default=None)
    data: object | None = None

    def print(self) -> None:
        """Print result. Override in subclasses.

        Raises:
            ValueError: If called on base class (override in subclasses).
        """
        raise ValueError("this is a base class method")

    def to_json(self) -> YAMLValue:
        """Serialize result to JSON-serializable value. Override in subclasses.

        Returns:
            JSON-serializable value (dict, list, str, etc.).

        Raises:
            ValueError: If called on base class (override in subclasses).
        """
        raise ValueError("this is a base class method")

    def error(self) -> None:
        """Handle error case. Override in subclasses.

        Raises:
            ValueError: If called on base class (override in subclasses).
        """
        raise ValueError("this is a base class method")
