# Integration tests for L025: Task/play name should start with uppercase

package apme.rules_test

import data.apme.rules

test_L025_fires_when_task_name_lowercase if {
	tree := {"nodes": [{"type": "taskcall", "name": "install package", "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	v := rules.name_casing(tree, node)
	v.rule_id == "L025"
}

test_L025_does_not_fire_when_task_name_uppercase if {
	tree := {"nodes": [{"type": "taskcall", "name": "Install package", "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.name_casing(tree, node)
}

test_L025_fires_when_play_name_lowercase if {
	tree := {"nodes": [{"type": "playcall", "name": "my play", "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	v := rules.name_casing(tree, node)
	v.rule_id == "L025"
}
