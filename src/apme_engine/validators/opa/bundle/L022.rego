# L022: Shell with pipe should set set -o pipefail

package apme.rules

import future.keywords.if
import future.keywords.in

violations contains v if {
	some tree in input.hierarchy
	some node in tree.nodes
	v := risky_shell_pipe(tree, node)
}

risky_shell_pipe(tree, node) := v if {
	node.type == "taskcall"
	{"ansible.builtin.shell", "ansible.legacy.shell", "shell"}[node.module]
	cmd := object.get(node, "module_options", {})["cmd"]
	contains(cmd, "|")
	contains(cmd, "pipefail") == false
	count(node.line) > 0
	v := {
		"rule_id": "L022",
		"level": "warning",
		"message": "Shell with pipe should set set -o pipefail",
		"file": node.file,
		"line": node.line[0],
		"path": node.key,
	}
}
