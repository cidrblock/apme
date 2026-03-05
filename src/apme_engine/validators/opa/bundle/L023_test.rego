# Integration tests for L023: Consider whether run_once is appropriate

package apme.rules_test

import data.apme.rules

test_L023_fires_when_run_once_true if {
	tree := {"nodes": [{"type": "taskcall", "options": {"run_once": true}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	v := rules.run_once(tree, node)
	v.rule_id == "L023"
}

test_L023_does_not_fire_when_no_run_once if {
	tree := {"nodes": [{"type": "taskcall", "options": {}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.run_once(tree, node)
}
