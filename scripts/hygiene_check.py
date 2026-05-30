#!/usr/bin/env python3
"""Lightweight repo-hygiene check (advisory, non-blocking by default).

Flags violations of the hygiene rules in AGENTS.md:
  - source files over the line-count cap
  - directories with too many sibling files (flat-dump fan-out)
  - major directories missing an index/README map

Usage:
  python scripts/hygiene_check.py            # report only, exit 0
  python scripts/hygiene_check.py --strict   # exit 1 if any violation

Counts only text/source files; skips .git, caches, the vector store, and data.
"""
import os
import sys
from pathlib import Path

LINE_CAP = 300          # hard refactor trigger
FANOUT_CAP = 10         # max sibling files before a dir should subdivide
SOURCE_EXT = {".py", ".sh"}
TEXT_EXT = SOURCE_EXT | {".md", ".yaml", ".yml", ".txt"}

SKIP_DIRS = {".git", "__pycache__", ".chroma", "data", ".github"}
# Directories expected to carry an index/README map.
MAJOR_DIRS = {"tools", "memory", "orchestration", "research", "scripts"}
INDEX_NAMES = {"readme.md", "index.md", "00_index.md"}


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def _iter_dirs(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        yield Path(dirpath), filenames


def check_file_sizes(root: Path):
    violations = []
    for dirpath, filenames in _iter_dirs(root):
        for name in filenames:
            if Path(name).suffix not in SOURCE_EXT:
                continue
            p = dirpath / name
            try:
                n = sum(1 for _ in p.open(encoding="utf-8", errors="replace"))
            except Exception:
                continue
            if n > LINE_CAP:
                rel = os.path.relpath(p, root)
                violations.append(f"[size] {rel}: {n} lines (cap {LINE_CAP})")
    return violations


def check_fanout(root: Path):
    violations = []
    for dirpath, filenames in _iter_dirs(root):
        text_files = [f for f in filenames if Path(f).suffix in TEXT_EXT]
        if len(text_files) > FANOUT_CAP:
            rel = os.path.relpath(dirpath, root)
            violations.append(
                f"[fanout] {rel}: {len(text_files)} files (cap {FANOUT_CAP}) — group into subdirs"
            )
    return violations


def check_maps(root: Path):
    violations = []
    for name in MAJOR_DIRS:
        d = root / name
        if not d.is_dir():
            continue
        has_index = any(
            (d / fn).exists() for fn in os.listdir(d)
            if fn.lower() in INDEX_NAMES
        )
        if not has_index:
            violations.append(f"[map] {name}/: no index/README map")
    return violations


def main(argv):
    strict = "--strict" in argv
    root = _root()
    violations = check_file_sizes(root) + check_fanout(root) + check_maps(root)
    if violations:
        print("Repo hygiene violations:")
        for v in violations:
            print("  " + v)
        print(f"\n{len(violations)} violation(s). See AGENTS.md > Code & repo hygiene.\n")
        return 1 if strict else 0
    print("Repo hygiene: OK — no violations.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
