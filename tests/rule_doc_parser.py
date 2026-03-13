"""Parse rule description .md files (frontmatter + Example: violation / Example: pass) for integration tests."""

import re
from pathlib import Path

import yaml


def parse_rule_doc(md_path: str | Path) -> dict[str, object] | None:
    """
    Parse a rule .md file. Returns dict with:
      - rule_id: str
      - validator: "native" | "opa"
      - description: str (optional)
      - examples: list of { "expect_violation": bool, "yaml": str }
    Returns None if frontmatter is missing or invalid.
    """
    path = Path(md_path)
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")

    # Frontmatter: between first --- and second ---
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not fm_match:
        return None
    try:
        front = yaml.safe_load(fm_match.group(1))
    except Exception:
        return None
    if not isinstance(front, dict) or "rule_id" not in front:
        return None

    rule_id = str(front.get("rule_id", "")).strip()
    validator = (front.get("validator") or "native").strip().lower()
    if validator not in ("native", "opa", "ansible"):
        validator = "native"
    description = str(front.get("description") or "").strip()

    # Examples: ### Example: violation / ### Example: pass, then fenced block
    rest = text[fm_match.end() :]
    examples = []
    for kind, expect in [("violation", True), ("pass", False)]:
        pattern = rf"###\s+Example:\s+{re.escape(kind)}\s*\n+"
        m = re.search(pattern, rest, re.IGNORECASE)
        if not m:
            continue
        after = rest[m.end() :]
        # Next fenced code block (```yaml or ```)
        block_match = re.match(r"```(?:yaml)?\s*\n(.*?)```", after, re.DOTALL)
        if not block_match:
            continue
        yaml_content = block_match.group(1).strip()
        if yaml_content:
            examples.append({"expect_violation": expect, "yaml": yaml_content})

    return {
        "rule_id": rule_id,
        "validator": validator,
        "description": description,
        "examples": examples,
    }


def discover_rule_docs(
    native_rules_dir: str | Path,
    opa_bundle_dir: str | Path,
    ansible_rules_dir: str | Path | None = None,
) -> list[tuple[str, dict[str, object]]]:
    """
    Discover all rule .md files and parse them. Returns list of (file_path, parsed_doc).
    Native: *.md next to .py in native_rules_dir (exclude *_test.md, README).
    OPA: *.md in opa_bundle_dir (exclude README, _helpers).
    Ansible: *.md in ansible_rules_dir (if provided).
    """
    out = []
    native_dir = Path(native_rules_dir)
    opa_dir = Path(opa_bundle_dir)

    for path in native_dir.glob("*.md"):
        if path.name.endswith("_test.md") or path.name.startswith("_"):
            continue
        if path.name.lower() == "readme.md":
            continue
        doc = parse_rule_doc(path)
        if doc:
            out.append((str(path), doc))

    for path in opa_dir.glob("*.md"):
        if path.name.startswith("_") or path.name.lower() == "readme.md":
            continue
        doc = parse_rule_doc(path)
        if doc:
            out.append((str(path), doc))

    if ansible_rules_dir:
        ansible_dir = Path(ansible_rules_dir)
        if ansible_dir.is_dir():
            for path in ansible_dir.glob("*.md"):
                if path.name.startswith("_") or path.name.lower() == "readme.md":
                    continue
                doc = parse_rule_doc(path)
                if doc:
                    out.append((str(path), doc))

    return out
