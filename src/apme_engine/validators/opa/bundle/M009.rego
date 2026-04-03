# M009: with_* loops are deprecated; use loop: instead

package apme.rules

import future.keywords.if
import future.keywords.in

violations contains v if {
	some tree in input.hierarchy
	some node in tree.nodes
	v := deprecated_with_loop(tree, node)
}

deprecated_with_loop(tree, node) := v if {
	node.type == "taskcall"
	opts := object.get(node, "options", {})
	wk := has_with_loop(opts)
	count(node.line) > 0
	v := {
		"rule_id": "M009",
		"severity": "high",
		"message": sprintf("with_* loops are deprecated; use loop: instead of %s", [wk]),
		"file": node.file,
		"line": node.line[0],
		"path": node.key,
		"with_key": wk,
		"scope": "task",
	}
}
