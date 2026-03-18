#!/usr/bin/env bash
# helpers.sh — typing simulator and display helpers for the APME demo

set -euo pipefail

DEMO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TYPE_SPEED="${TYPE_SPEED:-0.04}"
PROMPT_CHAR="${PROMPT_CHAR:-$}"

# Print a bold section header with a full-width separator
section() {
    local title="$1"
    local cols
    cols=$(tput cols 2>/dev/null || echo 80)
    local line
    line=$(printf '─%.0s' $(seq 1 "$cols"))
    echo ""
    printf '\e[1;36m%s\e[0m\n' "$line"
    printf '\e[1;37m  %s\e[0m\n' "$title"
    printf '\e[1;36m%s\e[0m\n' "$line"
    echo ""
}

# Print a dimmed comment line
comment() {
    printf '\e[2;37m  # %s\e[0m\n' "$*"
}

# Pause for N seconds (default 3)
pause() {
    sleep "${1:-3}"
}

# Simulate typing a command, then execute it
type_cmd() {
    local cmd="$1"
    printf '\e[1;32m%s \e[0m' "$PROMPT_CHAR"
    for ((i = 0; i < ${#cmd}; i++)); do
        printf '%s' "${cmd:$i:1}"
        sleep "$TYPE_SPEED"
    done
    echo ""
    sleep 0.3
    eval "$cmd"
}

# Simulate typing a command but do NOT execute it (just show it)
type_show() {
    local cmd="$1"
    printf '\e[1;32m%s \e[0m' "$PROMPT_CHAR"
    for ((i = 0; i < ${#cmd}; i++)); do
        printf '%s' "${cmd:$i:1}"
        sleep "$TYPE_SPEED"
    done
    echo ""
    sleep 0.3
}

# Render a markdown file using python rich
render_slide() {
    local md_file="$1"
    python3 -c "
from rich.console import Console
from rich.markdown import Markdown
from pathlib import Path
console = Console(width=100)
md = Markdown(Path('$md_file').read_text())
console.print(md)
"
}

# Clear screen with a brief pause
fresh() {
    sleep 0.5
    clear
}

# Print a big ASCII banner
banner() {
    local text="$1"
    local cols
    cols=$(tput cols 2>/dev/null || echo 80)
    local pad=$(( (cols - ${#text} - 4) / 2 ))
    local border
    border=$(printf '═%.0s' $(seq 1 $(( ${#text} + 4 ))))
    local spaces
    spaces=$(printf ' %.0s' $(seq 1 "$pad"))
    echo ""
    printf '%s\e[1;33m╔%s╗\e[0m\n' "$spaces" "$border"
    printf '%s\e[1;33m║\e[0m  \e[1;37m%s\e[0m  \e[1;33m║\e[0m\n' "$spaces" "$text"
    printf '%s\e[1;33m╚%s╝\e[0m\n' "$spaces" "$border"
    echo ""
}
