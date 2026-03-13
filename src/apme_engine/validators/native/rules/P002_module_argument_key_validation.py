"""Native rule P002: validate module argument keys and set annotations."""

from dataclasses import dataclass
from typing import cast

from apme_engine.engine.models import (
    ActionGroupMetadata,
    AnsibleRunContext,
    ExecutableType,
    Module,
    Rule,
    RuleResult,
    RunTargetType,
    Severity,
    TaskCall,
    YAMLDict,
    YAMLValue,
)
from apme_engine.engine.models import RuleTag as Tag


def is_set_fact(module_fqcn: str) -> bool:
    """Check if module is ansible.builtin.set_fact.

    Args:
        module_fqcn: Fully qualified module name.

    Returns:
        True if module is set_fact.
    """
    return module_fqcn == "ansible.builtin.set_fact"


def is_meta(module_fqcn: str) -> bool:
    """Check if module is ansible.builtin.meta.

    Args:
        module_fqcn: Fully qualified module name.

    Returns:
        True if module is meta.
    """
    return module_fqcn == "ansible.builtin.meta"


@dataclass
class ModuleArgumentKeyValidationRule(Rule):
    """Rule to validate module argument keys and set annotations.

    Attributes:
        rule_id: Rule identifier.
        description: Rule description.
        enabled: Whether the rule is enabled.
        name: Rule name.
        version: Rule version.
        severity: Severity level.
        tags: Rule tags.
        precedence: Evaluation order.
    """

    rule_id: str = "P002"
    description: str = "Validate module argument keys and set annotations"
    enabled: bool = True
    name: str = "ModuleArgumentKeyValidation"
    version: str = "v0.0.1"
    severity: str = Severity.NONE
    tags: tuple[str, ...] = (Tag.QUALITY,)
    precedence: int = 0

    def match(self, ctx: AnsibleRunContext) -> bool:
        """Check if context has a task target.

        Args:
            ctx: AnsibleRunContext to evaluate.

        Returns:
            True if current target is a task.
        """
        if ctx.current is None:
            return False
        return bool(ctx.current.type == RunTargetType.Task)

    def process(self, ctx: AnsibleRunContext) -> RuleResult | None:
        """Validate module argument keys and set annotations on task.

        Args:
            ctx: AnsibleRunContext to process.

        Returns:
            None (sets annotations on task).
        """
        task = ctx.current
        if task is None or not isinstance(task, TaskCall):
            return None

        if (
            getattr(task.spec, "executable_type", "") == ExecutableType.MODULE_TYPE
            and task.module
            and task.module.arguments
        ):
            mo = getattr(task.spec, "module_options", {})
            module_fqcn_val = task.get_annotation(key="module.correct_fqcn")
            module_fqcn = str(module_fqcn_val) if isinstance(module_fqcn_val, str) else ""
            module_short = ""
            if module_fqcn:
                parts = module_fqcn.split(".")
                if len(parts) <= 2:
                    module_short = module_fqcn.split(".")[-1]
                elif len(parts) > 2:
                    module_short = ".".join(module_fqcn.split(".")[2:])
            default_args: YAMLDict = {}
            if module_short and module_short in task.module_defaults:
                val = task.module_defaults[module_short]
                default_args = val if isinstance(val, dict) else {}
            elif module_fqcn and module_fqcn in task.module_defaults:
                val = task.module_defaults.get(module_fqcn)
                default_args = val if isinstance(val, dict) else {}
            elif ctx.ram_client:
                for group_name in task.module_defaults:
                    tmp_args = task.module_defaults[group_name]
                    if not isinstance(tmp_args, dict):
                        continue
                    found = False
                    if not group_name.startswith("group/"):
                        continue
                    groups = ctx.ram_client.search_action_group(group_name)
                    if not groups:
                        continue
                    for group_dict in groups:
                        if not group_dict:
                            continue
                        if not isinstance(group_dict, dict):
                            continue
                        group = ActionGroupMetadata.from_dict(group_dict)
                        group_modules = group.group_modules

                        def _module_matches(m: Module, name: str) -> bool:
                            return m.fqcn == name or getattr(m, "name", "") == name

                        if (module_short and any(_module_matches(m, module_short) for m in group_modules)) or (
                            module_fqcn and any(_module_matches(m, module_fqcn) for m in group_modules)
                        ):
                            found = True
                            default_args = tmp_args if isinstance(tmp_args, dict) else {}
                            break
                    if found:
                        break

            used_keys = []
            if isinstance(mo, dict):
                used_keys = list(mo.keys())

            available_keys = []
            required_keys = []
            alias_reverse_map = {}
            available_args = None
            wrong_keys = []
            missing_required_keys = []
            if not is_set_fact(module_fqcn) and not is_meta(module_fqcn):
                if task.module:
                    for arg in task.module.arguments:
                        available_keys.extend(arg.available_keys())
                        if arg.required:
                            aliases = list(arg.aliases) if arg.aliases else []
                            req_k: dict[str, str | list[str]] = {"key": arg.name, "aliases": aliases}
                            required_keys.append(req_k)
                        if arg.aliases:
                            for al in arg.aliases:
                                alias_reverse_map[al] = arg.name
                    available_args = task.module.arguments

                wrong_keys = [k for k in used_keys if k not in available_keys]

                for k in required_keys:
                    name = k.get("key", "")
                    if name in used_keys:
                        continue
                    if name in default_args:
                        continue
                    if aliases:
                        found = False
                        for a_k in aliases:
                            if a_k in used_keys:
                                found = True
                                break
                            if a_k in default_args:
                                found = True
                                break
                        if found:
                            continue
                    # here, the required key was not found
                    missing_required_keys.append(name)

            used_alias_and_real_keys = []
            for k in used_keys:
                if k not in alias_reverse_map:
                    continue
                real_name = alias_reverse_map[k]
                used_alias_and_real_keys.append(
                    {
                        "used_alias": k,
                        "real_key": real_name,
                    }
                )

            task.set_annotation("module.wrong_arg_keys", cast(YAMLValue, wrong_keys), rule_id=self.rule_id)
            task.set_annotation("module.available_arg_keys", cast(YAMLValue, available_keys), rule_id=self.rule_id)
            task.set_annotation("module.required_arg_keys", cast(YAMLValue, required_keys), rule_id=self.rule_id)
            task.set_annotation(
                "module.missing_required_arg_keys", cast(YAMLValue, missing_required_keys), rule_id=self.rule_id
            )
            task.set_annotation("module.available_args", cast(YAMLValue, available_args), rule_id=self.rule_id)
            task.set_annotation("module.default_args", cast(YAMLValue, default_args), rule_id=self.rule_id)
            task.set_annotation(
                "module.used_alias_and_real_keys", cast(YAMLValue, used_alias_and_real_keys), rule_id=self.rule_id
            )

        # TODO: find duplicate keys

        return None
