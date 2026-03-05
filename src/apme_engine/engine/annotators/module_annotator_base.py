from dataclasses import dataclass
from apme_engine.engine.models import TaskCall
from apme_engine.engine.annotators.annotator_base import Annotator, AnnotatorResult


class ModuleAnnotator(Annotator):
    type: str = "module_annotation"
    fqcn: str = "<module FQCN to be annotated by this>"

    def run(self, task: TaskCall) -> AnnotatorResult:
        raise ValueError("this is a base class method")


@dataclass
class ModuleAnnotatorResult(AnnotatorResult):
    pass
