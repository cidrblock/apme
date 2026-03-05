from typing import List
from apme_engine.engine.models import Annotation, RiskAnnotation, TaskCall, DefaultRiskType, PackageInstallDetail
from apme_engine.engine.annotators.module_annotator_base import ModuleAnnotator, ModuleAnnotatorResult


class DnfAnnotator(ModuleAnnotator):
    fqcn: str = "ansible.builtin.dnf"
    enabled: bool = True

    def run(self, task: TaskCall) -> List[Annotation]:
        pkg = task.args.get("name")
        allow_downgrade = task.args.get("allow_downgrade")
        validate_certs = task.args.get("validate_certs")

        annotation = RiskAnnotation.init(risk_type=DefaultRiskType.PACKAGE_INSTALL, detail=PackageInstallDetail(_pkg_arg=pkg,
                                         _validate_certs_arg=validate_certs, _allow_downgrade_arg=allow_downgrade))
        return ModuleAnnotatorResult(annotations=[annotation])
