# Integration tests for L012: Avoid state=latest (uses package_modules from data)

package apme.rules_test

import data.apme.rules

test_L012_fires_when_yum_state_latest if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.yum", "module_options": {"state": "latest"}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	v := rules.latest(tree, node)
	v.rule_id == "L012"
}

test_L012_does_not_fire_when_state_present if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.yum", "module_options": {"state": "present"}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.latest(tree, node)
}
