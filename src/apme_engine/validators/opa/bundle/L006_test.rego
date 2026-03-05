# Integration tests for L006: Command used in place of preferred module

package apme.rules_test

import data.apme.rules

# L006 needs data.apme.ansible.command_to_module and cmd_shell_modules; tested with bundle
test_L006_does_not_fire_for_plain_task if {
	tree := {"nodes": [{"type": "taskcall", "module": "ansible.builtin.copy", "module_options": {}, "line": [1], "key": "k", "file": "f.yml"}]}
	node := tree.nodes[0]
	not rules.command_instead_of_module(tree, node)
}
