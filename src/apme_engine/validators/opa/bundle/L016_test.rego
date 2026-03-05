# Integration tests for L016: pause without seconds/minutes prompts for input

package apme.rules_test

import data.apme.rules

test_L016_fires_when_pause_no_seconds if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.pause", "module_options": {}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	v := rules.no_prompting(tree, node)
	v.rule_id == "L016"
}

test_L016_does_not_fire_when_seconds_present if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.pause", "module_options": {"seconds": 1}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.no_prompting(tree, node)
}
