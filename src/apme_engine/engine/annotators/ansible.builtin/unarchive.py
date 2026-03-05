from typing import List
from apme_engine.engine.models import Annotation, RiskAnnotation, TaskCall, DefaultRiskType, InboundTransferDetail
from apme_engine.engine.utils import parse_bool
from apme_engine.engine.annotators.module_annotator_base import ModuleAnnotator, ModuleAnnotatorResult


class UnarchiveAnnotator(ModuleAnnotator):
    fqcn: str = "ansible.builtin.unarchive"
    enabled: bool = True

    def run(self, task: TaskCall) -> List[Annotation]:
        src = task.args.get("src")  # required
        dest = task.args.get("dest")  # required
        remote_src = task.args.get("remote_src")

        is_remote_src = False
        if remote_src:

            if isinstance(remote_src.raw, str) or isinstance(remote_src.raw, bool):
                try:
                    is_remote_src = parse_bool(remote_src.raw)
                except Exception:
                    pass
            if not is_remote_src and (isinstance(remote_src.templated, str) or isinstance(remote_src.templated, bool)):
                try:
                    is_remote_src = parse_bool(remote_src.templated)
                except Exception:
                    pass

        url_sep = "://"
        is_download = False
        if is_remote_src and (url_sep in src.raw or url_sep in src.templated):
            is_download = True

        if not is_download:
            return None

        annotation = RiskAnnotation.init(risk_type=DefaultRiskType.INBOUND, detail=InboundTransferDetail(_src_arg=src, _dest_arg=dest))
        return ModuleAnnotatorResult(annotations=[annotation])
