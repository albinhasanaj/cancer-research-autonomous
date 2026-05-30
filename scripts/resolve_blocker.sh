#!/usr/bin/env bash
# resolve_blocker.sh <id> — human convenience to clear a blocker.
#
# Sets the blocker's status to resolved, moves it to blockers/resolved/, removes
# its id from .notified, and — if no open blockers remain — deletes .all-blocked
# (which auto-resumes a paused loop). Prints what it did.
set -u

ID="${1:-}"
if [ -z "$ID" ]; then
  echo "usage: scripts/resolve_blocker.sh <id>" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BLOCKERS="$ROOT/blockers"
RESOLVED="$BLOCKERS/resolved"
mkdir -p "$RESOLVED"

# Find the blocker file(s) for this id (match "<id>-*.md" or "<id>.md").
shopt -s nullglob 2>/dev/null || true
matches=("$BLOCKERS/$ID-"*.md "$BLOCKERS/$ID.md")
found=""
for f in "${matches[@]}"; do
  [ -f "$f" ] || continue
  found="$f"
  # Flip status: open -> resolved.
  sed -i.bak 's/^status: open$/status: resolved/' "$f" 2>/dev/null && rm -f "$f.bak"
  base="$(basename "$f")"
  mv "$f" "$RESOLVED/$base"
  echo "resolved: moved $base -> blockers/resolved/"
done

if [ -z "$found" ]; then
  echo "no open blocker file found for id '$ID' in blockers/" >&2
  exit 1
fi

# Remove the id from .notified tracking file.
NOTIFIED="$ROOT/.notified"
if [ -f "$NOTIFIED" ]; then
  grep -vxF "$ID" "$NOTIFIED" > "$NOTIFIED.tmp" 2>/dev/null || true
  mv "$NOTIFIED.tmp" "$NOTIFIED" 2>/dev/null || true
  echo "cleared '$ID' from .notified"
fi

# If no open blockers remain, lift the full-pause flag.
open_count=0
for f in "$BLOCKERS"/*.md; do
  [ -f "$f" ] || continue
  [ "$(basename "$f")" = "README.md" ] && continue
  if grep -qx 'status: open' "$f" 2>/dev/null; then
    open_count=$((open_count + 1))
  fi
done

if [ "$open_count" -eq 0 ] && [ -f "$ROOT/.all-blocked" ]; then
  rm -f "$ROOT/.all-blocked"
  echo "no open blockers remain — removed .all-blocked (loop will resume)"
else
  echo "$open_count open blocker(s) remaining"
fi
