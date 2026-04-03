# L106: set_fact + loop + when is a scaling anti-pattern
#
# Using set_fact inside a loop with a when conditional to build a filtered
# subset is O(n) task evaluations.  Jinja2 filters (selectattr, select,
# reject) achieve the same result in one pass.

package apme.rules

import future.keywords.if
import future.keywords.in

violations contains v if {
	some tree in input.hierarchy
	some node in tree.nodes
	v := set_fact_loop_when(tree, node)
}

# Modern loop: syntax
set_fact_loop_when(tree, node) := v if {
	node.type == "taskcall"
	set_fact_modules[node.module]
	opts := object.get(node, "options", {})
	object.get(opts, "loop", null) != null
	object.get(opts, "when", null) != null
	count(node.line) > 0
	v := _l106_violation(node)
}

# Legacy with_* loops (any lookup plugin)
set_fact_loop_when(tree, node) := v if {
	node.type == "taskcall"
	set_fact_modules[node.module]
	opts := object.get(node, "options", {})
	has_with_loop(opts)
	object.get(opts, "when", null) != null
	count(node.line) > 0
	v := _l106_violation(node)
}

_l106_violation(node) := {
	"rule_id": "L106",
	"severity": "medium",
	"message": "set_fact + loop + when is an O(n) anti-pattern; use Jinja2 filters (selectattr, select, reject) instead",
	"file": node.file,
	"line": node.line[0],
	"path": node.key,
	"scope": "task",
}
