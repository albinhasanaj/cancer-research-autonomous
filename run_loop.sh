#!/usr/bin/env bash
# Ralph loop (PRIMARY PATH — Copilot CLI is the brain).
#
# Each pass spawns a FRESH, non-interactive `copilot` process with a clean
# context window. Nothing persists in-memory between iterations; all state lives
# on disk + git history. The agent reads AGENTS.md and performs exactly ONE
# iteration of the protocol (orient -> select -> act -> criticise -> record),
# then exits. This script commits between iterations and handles the
# human-in-the-loop escalation (notify on new blockers; pause on .all-blocked).
#
# Env:
#   MAX_ITERS      number of iterations (0 = unlimited, default 0)
#   SLEEP          seconds to sleep between passes (default 5)
#   COPILOT_MODEL  optional model override passed to `copilot --model`
#
# Windows note: run via Git Bash, e.g.
#   "C:\Program Files\Git\bin\bash.exe" run_loop.sh
#
# This does NOT auto-start on import; you must run it explicitly.
set -u

cd "$(dirname "$0")" || exit 1
ROOT="$(pwd)"

MAX_ITERS="${MAX_ITERS:-0}"
SLEEP="${SLEEP:-5}"
NOTIFY="$ROOT/scripts/notify.sh"
NOTIFIED="$ROOT/.notified"

PROMPT="Read AGENTS.md and do exactly one iteration of the protocol, then exit."

# Export API keys from .env so Copilot's shell tools and any research code see
# them (OPENAI_API_KEY, XAI_API_KEY, ...). .env is git-ignored.
if [ -f "$ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ROOT/.env"
  set +a
fi

if ! command -v copilot >/dev/null 2>&1; then
  echo "[run_loop] ERROR: 'copilot' CLI not found on PATH." >&2
  exit 127
fi

if [ ! -d "$ROOT/.git" ]; then
  git init
fi

# Assemble copilot flags. --allow-all = tools + paths + urls (full autonomy,
# required for unattended non-interactive runs). --no-color keeps logs clean.
COPILOT_ARGS=(--prompt "$PROMPT" --allow-all --no-color)
if [ -n "${COPILOT_MODEL:-}" ]; then
  COPILOT_ARGS+=(--model "$COPILOT_MODEL")
fi

# Notify the human once per NEW open blocker (id not yet in .notified).
notify_new_blockers() {
  [ -d "$ROOT/blockers" ] || return 0
  touch "$NOTIFIED"
  for f in "$ROOT"/blockers/*.md; do
    [ -f "$f" ] || continue
    [ "$(basename "$f")" = "README.md" ] && continue
    grep -qx 'status: open' "$f" 2>/dev/null || continue
    id=$(sed -n 's/^id:[[:space:]]*//p' "$f" | head -n1)
    [ -n "$id" ] || continue
    if ! grep -qxF "$id" "$NOTIFIED" 2>/dev/null; then
      bash "$NOTIFY" "New blocker [$id] — see blockers/$(basename "$f")" || true
      echo "$id" >> "$NOTIFIED"
    fi
  done
}

# Block while .all-blocked exists; the human removes it (or resolve_blocker.sh).
wait_if_fully_blocked() {
  if [ -f "$ROOT/.all-blocked" ]; then
    bash "$NOTIFY" "FULLY BLOCKED — all open work needs you. See blockers/." || true
    echo "######################################################"
    echo "#  [run_loop] PAUSED — waiting for human (.all-blocked)"
    echo "#  Resolve a blocker (scripts/resolve_blocker.sh <id>) "
    echo "#  or delete .all-blocked to resume.                   "
    echo "######################################################"
    while [ -f "$ROOT/.all-blocked" ]; do
      sleep 60
    done
    echo "[run_loop] .all-blocked cleared — resuming."
  fi
}

i=0
while true; do
  wait_if_fully_blocked

  i=$((i + 1))
  echo "=============================="
  echo "[run_loop] iteration $i  ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
  echo "=============================="

  # Fresh Copilot process per iteration — clean context window every pass.
  copilot "${COPILOT_ARGS[@]}"
  rc=$?

  if [ $rc -ne 0 ]; then
    echo "[run_loop] copilot exited non-zero ($rc); sleeping 30s and continuing"
    sleep 30
    continue
  fi

  # Commit if the working tree changed (episodic memory). Stale pre-refactor
  # duplicates are git-ignored, so `git add -A` will not re-track them.
  if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -m "ralph: iteration $i ($(date -u +%Y-%m-%dT%H:%M:%SZ))" >/dev/null 2>&1
    echo "[run_loop] committed iteration $i"
  else
    echo "[run_loop] no changes to commit"
  fi

  # Human-in-the-loop: notify on new blockers (non-blocking), pause if fully blocked.
  notify_new_blockers
  wait_if_fully_blocked

  if [ "$MAX_ITERS" -ne 0 ] && [ "$i" -ge "$MAX_ITERS" ]; then
    echo "[run_loop] reached MAX_ITERS=$MAX_ITERS; stopping"
    break
  fi

  sleep "$SLEEP"
done
