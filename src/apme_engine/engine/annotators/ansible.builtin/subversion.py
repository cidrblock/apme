from typing import List
from apme_engine.engine.models import Annotation, RiskAnnotation, TaskCall, DefaultRiskType, InboundTransferDetail
from apme_engine.engine.annotators.module_annotator_base import ModuleAnnotator, ModuleAnnotatorResult


class SubversionAnnotator(ModuleAnnotator):
    fqcn: str = "ansible.builtin.subversion"
    enabled: bool = True

    def run(self, task: TaskCall) -> List[Annotation]:
        src = task.args.get("repo")
        dest = task.args.get("dest")
        annotation = RiskAnnotation.init(risk_type=DefaultRiskType.INBOUND, detail=InboundTransferDetail(_src_arg=src, _dest_arg=dest))
        return ModuleAnnotatorResult(annotations=[annotation])
