from dataclasses import dataclass
from typing import cast

from apme_engine.engine.models import (
    AnsibleRunContext,
    ArgumentsType,
    ExecutableType,
    Rule,
    RuleResult,
    RunTargetType,
    Severity,
    TaskCall,
    VariableType,
    YAMLValue,
)
from apme_engine.engine.models import RuleTag as Tag


def is_loop_var(value: str, task: TaskCall) -> bool:
    # `item` and alternative loop variable (if any) should not be replaced to avoid breaking loop
    skip_variables = ["item"]
    loop = getattr(task.spec, "loop", None)
    if loop and isinstance(loop, dict):
        skip_variables.extend(list(loop.keys()))

    _v = value.replace(" ", "")

    for var in skip_variables:
        for _prefix in ["}}", "|", "."]:
            pattern = "{{" + var + _prefix
            if pattern in _v:
                return True
    return False


def is_debug(module_fqcn: str) -> bool:
    return module_fqcn == "ansible.builtin.debug"


@dataclass
class ModuleArgumentValueValidationRule(Rule):
    rule_id: str = "P003"
    description: str = "Validate module argument values and set annotations"
    enabled: bool = True
    name: str = "ModuleArgumentValueValidation"
    version: str = "v0.0.1"
    severity: str = Severity.NONE
    tags: tuple[str, ...] = (Tag.QUALITY,)
    precedence: int = 0

    def match(self, ctx: AnsibleRunContext) -> bool:
        if ctx.current is None:
            return False
        return bool(ctx.current.type == RunTargetType.Task)

    def process(self, ctx: AnsibleRunContext) -> RuleResult | None:
        task = ctx.current
        if task is None or not isinstance(task, TaskCall):
            return None

        if (
            getattr(task.spec, "executable_type", "") == ExecutableType.MODULE_TYPE
            and task.module
            and task.module.arguments
        ):
            wrong_values: list[dict[str, str | YAMLValue]] = []
            undefined_values: list[dict[str, str | list[str]]] = []
            unknown_type_values: list[dict[str, str | YAMLValue]] = []

            registered_vars: list[str] = []
            for v_name in task.variable_set:
                v = task.variable_set[v_name]
                if (
                    isinstance(v, list)
                    and v
                    and (v[-1] is not None and getattr(v[-1], "type", None) == VariableType.RegisteredVars)
                ):
                    registered_vars.append(v_name)

            module_fqcn = task.module.fqcn

            raw_args = task.args.raw
            if task.args.type == ArgumentsType.DICT and isinstance(raw_args, dict):
                for key in raw_args:
                    raw_value = raw_args[key]
                    resolved_value: YAMLValue | None = None
                    templated = task.args.templated
                    if isinstance(templated, list) and len(templated) >= 1:
                        first = templated[0]
                        if isinstance(first, dict) and key in first:
                            resolved_value = first[key]
                    spec = None
                    for arg_spec in task.module.arguments:
                        if key == arg_spec.name or (arg_spec.aliases and key in arg_spec.aliases):
                            spec = arg_spec
                            break
                    if not spec:
                        continue

                    d: dict[str, str | YAMLValue] = {"key": str(key)}
                    wrong_val = False
                    unknown_type_val = False
                    if spec.type and not is_debug(module_fqcn):
                        actual_type: str = ""
                        # if the raw_value is not a variable
                        if not isinstance(raw_value, str) or "{{" not in raw_value:
                            actual_type = type(raw_value).__name__
                        else:
                            # otherwise, check the resolved value
                            # if the variable could not be resovled successfully
                            if isinstance(resolved_value, str) and "{{" in resolved_value:
                                pass
                            elif is_loop_var(str(raw_value), task):
                                # if the variable is loop var, use the element type as actual type
                                resolved_element: YAMLValue | None = None
                                if isinstance(resolved_value, (list, tuple)) and resolved_value:
                                    resolved_element = resolved_value[0]
                                if resolved_element is not None:
                                    actual_type = type(resolved_element).__name__
                            else:
                                # otherwise, use the resolved value type as actual type
                                actual_type = type(resolved_value).__name__ if resolved_value is not None else ""

                        if actual_type:
                            type_wrong = False
                            if spec.type != "any" and actual_type != spec.type:
                                type_wrong = True

                            elements_type = spec.elements
                            if spec.type == "list" and not spec.elements:
                                elements_type = "any"

                            elements_type_wrong = False
                            no_elements = False
                            if elements_type:
                                if elements_type != "any" and actual_type != elements_type:
                                    elements_type_wrong = True
                            else:
                                no_elements = True
                            if type_wrong and (elements_type_wrong or no_elements):
                                d["expected_type"] = str(spec.type) if spec.type else ""
                                d["actual_type"] = actual_type
                                d["actual_value"] = raw_value
                                wrong_val = True
                        else:
                            d["expected_type"] = str(spec.type) if spec.type else ""
                            d["unknown_type_value"] = resolved_value
                            unknown_type_val = True

                    if wrong_val:
                        wrong_values.append(d)

                    if unknown_type_val:
                        unknown_type_values.append(d)

                    sub_args = task.args.get(str(key))
                    if sub_args:
                        undefined_vars_list: list[str] = []
                        for var in sub_args.vars:
                            first_v_name = var.name.split(".")[0]
                            # skip registered vars
                            if first_v_name in registered_vars:
                                continue

                            if var.type == VariableType.Unknown:
                                undefined_vars_list.append(var.name)

                        if undefined_vars_list:
                            undefined_values.append(
                                {
                                    "key": str(key),
                                    "value": str(raw_value) if raw_value is not None else "",
                                    "undefined_variables": undefined_vars_list,
                                }
                            )

            task.set_annotation("module.wrong_arg_values", cast(YAMLValue, wrong_values), rule_id=self.rule_id)
            task.set_annotation("module.undefined_values", cast(YAMLValue, undefined_values), rule_id=self.rule_id)
            task.set_annotation(
                "module.unknown_type_values", cast(YAMLValue, unknown_type_values), rule_id=self.rule_id
            )

        # TODO: find duplicate keys

        return None
