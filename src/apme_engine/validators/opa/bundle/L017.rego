# L017: Avoid relative path in src (uses copy_template_modules from _helpers.rego)

package apme.rules

import future.keywords.if
import future.keywords.in

violations contains v if {
	some tree in input.hierarchy
	some node in tree.nodes
	v := no_relative_paths(tree, node)
}

no_relative_paths(tree, node) := v if {
	node.type == "taskcall"
	copy_template_modules[node.module]
	src := object.get(node, "module_options", {})["src"]
	contains(src, "../")
	count(node.line) > 0
	v := {
		"rule_id": "L017",
		"level": "warning",
		"message": "Avoid relative path in src; use role-relative paths",
		"file": node.file,
		"line": node.line[0],
		"path": node.key,
	}
}
