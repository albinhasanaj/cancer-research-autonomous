#!/usr/bin/env bash
# Ralph loop (FALLBACK PATH — raw-API backend).
# Drives the provider-API iteration directly. The PRIMARY execution model is
# Copilot CLI driving the loop; use this only when running without Copilot.
#
# Each pass is a FRESH process with a clean context window.
# Nothing persists in-memory between iterations; all state lives on disk + git.
#
# Human-in-the-loop: after each pass it notifies on NEW open blockers
# (non-blocking) and pauses only if `.all-blocked` exists at repo root.
#
# Env:
#   MAX_ITERS  number of iterations (0 = unlimited, default 0)
#   SLEEP      seconds to sleep between passes (default 5)
#
# This does NOT auto-start on import; you must run it explicitly.
set -u

cd "$(dirname "$0")/.." || exit 1
ROOT="$(pwd)"

MAX_ITERS="${MAX_ITERS:-0}"
SLEEP="${SLEEP:-5}"
NOTIFY="$ROOT/scripts/notify.sh"
NOTIFIED="$ROOT/.notified"

if [ ! -d "$ROOT/.git" ]; then
  git init
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
    echo "#  [ralph] PAUSED — waiting for human (.all-blocked)  "
    echo "#  Resolve a blocker (scripts/resolve_blocker.sh <id>)"
    echo "#  or delete .all-blocked to resume.                  "
    echo "######################################################"
    while [ -f "$ROOT/.all-blocked" ]; do
      sleep 60
    done
    echo "[ralph] .all-blocked cleared — resuming."
  fi
}

i=0
while true; do
  wait_if_fully_blocked

  i=$((i + 1))
  echo "=============================="
  echo "[ralph] iteration $i  ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
  echo "=============================="

  python -m api_backend.iteration
  rc=$?

  if [ $rc -ne 0 ]; then
    echo "[ralph] iteration exited non-zero ($rc); sleeping 30s and continuing"
    sleep 30
    continue
  fi

  # Commit if the working tree changed (episodic memory).
  if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -m "ralph: iteration $i ($(date -u +%Y-%m-%dT%H:%M:%SZ))" >/dev/null 2>&1
    echo "[ralph] committed iteration $i"
  else
    echo "[ralph] no changes to commit"
  fi

  # Human-in-the-loop: notify on new blockers (non-blocking), pause if fully blocked.
  notify_new_blockers
  wait_if_fully_blocked

  if [ "$MAX_ITERS" -ne 0 ] && [ "$i" -ge "$MAX_ITERS" ]; then
    echo "[ralph] reached MAX_ITERS=$MAX_ITERS; stopping"
    break
  fi

  sleep "$SLEEP"
done
