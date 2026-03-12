from dataclasses import dataclass

from apme_engine.engine.models import Annotation, AnsibleRunContext, TaskCall


class Annotator:
    type: str = ""
    context: AnsibleRunContext = None

    def __init__(self, context: AnsibleRunContext = None):
        if context:
            self.context = context

    def run(self, task: TaskCall):
        raise ValueError("this is a base class method")


@dataclass
class AnnotatorResult:
    annotations: list[Annotation] = None
    data: any = None

    def print(self):
        raise ValueError("this is a base class method")

    def to_json(self):
        raise ValueError("this is a base class method")

    def error(self):
        raise ValueError("this is a base class method")
