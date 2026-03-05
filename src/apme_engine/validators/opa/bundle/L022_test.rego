# Integration tests for L022: Shell with pipe should set pipefail

package apme.rules_test

import data.apme.rules

test_L022_fires_when_shell_pipe_no_pipefail if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.shell", "module_options": {"cmd": "cat f | grep x"}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	v := rules.risky_shell_pipe(tree, node)
	v.rule_id == "L022"
}

test_L022_does_not_fire_when_pipefail_present if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.shell", "module_options": {"cmd": "set -o pipefail; cat f | grep x"}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.risky_shell_pipe(tree, node)
}
