# L001: Task using shell module should have a name

package apme.rules

import future.keywords.if
import future.keywords.in

violations contains v if {
	some tree in input.hierarchy
	some node in tree.nodes
	v := task_has_no_name(tree, node)
}

task_has_no_name(tree, node) := v if {
	node.type == "taskcall"
	node.module == "ansible.builtin.shell"
	object.get(node, "name", null) == null
	count(node.line) > 0
	v := {
		"rule_id": "L001",
		"level": "warning",
		"message": "Task using shell module should have a name",
		"file": node.file,
		"line": node.line[0],
		"path": node.key,
	}
}
