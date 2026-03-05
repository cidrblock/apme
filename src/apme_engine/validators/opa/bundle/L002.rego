# L002: Use FQCN for module

package apme.rules

import future.keywords.if
import future.keywords.in

violations contains v if {
	some tree in input.hierarchy
	some node in tree.nodes
	v := task_not_fqcn(tree, node)
}

task_not_fqcn(tree, node) := v if {
	node.type == "taskcall"
	node.module != ""
	not startswith(node.module, "ansible.builtin.")
	not startswith(node.module, "ansible.legacy.")
	count(split(node.module, ".")) < 3
	count(node.line) > 0
	v := {
		"rule_id": "L002",
		"level": "warning",
		"message": sprintf("Use FQCN for module: %s", [node.module]),
		"file": node.file,
		"line": node.line[0],
		"path": node.key,
	}
}
