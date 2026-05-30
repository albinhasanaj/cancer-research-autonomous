#!/usr/bin/env bash
# Ralph loop: each pass is a FRESH process with a clean context window.
# Nothing persists in-memory between iterations; all state lives on disk + git.
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

if [ ! -d "$ROOT/.git" ]; then
  git init
fi

i=0
while true; do
  i=$((i + 1))
  echo "=============================="
  echo "[ralph] iteration $i  ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
  echo "=============================="

  python -m agentic_loops.iteration
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

  if [ "$MAX_ITERS" -ne 0 ] && [ "$i" -ge "$MAX_ITERS" ]; then
    echo "[ralph] reached MAX_ITERS=$MAX_ITERS; stopping"
    break
  fi

  sleep "$SLEEP"
done
