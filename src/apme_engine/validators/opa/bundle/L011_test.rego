# Integration tests for L011: Avoid literal true/false in when

package apme.rules_test

import data.apme.rules

test_L011_fires_when_equals_true if {
	tree := {"nodes": [{"type": "taskcall", "options": {"when": "x == true"}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	v := rules.literal_compare(tree, node)
	v.rule_id == "L011"
}

test_L011_does_not_fire_when_no_literal if {
	tree := {"nodes": [{"type": "taskcall", "options": {"when": "x"}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.literal_compare(tree, node)
}
