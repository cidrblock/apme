# Integration tests for L008: Do not use local_action

package apme.rules_test

import data.apme.rules

test_L008_fires_when_local_action_present if {
	tree := {"nodes": [{"type": "taskcall", "options": {"local_action": "shell echo hi"}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	v := rules.deprecated_local_action(tree, node)
	v.rule_id == "L008"
}

test_L008_does_not_fire_without_local_action if {
	tree := {"nodes": [{"type": "taskcall", "options": {}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.deprecated_local_action(tree, node)
}
