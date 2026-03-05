from typing import List
from apme_engine.engine.models import Annotation, RiskAnnotation, TaskCall, DefaultRiskType, InboundTransferDetail
from apme_engine.engine.annotators.module_annotator_base import ModuleAnnotator, ModuleAnnotatorResult


class GetURLAnnotator(ModuleAnnotator):
    fqcn: str = "ansible.builtin.get_url"
    enabled: bool = True

    def run(self, task: TaskCall) -> List[Annotation]:
        src = task.args.get("url")
        dest = task.args.get("dest")

        annotation = RiskAnnotation.init(risk_type=DefaultRiskType.INBOUND, detail=InboundTransferDetail(_src_arg=src, _dest_arg=dest))
        return ModuleAnnotatorResult(annotations=[annotation])
