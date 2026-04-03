# Tests for L106: set_fact + loop + when anti-pattern

package apme.rules_test

import data.apme.rules

# --- Positive cases (should fire) ---

test_L106_fires_fqcn_loop_when if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.set_fact", "module_options": {"running": "{{ running | default([]) + [item] }}"}, "options": {"loop": "{{ all_services }}", "when": "item.state == 'running'"}, "line": [10], "key": "k", "file": "play.yml"}]}
	node := tree.nodes[0]
	v := rules.set_fact_loop_when(tree, node)
	v.rule_id == "L106"
}

test_L106_fires_short_name_with_items_when if {
	tree := {"nodes": [{"type": "taskcall", "module": "set_fact", "module_options": {"result": "{{ result | default([]) + [item] }}"}, "options": {"with_items": "{{ packages }}", "when": "item.installed"}, "line": [5], "key": "k", "file": "play.yml"}]}
	node := tree.nodes[0]
	v := rules.set_fact_loop_when(tree, node)
	v.rule_id == "L106"
}

test_L106_fires_legacy_name_with_dict_when if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.legacy.set_fact", "module_options": {"enabled": "{{ enabled | default({}) | combine({item.key: item.value}) }}"}, "options": {"with_dict": {"a": 1}, "when": "item.value | bool"}, "line": [15], "key": "k", "file": "play.yml"}]}
	node := tree.nodes[0]
	v := rules.set_fact_loop_when(tree, node)
	v.rule_id == "L106"
}

test_L106_fires_with_together_when if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.set_fact", "module_options": {"merged": "val"}, "options": {"with_together": [["a"], ["b"]], "when": "item.0"}, "line": [20], "key": "k", "file": "play.yml"}]}
	node := tree.nodes[0]
	v := rules.set_fact_loop_when(tree, node)
	v.rule_id == "L106"
}

# --- Negative cases (should NOT fire) ---

test_L106_no_fire_loop_without_when if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.set_fact", "module_options": {"upper": "{{ upper | default([]) + [item | upper] }}"}, "options": {"loop": ["hello", "world"]}, "line": [1], "key": "k", "file": "play.yml"}]}
	node := tree.nodes[0]
	not rules.set_fact_loop_when(tree, node)
}

test_L106_no_fire_when_without_loop if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.set_fact", "module_options": {"db_host": "replica.example.com"}, "options": {"when": "use_replica | default(false)"}, "line": [1], "key": "k", "file": "play.yml"}]}
	node := tree.nodes[0]
	not rules.set_fact_loop_when(tree, node)
}

test_L106_no_fire_wrong_module if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.debug", "module_options": {"msg": "{{ item }}"}, "options": {"loop": "{{ services }}", "when": "item.state == 'running'"}, "line": [1], "key": "k", "file": "play.yml"}]}
	node := tree.nodes[0]
	not rules.set_fact_loop_when(tree, node)
}

test_L106_no_fire_plain_set_fact if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.set_fact", "module_options": {"app_env": "production"}, "options": {}, "line": [1], "key": "k", "file": "play.yml"}]}
	node := tree.nodes[0]
	not rules.set_fact_loop_when(tree, node)
}
