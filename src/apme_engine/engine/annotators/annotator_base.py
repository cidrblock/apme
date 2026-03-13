from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from apme_engine.engine.context import Context
from apme_engine.engine.models import Annotation, AnsibleRunContext, TaskCall, YAMLValue


class Annotator:
    type: str = ""
    context: AnsibleRunContext | Context | None = None

    def __init__(self, context: AnsibleRunContext | Context | None = None) -> None:
        if context is not None:
            self.context = context

    def run(self, task: TaskCall) -> AnnotatorResult | None:
        raise ValueError("this is a base class method")


@dataclass
class AnnotatorResult:
    annotations: Sequence[Annotation] | None = field(default=None)
    data: object | None = None

    def print(self) -> None:
        raise ValueError("this is a base class method")

    def to_json(self) -> YAMLValue:
        raise ValueError("this is a base class method")

    def error(self) -> None:
        raise ValueError("this is a base class method")
