"""Resolve a module/plugin short name to FQCN using Ansible's loader in the current env.

Run with the venv's Python (which has ansible-core + collections on path):
  python -m apme_engine.collection_cache._fqcn_resolve <module_name>

Prints the resolved FQCN to stdout, or exits non-zero if not found.
"""

import sys


def main() -> None:
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: python -m apme_engine.collection_cache._fqcn_resolve <module_name>\n")
        sys.exit(2)
    name = sys.argv[1].strip()
    if not name:
        sys.exit(2)

    try:
        from ansible.plugins.loader import module_loader
    except ImportError as e:
        sys.stderr.write(f"ansible not available: {e}\n")
        sys.exit(3)

    ctx = module_loader.find_plugin_with_context(name)
    if ctx is None:
        sys.stderr.write(f"Module not found: {name}\n")
        sys.exit(1)

    # PluginResolutionContext: resolved_fqcn (ansible-core 2.14+)
    fqcn = getattr(ctx, "resolved_fqcn", None) or getattr(ctx, "plugin_resolved_name", None)
    if not fqcn and hasattr(ctx, "plugin"):
        plugin = ctx.plugin
        if plugin is not None:
            fqcn = getattr(plugin, "resolved_fqcn", None) or getattr(plugin, "_load_name", None)
    if not fqcn:
        fqcn = name
    print(fqcn)


if __name__ == "__main__":
    main()
