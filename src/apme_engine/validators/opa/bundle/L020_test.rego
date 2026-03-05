# Integration tests for L020: mode should be string with leading zero (uses file_permission_modules, is_number)

package apme.rules_test

import data.apme.rules

test_L020_fires_when_mode_numeric if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.copy", "module_options": {"mode": 644}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	v := rules.risky_octal(tree, node)
	v.rule_id == "L020"
}

test_L020_does_not_fire_when_mode_string if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.copy", "module_options": {"mode": "0644"}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.risky_octal(tree, node)
}
