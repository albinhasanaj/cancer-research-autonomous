"""ChromaDB persistent vector store over the research/ vault.

Semantic recall across iterations: research/**/*.md is chunked by paragraph and
upserted with a stable md5 id, so reindex() is idempotent. memory_search is the
tool the agent uses to recall prior notes.
"""
import hashlib
import os
from pathlib import Path

from tools.registry import tool

_COLLECTION = "research"


def _root() -> Path:
    return Path(os.environ.get("AGENT_ROOT", os.getcwd())).resolve()


def _client():
    import chromadb
    path = str(_root() / "memory" / ".chroma")
    return chromadb.PersistentClient(path=path)


def _collection():
    client = _client()
    return client.get_or_create_collection(name=_COLLECTION)


def reindex() -> int:
    """Walk research/**/*.md, chunk by paragraph, upsert. Returns chunk count."""
    root = _root()
    research = root / "research"
    if not research.is_dir():
        return 0
    col = _collection()
    ids, docs, metas = [], [], []
    for md in research.rglob("*.md"):
        rel = os.path.relpath(md, root)
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for chunk in [c.strip() for c in text.split("\n\n") if c.strip()]:
            cid = hashlib.md5(f"{rel}::{chunk}".encode("utf-8")).hexdigest()
            ids.append(cid)
            docs.append(chunk)
            metas.append({"path": rel, "chunk": chunk[:200]})
    if not ids:
        return 0
    col.upsert(ids=ids, documents=docs, metadatas=metas)
    return len(ids)


@tool(
    "memory_search",
    "Semantic search over the research/ knowledge graph. Returns top-k chunks with paths.",
    {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "k": {"type": "integer", "description": "Number of results (default 5)"},
        },
        "required": ["query"],
    },
)
def memory_search(query: str, k: int = 5) -> str:
    try:
        col = _collection()
        res = col.query(query_texts=[query], n_results=k)
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        if not docs:
            return "(no results)"
        out = []
        for doc, meta in zip(docs, metas):
            path = meta.get("path", "?") if isinstance(meta, dict) else "?"
            out.append(f"[{path}]\n{doc}")
        return "\n\n---\n\n".join(out)
    except Exception as e:
        return f"ERROR memory_search: {e}"
