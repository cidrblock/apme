# L014: Use notify/handler instead of when: result.changed

package apme.rules

import future.keywords.if
import future.keywords.in

violations contains v if {
	some tree in input.hierarchy
	some node in tree.nodes
	v := no_handler(tree, node)
}

no_handler(tree, node) := v if {
	node.type == "taskcall"
	when_val := object.get(node, "options", {})["when"]
	contains(when_val, ".changed")
	count(node.line) > 0
	v := {
		"rule_id": "L014",
		"level": "info",
		"message": "Use notify/handler instead of when: result.changed",
		"file": node.file,
		"line": node.line[0],
		"path": node.key,
	}
}

no_handler(tree, node) := v if {
	node.type == "taskcall"
	when_val := object.get(node, "options", {})["when"]
	contains(when_val, "is changed")
	count(node.line) > 0
	v := {
		"rule_id": "L014",
		"level": "info",
		"message": "Use notify/handler instead of when: result.changed",
		"file": node.file,
		"line": node.line[0],
		"path": node.key,
	}
}
