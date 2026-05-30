#!/usr/bin/env bash
# notify.sh "<message>" — alert the human about an escalation.
#
# Channels (all best-effort; a missing channel never fails the loop):
#   1. Always: loud console banner + a timestamped line in NEEDS_HUMAN.log
#   2. If $NOTIFY_WEBHOOK is set: POST {"content": "<message>"} (Discord/Slack)
#   3. If a desktop notifier exists: fire a desktop notification
#
# Exit code is always 0 — notification must never break an unattended run.
set -u

MSG="${1:-"(no message)"}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$ROOT/NEEDS_HUMAN.log"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1) Console banner + log (always).
printf '\n'
printf '########################################################\n'
printf '#  NEEDS HUMAN  (%s)\n' "$TS"
printf '#  %s\n' "$MSG"
printf '########################################################\n\n'
printf '%s | %s\n' "$TS" "$MSG" >> "$LOG" 2>/dev/null || true

# 2) Webhook (optional).
if [ -n "${NOTIFY_WEBHOOK:-}" ]; then
  # Escape backslashes and double quotes for JSON.
  esc=$(printf '%s' "$MSG" | sed 's/\\/\\\\/g; s/"/\\"/g')
  curl -s -m 10 -X POST -H 'Content-Type: application/json' \
    -d "{\"content\": \"$esc\"}" "$NOTIFY_WEBHOOK" >/dev/null 2>&1 || true
fi

# 3) Desktop notifier (optional, platform-dependent).
if command -v notify-send >/dev/null 2>&1; then
  notify-send "Research agent: NEEDS HUMAN" "$MSG" >/dev/null 2>&1 || true
elif command -v terminal-notifier >/dev/null 2>&1; then
  terminal-notifier -title "Research agent: NEEDS HUMAN" -message "$MSG" >/dev/null 2>&1 || true
elif command -v osascript >/dev/null 2>&1; then
  osascript -e "display notification \"$MSG\" with title \"Research agent: NEEDS HUMAN\"" >/dev/null 2>&1 || true
fi

exit 0
