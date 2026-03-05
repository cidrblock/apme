from dataclasses import dataclass
from typing import List
from apme_engine.engine.models import TaskCall, AnsibleRunContext, Annotation


class Annotator(object):
    type: str = ""
    context: AnsibleRunContext = None

    def __init__(self, context: AnsibleRunContext = None):
        if context:
            self.context = context

    def run(self, task: TaskCall):
        raise ValueError("this is a base class method")


@dataclass
class AnnotatorResult(object):
    annotations: List[Annotation] = None
    data: any = None

    def print(self):
        raise ValueError("this is a base class method")

    def to_json(self):
        raise ValueError("this is a base class method")

    def error(self):
        raise ValueError("this is a base class method")
