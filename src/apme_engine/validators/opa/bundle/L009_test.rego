# Integration tests for L009: Avoid comparison to empty string in when

package apme.rules_test

import data.apme.rules

test_L009_fires_when_empty_string_compare if {
	tree := {"nodes": [{"type": "taskcall", "options": {"when": ""}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	v := rules.empty_string_compare(tree, node)
	v.rule_id == "L009"
}

test_L009_does_not_fire_when_no_when if {
	tree := {"nodes": [{"type": "taskcall", "options": {}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.empty_string_compare(tree, node)
}
