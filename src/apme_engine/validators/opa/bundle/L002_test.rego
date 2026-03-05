# Integration tests for L002: Use FQCN for module

package apme.rules_test

import data.apme.rules

test_L002_fires_when_short_module_name if {
	tree := {"nodes": [{"type": "taskcall", "module": "copy", "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	v := rules.task_not_fqcn(tree, node)
	v.rule_id == "L002"
	v.level == "warning"
}

test_L002_does_not_fire_for_fqcn if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.copy", "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.task_not_fqcn(tree, node)
}

test_L002_does_not_fire_for_legacy if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.legacy.copy", "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.task_not_fqcn(tree, node)
}
