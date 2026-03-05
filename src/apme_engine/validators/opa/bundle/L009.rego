# L009: Avoid comparison to empty string in when

package apme.rules

import future.keywords.if
import future.keywords.in

violations contains v if {
	some tree in input.hierarchy
	some node in tree.nodes
	v := empty_string_compare(tree, node)
}

empty_string_compare(tree, node) := v if {
	node.type == "taskcall"
	when_val := object.get(node, "options", {})["when"]
	when_val == ""
	count(node.line) > 0
	v := {
		"rule_id": "L009",
		"level": "warning",
		"message": "Avoid comparison to empty string in when",
		"file": node.file,
		"line": node.line[0],
		"path": node.key,
	}
}

empty_string_compare(tree, node) := v if {
	node.type == "taskcall"
	when_val := object.get(node, "options", {})["when"]
	contains(when_val, " == \"\"")
	count(node.line) > 0
	v := {
		"rule_id": "L009",
		"level": "warning",
		"message": "Avoid comparison to empty string in when",
		"file": node.file,
		"line": node.line[0],
		"path": node.key,
	}
}
