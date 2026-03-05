# L011: Avoid comparison to literal true/false in when

package apme.rules

import future.keywords.if
import future.keywords.in

violations contains v if {
	some tree in input.hierarchy
	some node in tree.nodes
	v := literal_compare(tree, node)
}

literal_compare(tree, node) := v if {
	node.type == "taskcall"
	when_val := object.get(node, "options", {})["when"]
	contains(when_val, " == true")
	count(node.line) > 0
	v := {
		"rule_id": "L011",
		"level": "warning",
		"message": "Avoid comparison to literal true/false in when",
		"file": node.file,
		"line": node.line[0],
		"path": node.key,
	}
}

literal_compare(tree, node) := v if {
	node.type == "taskcall"
	when_val := object.get(node, "options", {})["when"]
	contains(when_val, " == false")
	count(node.line) > 0
	v := {
		"rule_id": "L011",
		"level": "warning",
		"message": "Avoid comparison to literal true/false in when",
		"file": node.file,
		"line": node.line[0],
		"path": node.key,
	}
}

literal_compare(tree, node) := v if {
	node.type == "taskcall"
	when_val := object.get(node, "options", {})["when"]
	contains(when_val, " is true")
	count(node.line) > 0
	v := {
		"rule_id": "L011",
		"level": "warning",
		"message": "Avoid comparison to literal true/false in when",
		"file": node.file,
		"line": node.line[0],
		"path": node.key,
	}
}

literal_compare(tree, node) := v if {
	node.type == "taskcall"
	when_val := object.get(node, "options", {})["when"]
	contains(when_val, " is false")
	count(node.line) > 0
	v := {
		"rule_id": "L011",
		"level": "warning",
		"message": "Avoid comparison to literal true/false in when",
		"file": node.file,
		"line": node.line[0],
		"path": node.key,
	}
}
