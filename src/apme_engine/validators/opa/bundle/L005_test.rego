# Integration tests for L005: Use only ansible.builtin or ansible.legacy

package apme.rules_test

import data.apme.rules

test_L005_fires_for_short_module if {
	tree := {"nodes": [{"type": "taskcall", "module": "copy", "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	v := rules.only_builtins(tree, node)
	v.rule_id == "L005"
}

test_L005_does_not_fire_for_builtin if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.copy", "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.only_builtins(tree, node)
}
