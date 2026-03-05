package apme.rules

import future.keywords.if
import future.keywords.in

test_R118_inbound_transfer if {
	inp := {"hierarchy": [{"root_key": "playbook:pb.yml", "root_type": "playbook", "nodes": [
		{
			"type": "taskcall",
			"key": "task1",
			"module": "ansible.builtin.get_url",
			"name": "Download artifact",
			"file": "pb.yml",
			"line": [5, 8],
			"annotations": [{"type": "risk_annotation", "key": "", "risk_type": "inbound_transfer", "src": {"type": "url", "value": "https://example.com/pkg.tar.gz", "is_mutable": false}, "dest": {"type": "file", "value": "/tmp/pkg.tar.gz", "is_mutable": false}}],
			"options": {},
			"module_options": {},
		},
	]}]}
	result := violations with input as inp
	count(result) == 1
	some v in result
	v.rule_id == "R118"
	contains(v.message, "example.com")
}

test_R118_no_flag_non_inbound if {
	inp := {"hierarchy": [{"root_key": "playbook:pb.yml", "root_type": "playbook", "nodes": [
		{
			"type": "taskcall",
			"key": "task1",
			"module": "ansible.builtin.command",
			"name": "Run something",
			"file": "pb.yml",
			"line": [5, 8],
			"annotations": [{"type": "risk_annotation", "key": "", "risk_type": "cmd_exec", "command": "whoami"}],
			"options": {},
			"module_options": {},
		},
	]}]}
	result := violations with input as inp
	not any_R118(result)
}

any_R118(result) if {
	some v in result
	v.rule_id == "R118"
}
