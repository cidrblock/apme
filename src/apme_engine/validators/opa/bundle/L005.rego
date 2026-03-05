# L005: Use only ansible.builtin or ansible.legacy

package apme.rules

import future.keywords.if
import future.keywords.in

violations contains v if {
	some tree in input.hierarchy
	some node in tree.nodes
	v := only_builtins(tree, node)
}

only_builtins(tree, node) := v if {
	node.type == "taskcall"
	node.module != ""
	not startswith(node.module, "ansible.builtin.")
	not startswith(node.module, "ansible.legacy.")
	count(node.line) > 0
	v := {
		"rule_id": "L005",
		"level": "warning",
		"message": sprintf("Use only ansible.builtin or ansible.legacy: %s", [node.module]),
		"file": node.file,
		"line": node.line[0],
		"path": node.key,
	}
}
