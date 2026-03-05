# Integration tests for L010: Use failed_when or register instead of ignore_errors

package apme.rules_test

import data.apme.rules

test_L010_fires_when_ignore_errors_true if {
	tree := {"nodes": [{"type": "taskcall", "options": {"ignore_errors": true}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	v := rules.ignore_errors(tree, node)
	v.rule_id == "L010"
}

test_L010_does_not_fire_when_register_present if {
	tree := {"nodes": [{"type": "taskcall", "options": {"ignore_errors": true, "register": "out"}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.ignore_errors(tree, node)
}
