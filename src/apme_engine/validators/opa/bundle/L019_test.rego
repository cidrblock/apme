# Integration tests for L019: Playbook should have .yml or .yaml extension

package apme.rules_test

import data.apme.rules

test_L019_fires_when_playbook_bad_extension if {
	tree_bad := {"root_type": "playbook", "root_path": "site", "root_key": "site"}
	v := rules.playbook_extension(tree_bad)
	v.rule_id == "L019"
}

test_L019_does_not_fire_when_yml_extension if {
	tree := {"root_type": "playbook", "root_path": "site.yml", "root_key": "site"}
	not rules.playbook_extension(tree)
}
