# Integration tests for L018: become_user should have a corresponding become

package apme.rules_test

import data.apme.rules

test_L018_fires_when_become_user_without_become_task if {
	tree := {"nodes": [{"type": "taskcall", "options": {"become_user": "root"}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	v := rules.partial_become_task(tree, node)
	v.rule_id == "L018"
}

test_L018_fires_when_become_user_without_become_play if {
	tree := {"nodes": [{"type": "playcall", "options": {"become_user": "root"}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	v := rules.partial_become_play(tree, node)
	v.rule_id == "L018"
}

test_L018_does_not_fire_when_become_present if {
	tree := {"nodes": [{"type": "taskcall", "options": {"become_user": "root", "become": true}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.partial_become_task(tree, node)
}
