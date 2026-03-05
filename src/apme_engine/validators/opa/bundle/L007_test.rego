# Integration tests for L007: Prefer command when no shell features needed

package apme.rules_test

import data.apme.rules

test_L007_fires_when_shell_without_pipe if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.shell", "module_options": {"cmd": "echo hi"}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	v := rules.command_instead_of_shell(tree, node)
	v.rule_id == "L007"
}

test_L007_does_not_fire_when_shell_has_pipe if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.shell", "module_options": {"cmd": "cat f | grep x"}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.command_instead_of_shell(tree, node)
}
