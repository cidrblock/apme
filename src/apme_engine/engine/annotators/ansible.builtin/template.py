from typing import List
from apme_engine.engine.models import Annotation, RiskAnnotation, TaskCall, DefaultRiskType, FileChangeDetail
from apme_engine.engine.annotators.module_annotator_base import ModuleAnnotator, ModuleAnnotatorResult


class TemplateAnnotator(ModuleAnnotator):
    fqcn: str = "ansible.builtin.template"
    enabled: bool = True

    def run(self, task: TaskCall) -> List[Annotation]:
        path = task.args.get("dest")
        src = task.args.get("src")
        mode = task.args.get("mode")
        unsafe_writes = task.args.get("unsafe_writes")

        annotation = RiskAnnotation.init(risk_type=DefaultRiskType.FILE_CHANGE,
                                         detail=FileChangeDetail(_path_arg=path, _src_arg=src, _mode_arg=mode, _unsafe_write_arg=unsafe_writes))
        return ModuleAnnotatorResult(annotations=[annotation])
