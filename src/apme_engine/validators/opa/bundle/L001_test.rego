# Integration tests for L001: Task using shell module should have a name

package apme.rules_test

import data.apme.rules

test_L001_fires_when_shell_task_has_no_name if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.shell", "name": null, "line": [1], "key": "tasks[0]", "file": "main.yml"}]}
	node := tree.nodes[0]
	v := rules.task_has_no_name(tree, node)
	v.rule_id == "L001"
	v.level == "warning"
}

test_L001_does_not_fire_when_task_has_name if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.shell", "name": "Run something", "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.task_has_no_name(tree, node)
}

test_L001_does_not_fire_for_non_shell_module if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.command", "name": null, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.task_has_no_name(tree, node)
}
