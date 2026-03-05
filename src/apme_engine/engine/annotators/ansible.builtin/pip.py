from typing import List
from apme_engine.engine.models import Annotation, RiskAnnotation, TaskCall, DefaultRiskType, PackageInstallDetail
from apme_engine.engine.annotators.module_annotator_base import ModuleAnnotator, ModuleAnnotatorResult


class PipAnnotator(ModuleAnnotator):
    fqcn: str = "ansible.builtin.pip"
    enabled: bool = True

    def run(self, task: TaskCall) -> List[Annotation]:
        pkg = task.args.get("name")
        if pkg is None:
            pkg = task.args.get("requirements")

        annotation = RiskAnnotation.init(risk_type=DefaultRiskType.PACKAGE_INSTALL, detail=PackageInstallDetail(_pkg_arg=pkg))
        return ModuleAnnotatorResult(annotations=[annotation])
