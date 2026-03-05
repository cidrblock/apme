# Shared helpers for APME OPA rules. Used by L004, L006, L012, L013, L017, L020, L021.
# Package must match rule files so they can reference these definitions.

package apme.rules

short_module_name(module) := short if {
	parts := split(module, ".")
	count(parts) > 0
	short := parts[count(parts) - 1]
}

is_number(x) if {
	count(numbers.range(x, x)) >= 0
}

cmd_shell_modules[m] if {
	m := data.apme.ansible.command_shell_modules[_]
}

package_modules[m] if {
	m := data.apme.ansible.package_modules[_]
}

copy_template_modules[m] if {
	m := data.apme.ansible.copy_template_modules[_]
}

file_permission_modules[m] if {
	m := data.apme.ansible.file_permission_modules[_]
}
