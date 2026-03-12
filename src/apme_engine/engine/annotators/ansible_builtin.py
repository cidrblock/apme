from apme_engine.engine.annotators.risk_annotator_base import RiskAnnotator
from apme_engine.engine.models import TaskCall


class AnsibleBuiltinRiskAnnotator(RiskAnnotator):
    name: str = "ansible.builtin"
    enabled: bool = True

    def match(self, task: TaskCall) -> bool:
        resolved_name = task.spec.resolved_name
        return resolved_name.startswith("ansible.builtin.")

    # embed "analyzed_data" field in Task
    def run(self, task: TaskCall):
        if not self.match(task):
            return []

        return self.run_module_annotators("ansible.builtin", task)
