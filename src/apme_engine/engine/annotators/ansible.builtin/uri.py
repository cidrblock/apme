from apme_engine.engine.models import RiskAnnotation, TaskCall, DefaultRiskType, OutboundTransferDetail
from apme_engine.engine.annotators.module_annotator_base import ModuleAnnotator, ModuleAnnotatorResult


class URIAnnotator(ModuleAnnotator):
    fqcn: str = "ansible.builtin.uri"
    enabled: bool = True

    def run(self, task: TaskCall) -> ModuleAnnotatorResult:
        method = task.args.get("method")

        annotations = []
        if method in ["PUT", "POST", "PATCH"]:
            url = task.args.get("url")
            body = task.args.get("body")
            annotation = RiskAnnotation.init(
                risk_type=DefaultRiskType.OUTBOUND,
                detail=OutboundTransferDetail(_dest_arg=url, _src_arg=body),
            )
            annotations.append(annotation)
        return ModuleAnnotatorResult(annotations=annotations)
