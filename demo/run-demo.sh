#!/usr/bin/env bash
# run-demo.sh — APME asciinema demo driver
#
# Usage:
#   ./demo/run-demo.sh                                    # interactive
#   TERM=xterm-256color asciinema rec demo.cast -c ./demo/run-demo.sh  # record
#
set -euo pipefail

DEMO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$DEMO_DIR/.." && pwd)"

# shellcheck source=helpers.sh
source "$DEMO_DIR/helpers.sh"

PLAYBOOK_DIR="$DEMO_DIR/playbook"
SLIDES_DIR="$DEMO_DIR/slides"

WORK_DIR=$(mktemp -d)
cp -r "$PLAYBOOK_DIR"/* "$WORK_DIR/"
trap 'rm -rf "$WORK_DIR"' EXIT

# ── ACT 1: Overview ──────────────────────────────────────────────────
clear
banner "APME — Ansible Policy & Modernization Engine"
pause 3
render_slide "$SLIDES_DIR/01-overview.md"
pause 6

# ── ACT 2: Architecture ──────────────────────────────────────────────
fresh
banner "Architecture"
pause 2
render_slide "$SLIDES_DIR/02-architecture.md"
pause 6

# ── ACT 3: What it catches ──────────────────────────────────────────
fresh
banner "What Does APME Catch?"
pause 2
render_slide "$SLIDES_DIR/03-highlights.md"
pause 6

# ── ACT 4: The Terrible Playbook ─────────────────────────────────────
fresh
banner "The Terrible Playbook"
pause 2

comment "Every org has one. This is ours."
echo ""
pause 3

type_cmd "cat $WORK_DIR/site.yml"
pause 6

# ── ACT 5: Scan ──────────────────────────────────────────────────────
fresh
banner "Step 1: Scan"
pause 2

comment "Find everything wrong..."
echo ""
pause 2

type_cmd "apme-scan scan $WORK_DIR/"
pause 6

# ── ACT 6: Fix ───────────────────────────────────────────────────────
fresh
banner "Step 2: Fix"
pause 2

comment "Format, modernize, and auto-remediate."
comment "All deterministic. No AI needed."
echo ""
pause 3

type_cmd "apme-scan fix $WORK_DIR/ --apply --no-ai --max-passes 10"
pause 6

# ── ACT 7: Re-scan ───────────────────────────────────────────────────
fresh
banner "Step 3: Re-scan"
pause 2

comment "How many violations remain?"
echo ""
pause 2

type_cmd "apme-scan scan $WORK_DIR/"
pause 6

# ── ACT 8: Before / After ────────────────────────────────────────────
fresh
banner "Before"
pause 2
type_cmd "cat $PLAYBOOK_DIR/site.yml"
pause 6

fresh
banner "After"
pause 2
type_cmd "cat $WORK_DIR/site.yml"
pause 6

# ── ACT 9: Summary ───────────────────────────────────────────────────
fresh
banner "Results"
pause 2

# Count violations before and after
BEFORE=$(apme-scan scan "$PLAYBOOK_DIR/" --json 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin).get('count',0))")
AFTER=$(apme-scan scan "$WORK_DIR/" --json 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin).get('count',0))")
FIXED=$((BEFORE - AFTER))
if [ "$BEFORE" -gt 0 ]; then
    PCT=$(( FIXED * 100 / BEFORE ))
else
    PCT=0
fi

echo ""
printf '  \e[1;37mViolations before:  \e[1;31m%s\e[0m\n' "$BEFORE"
printf '  \e[1;37mViolations after:   \e[1;32m%s\e[0m\n' "$AFTER"
printf '  \e[1;37mAuto-fixed:         \e[1;33m%s  (%s%%)\e[0m\n' "$FIXED" "$PCT"
echo ""
pause 4

comment "Remaining violations are Tier 2 (AI-proposable) and Tier 3 (manual)."
comment "AI escalation should further improve remediation coverage."
echo ""
pause 4

# ── Closing ───────────────────────────────────────────────────────────
fresh
banner "APME — Ansible Policy & Modernization Engine"
echo ""
comment "90+ rules  |  20+ auto-fix transforms  |  5 validators"
comment "One command to scan. One command to fix."
echo ""
comment "github.com/ansible/apme"
echo ""
pause 6
