# Integration tests for L015: Avoid Jinja in when

package apme.rules_test

import data.apme.rules

test_L015_fires_when_jinja_in_when if {
	tree := {"nodes": [{"type": "taskcall", "options": {"when": "{{ x }}"}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	v := rules.no_jinja_when(tree, node)
	v.rule_id == "L015"
}

test_L015_does_not_fire_when_no_jinja if {
	tree := {"nodes": [{"type": "taskcall", "options": {"when": "x"}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.no_jinja_when(tree, node)
}
