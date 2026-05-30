"""self_check.py — capability health probe for the Ralph loop.

Exercises each core capability and reports PASS/FAIL/WARN.
With --queue, appends [HEALTH] items to research/open_questions.md
for any FAILing probes (deduplicated).

Usage:
    python scripts/self_check.py           # report only
    python scripts/self_check.py --queue   # report + queue health items on FAIL
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# Ensure repo root is on sys.path so `memory` and `tools` are importable
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Safe print that never crashes on encoding errors
def _print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))


# ---------------------------------------------------------------------------
# Result accumulator
# ---------------------------------------------------------------------------

_results: list[tuple[str, str, str]] = []  # (status, name, detail)


def _record(status: str, name: str, detail: str) -> None:
    _results.append((status, name, detail))
    _print(f"[{status}] {name} — {detail}")


# ---------------------------------------------------------------------------
# Probe 1: memory_search
# ---------------------------------------------------------------------------

def probe_memory_search() -> None:
    try:
        from memory.vector_store import memory_search  # type: ignore
        r = memory_search("cancer", 3)
        if not r or r.strip() == "(no results)" or r.startswith("ERROR"):
            _record("FAIL", "memory_search",
                    f"returned unusable result: {r[:120]!r}")
        else:
            _record("PASS", "memory_search",
                    f"returned {len(r)} chars — first 80: {r[:80]!r}")
    except Exception as exc:
        _record("FAIL", "memory_search", f"exception: {exc}")


# ---------------------------------------------------------------------------
# Probe 2: pubmed_search
# ---------------------------------------------------------------------------

def probe_pubmed_search() -> None:
    try:
        from tools.pubmed_tool import pubmed_search  # type: ignore
        r = pubmed_search("TP53", 2)
        if not r or "(no results)" in r or r.startswith("ERROR"):
            _record("FAIL", "pubmed_search",
                    f"returned unusable result: {r[:120]!r}")
        else:
            # Format is "{pmid} | {title}" — check for the " | " separator
            lines = [l for l in r.splitlines() if " | " in l]
            if not lines:
                _record("FAIL", "pubmed_search",
                        f"no 'id | title' lines found: {r[:120]!r}")
            else:
                _record("PASS", "pubmed_search",
                        f"{len(lines)} result line(s) — first: {lines[0][:80]!r}")
    except Exception as exc:
        _record("FAIL", "pubmed_search", f"exception: {exc}")


# ---------------------------------------------------------------------------
# Probe 3: data tools registered
# ---------------------------------------------------------------------------

REQUIRED_TOOLS = [
    "cbioportal_studies", "cbioportal_gene_mutations", "cbioportal_clinical",
    "depmap_query", "depmap_compare",
    "geo_search", "geo_summary",
    "gdc_projects", "gdc_gene_mutations", "gdc_case_count",
]


def probe_tool_registry() -> None:
    try:
        from tools import registry  # type: ignore
        registry.discover()
        present = set(registry.names())
        missing = [t for t in REQUIRED_TOOLS if t not in present]
        if missing:
            _record("FAIL", "tool_registry",
                    f"missing tools: {', '.join(missing)}")
        else:
            _record("PASS", "tool_registry",
                    f"all {len(REQUIRED_TOOLS)} required tools registered")
    except Exception as exc:
        _record("FAIL", "tool_registry", f"exception: {exc}")


# ---------------------------------------------------------------------------
# Probe 4: scientific stack imports
# ---------------------------------------------------------------------------

STACK_IMPORTS = [
    ("numpy",          "numpy"),
    ("scipy",          "scipy"),
    ("pandas",         "pandas"),
    ("statsmodels",    "statsmodels.api"),
    ("sklearn",        "sklearn"),
    ("Bio",            "Bio"),
    ("lifelines",      "lifelines"),
    ("gseapy",         "gseapy"),
    ("pingouin",       "pingouin"),
    ("matplotlib",     "matplotlib"),
]


def probe_scientific_stack() -> None:
    failed = []
    for label, module in STACK_IMPORTS:
        try:
            __import__(module)
        except ImportError:
            failed.append(label)
    if failed:
        _record("FAIL", "scientific_stack",
                f"failed imports: {', '.join(failed)}")
    else:
        _record("PASS", "scientific_stack",
                f"all {len(STACK_IMPORTS)} packages imported successfully")


# ---------------------------------------------------------------------------
# Probe 5: API keys
# ---------------------------------------------------------------------------

def probe_api_keys() -> None:
    # Required keys: PASS if present, WARN if absent (never FAIL — .env may not
    # be loaded when running standalone; run_loop.sh loads it before calling us).
    required = ["OPENAI_API_KEY", "XAI_API_KEY"]
    optional = ["NCBI_API_KEY", "ANTHROPIC_API_KEY"]

    issues: list[str] = []
    any_warn = False

    for key in required:
        val = os.environ.get(key, "")
        if not val:
            issues.append(f"WARN {key} absent")
            any_warn = True
        else:
            issues.append(f"PASS {key} present")

    for key in optional:
        val = os.environ.get(key, "")
        if not val:
            issues.append(f"WARN {key} absent (optional)")

    summary = "; ".join(issues)
    if any_warn:
        _record("WARN", "api_keys", summary)
    else:
        _record("PASS", "api_keys", summary)


# ---------------------------------------------------------------------------
# Self-heal: queue [HEALTH] items into research/open_questions.md
# ---------------------------------------------------------------------------

def _open_questions_path() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "research", "open_questions.md")


HEALTH_MESSAGES: dict[str, str] = {
    "memory_search": (
        "[HEALTH] self_check: memory_search returned no results or error — "
        "memory/.chroma may be unbuilt or corrupt; investigate "
        "memory/vector_store.py reindex() and the loop's reindex step; "
        "verify with `python scripts/self_check.py`."
    ),
    "pubmed_search": (
        "[HEALTH] self_check: pubmed_search returned no results or error — "
        "check network connectivity, NCBI API endpoint, and tools/pubmed_tool.py; "
        "verify with `python scripts/self_check.py`."
    ),
    "tool_registry": (
        "[HEALTH] self_check: tool_registry missing one or more required tools — "
        "run `from tools import registry; registry.discover(); print(registry.names())` "
        "to diagnose; check tools/*.py for missing @tool registrations; "
        "verify with `python scripts/self_check.py`."
    ),
    "scientific_stack": (
        "[HEALTH] self_check: scientific_stack imports failed — "
        "run `pip install -r requirements.txt` to restore missing packages; "
        "verify with `python scripts/self_check.py`."
    ),
    "api_keys": (
        "[HEALTH] self_check: api_keys — required API key(s) absent from environment; "
        "check .env file has OPENAI_API_KEY and XAI_API_KEY set; "
        "verify with `python scripts/self_check.py`."
    ),
}


def queue_health_items() -> None:
    """Append [HEALTH] items for failed probes, skipping duplicates."""
    path = _open_questions_path()
    try:
        existing = open(path, encoding="utf-8").read()
    except Exception as exc:
        _print(f"[self_check] WARNING: could not read open_questions.md: {exc}")
        return

    to_append: list[str] = []
    for status, name, _detail in _results:
        if status != "FAIL":
            continue
        # Dedup: skip if a [HEALTH] line with this probe name already exists
        if f"self_check: {name}" in existing:
            _print(f"[self_check] dedup: [HEALTH] for '{name}' already in open_questions.md")
            continue
        msg = HEALTH_MESSAGES.get(name)
        if not msg:
            msg = (
                f"[HEALTH] self_check: {name} probe failed — "
                f"investigate and verify with `python scripts/self_check.py`."
            )
        to_append.append(f"\n- [ ] {msg}")

    if not to_append:
        _print("[self_check] no new [HEALTH] items to append")
        return

    try:
        with open(path, "a", encoding="utf-8") as f:
            # Ensure we start on a fresh line
            if not existing.endswith("\n"):
                f.write("\n")
            if "## Self-check health items" not in existing:
                f.write("\n## Self-check health items\n")
            for item in to_append:
                f.write(item)
                f.write("\n")
        _print(f"[self_check] appended {len(to_append)} [HEALTH] item(s) to open_questions.md")
    except Exception as exc:
        _print(f"[self_check] WARNING: could not write open_questions.md: {exc}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> int:
    queue = "--queue" in sys.argv

    _print("=" * 60)
    _print("self_check — Ralph loop capability health report")
    _print("=" * 60)

    probe_memory_search()
    probe_pubmed_search()
    probe_tool_registry()
    probe_scientific_stack()
    probe_api_keys()

    _print("=" * 60)
    fails = [r for r in _results if r[0] == "FAIL"]
    warns = [r for r in _results if r[0] == "WARN"]
    _print(f"Summary: {len(_results)} probes | "
           f"{len(_results) - len(fails) - len(warns)} PASS | "
           f"{len(warns)} WARN | {len(fails)} FAIL")

    if queue:
        _print("-" * 60)
        _print("[self_check] --queue: checking for items to add to open_questions.md")
        queue_health_items()

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
