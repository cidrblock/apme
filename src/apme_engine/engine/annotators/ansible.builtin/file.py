from typing import List
from apme_engine.engine.models import Annotation, RiskAnnotation, TaskCall, DefaultRiskType, FileChangeDetail
from apme_engine.engine.annotators.module_annotator_base import ModuleAnnotator, ModuleAnnotatorResult


class FileAnnotator(ModuleAnnotator):
    fqcn: str = "ansible.builtin.file"
    enabled: bool = True

    def run(self, task: TaskCall) -> List[Annotation]:
        path = task.args.get("path")
        mode = task.args.get("mode")
        unsafe_writes = task.args.get("unsafe_writes")
        state = task.args.get("state")

        annotation = RiskAnnotation.init(risk_type=DefaultRiskType.FILE_CHANGE,
                                         detail=FileChangeDetail(_path_arg=path, _state_arg=state, _mode_arg=mode, _unsafe_write_arg=unsafe_writes))
        return ModuleAnnotatorResult(annotations=[annotation])
