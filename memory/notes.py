"""write_note tool — Obsidian-style notes with YAML frontmatter + wikilinks.

Lives in the memory package (not the auto-discovered tools package), so its @tool
registers when memory.notes is imported. On the Copilot path call it from the
shell, e.g. `python -c "from memory.notes import write_note; print(write_note(...))"`.
"""
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from tools.registry import tool

_KIND_DIRS = {
    "hypothesis": "research/hypotheses",
    "finding": "research/findings",
    "literature": "research/literature",
}


def _root() -> Path:
    return Path(os.environ.get("AGENT_ROOT", os.getcwd())).resolve()


def _slugify(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s or "note"


@tool(
    "write_note",
    "Write a dated Obsidian note (kind: hypothesis|finding|literature) with frontmatter. "
    "Use [[wikilinks]] in body_md to connect notes. For findings/hypotheses set "
    "confidence (speculative|tentative|supported|strong) and falsifier (the real "
    "external observation that would prove the claim wrong) — see the epistemics skill.",
    {
        "type": "object",
        "properties": {
            "kind": {"type": "string", "enum": ["hypothesis", "finding", "literature"]},
            "title": {"type": "string"},
            "body_md": {"type": "string", "description": "Markdown body; use [[wikilinks]]"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "status": {"type": "string", "description": "e.g. draft, kept, demoted, rejected"},
            "confidence": {
                "type": "string",
                "enum": ["speculative", "tentative", "supported", "strong"],
                "description": "Epistemic confidence; a sim with no external falsifier is at most 'speculative'.",
            },
            "falsifier": {
                "type": "string",
                "description": "The real external observation that would prove this wrong. Empty ⇒ hypothesis, not a result.",
            },
        },
        "required": ["kind", "title", "body_md"],
    },
)
def write_note(kind: str, title: str, body_md: str, tags=None, status: str = "draft",
               confidence: str = "", falsifier: str = "") -> str:
    if kind not in _KIND_DIRS:
        return f"ERROR: invalid kind '{kind}'; must be one of {list(_KIND_DIRS)}"
    root = _root()
    now = datetime.now(timezone.utc)
    date = now.strftime("%Y-%m-%d")
    folder = root / _KIND_DIRS[kind]
    folder.mkdir(parents=True, exist_ok=True)
    slug = _slugify(title)
    filename = f"{date}-{slug}.md"
    path = folder / filename
    tags = tags or []
    tags_yaml = "[" + ", ".join(tags) + "]"
    # Findings/hypotheses carry epistemic metadata (see epistemics skill). Default
    # confidence to 'speculative' so an unset value never reads as trustworthy.
    epistemic_yaml = ""
    if kind in ("finding", "hypothesis"):
        conf = confidence or "speculative"
        epistemic_yaml = f"confidence: {conf}\nfalsifier: {falsifier}\n"
    frontmatter = (
        "---\n"
        f"title: {title}\n"
        f"kind: {kind}\n"
        f"status: {status}\n"
        f"created: {now.isoformat()}\n"
        f"tags: {tags_yaml}\n"
        f"{epistemic_yaml}"
        "---\n\n"
    )
    path.write_text(frontmatter + body_md + "\n", encoding="utf-8")
    rel = os.path.relpath(path, root)
    return f"wrote note {rel}"
