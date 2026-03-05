from apme_engine.engine.models import RiskAnnotation, TaskCall, DefaultRiskType, CommandExecDetail
from apme_engine.engine.annotators.module_annotator_base import ModuleAnnotator, ModuleAnnotatorResult


class RawAnnotator(ModuleAnnotator):
    fqcn: str = "ansible.builtin.raw"
    enabled: bool = True

    def run(self, task: TaskCall) -> ModuleAnnotatorResult:
        cmd = task.args.get("")
        if cmd is None:
            cmd = task.args.get("command")
        if cmd is None:
            cmd = task.args.get("cmd")
        if cmd is None:
            cmd = task.args.get("argv")

        annotation = RiskAnnotation.init(
            risk_type=DefaultRiskType.CMD_EXEC,
            detail=CommandExecDetail(command=cmd),
        )
        return ModuleAnnotatorResult(annotations=[annotation])
