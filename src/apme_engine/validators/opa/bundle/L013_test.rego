# Integration tests for L013: command/shell should have changed_when or creates/removes

package apme.rules_test

import data.apme.rules

test_L013_does_not_fire_when_changed_when_present if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.shell", "options": {"changed_when": true}, "module_options": {}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.no_changed_when(tree, node)
}
