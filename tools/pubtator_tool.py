"""PubTator3 tools: turn PubMed abstracts into normalized, graph-linkable facts.

NCBI PubTator3 supplies pre-computed, normalized biomedical entity annotations
(gene/disease/chemical/variant/species linked to concept IDs) and curated
relations for all of PubMed — no local NER model, no GPU, no inference cost.

This is the upgrade for the literature loop: `pubmed_search` finds PMIDs, then
`pubtator_annotate` returns those papers' entities as concept IDs (NCBI Gene,
MeSH, …) that merge cleanly into a knowledge graph, plus the relations PubTator
extracted. `pubtator_entity` normalizes a free-text name to its concept ID.

No API key. Base: https://www.ncbi.nlm.nih.gov/research/pubtator3-api
All functions return plain strings; errors surface as "ERROR <name>: ..." so an
iteration never crashes.
"""
import json
import time
import urllib.parse
import urllib.request

from tools.registry import tool

_BASE = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api"
_HEADERS = {"User-Agent": "research-agent/1.0"}
_SLEEP = 0.34
_TRUNC = 18_000


def _get(path: str, timeout: int = 50) -> bytes:
    req = urllib.request.Request(_BASE + path, headers=_HEADERS)
    time.sleep(_SLEEP)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


@tool(
    "pubtator_entity",
    (
        "Normalize a free-text biomedical name to its PubTator/standard concept "
        "ID(s) (NCBI Gene id, MeSH id, etc.) with entity type. Use to turn a gene/"
        "disease/chemical mention into a stable id before linking it in notes or a "
        "knowledge graph, or to disambiguate a name."
    ),
    {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Entity name, e.g. 'BRCA1' or 'olaparib'"},
            "limit": {"type": "integer", "description": "Max candidates (default 5)"},
        },
        "required": ["name"],
    },
)
def pubtator_entity(name: str, limit: int = 5) -> str:
    try:
        q = urllib.parse.urlencode({"query": name, "limit": limit})
        rows = json.loads(_get(f"/entity/autocomplete/?{q}"))
        if not rows:
            return f"No PubTator concept found for '{name}'."
        lines = [f"PubTator concepts for '{name}':",
                 f"{'type':>9}  {'db':>10}  {'id':<14} name"]
        for r in rows:
            lines.append(
                f"{r.get('biotype', '?'):>9}  {r.get('db', '?'):>10}  "
                f"{str(r.get('db_id', '?')):<14} {r.get('name', '?')}"
                + (f"  ({r['description']})" if r.get('description') else "")
            )
        return "\n".join(lines)[:_TRUNC]
    except Exception as e:
        return f"ERROR pubtator_entity: {e}"


def _doc_annotations(doc: dict):
    """Yield (type, text, identifier) for every annotation in a BioC doc."""
    for p in doc.get("passages", []):
        for a in p.get("annotations", []):
            infons = a.get("infons", {})
            yield infons.get("type", "?"), a.get("text", ""), infons.get("identifier")


def _format_relation(rel: dict) -> str | None:
    """Render a PubTator relation entry generically (shape varies by release)."""
    if not isinstance(rel, dict):
        return None
    infons = rel.get("infons", rel)
    rtype = infons.get("type") or rel.get("type")
    # role/entity fields appear under several keys across releases
    parts = [v for k, v in infons.items()
             if k not in ("type",) and isinstance(v, str) and v]
    if rtype and parts:
        return f"{rtype}: " + " — ".join(parts)
    return None


@tool(
    "pubtator_annotate",
    (
        "Fetch PubTator3's pre-computed, normalized entity annotations (and any "
        "extracted relations) for one or more PMIDs. Returns genes/diseases/"
        "chemicals/variants with concept IDs, so abstracts become graph-linkable "
        "facts instead of free text. Pair with pubmed_search to enrich hits."
    ),
    {
        "type": "object",
        "properties": {
            "pmids": {
                "type": "string",
                "description": "Comma-separated PMIDs, e.g. '21720365,26947069' (up to ~100)",
            },
        },
        "required": ["pmids"],
    },
)
def pubtator_annotate(pmids: str) -> str:
    try:
        ids = ",".join(p.strip() for p in str(pmids).split(",") if p.strip())
        if not ids:
            return "ERROR pubtator_annotate: no valid PMIDs given"
        data = json.loads(_get(f"/publications/export/biocjson?pmids={ids}"))
        docs = data.get("PubTator3") or data.get("documents") or []
        if not docs:
            return f"No PubTator annotations returned for PMIDs {ids}."
        out = []
        for doc in docs:
            pmid = doc.get("pmid") or doc.get("id", "?")
            # group unique (text -> id) per entity type
            by_type: dict[str, dict[str, str]] = {}
            for etype, text, ident in _doc_annotations(doc):
                by_type.setdefault(etype, {}).setdefault(text, ident or "")
            out.append(f"PMID {pmid}")
            for etype in sorted(by_type):
                items = by_type[etype]
                rendered = ", ".join(
                    f"{t} [{i}]" if i else t for t, i in list(items.items())[:12]
                )
                out.append(f"  {etype} ({len(items)}): {rendered}")
            rels = doc.get("relations_display") or doc.get("relations") or []
            shown = [s for s in (_format_relation(r) for r in rels) if s]
            if shown:
                out.append(f"  Relations ({len(shown)}):")
                out.extend(f"    - {s}" for s in shown[:15])
            out.append("")
        return "\n".join(out)[:_TRUNC]
    except Exception as e:
        return f"ERROR pubtator_annotate: {e}"


if __name__ == "__main__":
    import sys
    fn = sys.argv[1] if len(sys.argv) > 1 else "pubtator_annotate"
    arg = sys.argv[2] if len(sys.argv) > 2 else "21720365"
    print({"pubtator_entity": pubtator_entity,
           "pubtator_annotate": pubtator_annotate}[fn](arg))
