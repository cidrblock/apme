# Integration tests for L021: Consider setting mode explicitly (uses file_permission_modules)

package apme.rules_test

import data.apme.rules

test_L021_fires_when_file_module_no_mode if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.file", "module_options": {}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	v := rules.risky_file_permissions(tree, node)
	v.rule_id == "L021"
}

test_L021_does_not_fire_when_mode_set if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.file", "module_options": {"mode": "0644"}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.risky_file_permissions(tree, node)
}
