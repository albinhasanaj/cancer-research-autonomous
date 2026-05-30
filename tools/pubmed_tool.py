"""PubMed literature tools via NCBI E-utilities (free; key optional).

This is the literature-grounding tool — every empirical claim the agent makes
should trace back to a PMID fetched here. Works with no API key; if NCBI_API_KEY
is set in the environment the rate limit is higher. We sleep ~0.34s between
calls to stay polite / within the unauthenticated 3 req/s limit.
"""
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from tools.registry import tool

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
_SLEEP = 0.34


def _params(extra: dict) -> dict:
    p = dict(extra)
    key = os.environ.get("NCBI_API_KEY")
    if key:
        p["api_key"] = key
    return p


def _get(endpoint: str, params: dict, timeout: int = 30) -> bytes:
    url = f"{BASE}/{endpoint}?" + urllib.parse.urlencode(_params(params))
    req = urllib.request.Request(url, headers={"User-Agent": "research-agent/1.0"})
    time.sleep(_SLEEP)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


@tool(
    "pubmed_search",
    "Search PubMed for a query; returns up to retmax results as 'PMID | title'.",
    {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "retmax": {"type": "integer", "description": "Max results (default 5)"},
        },
        "required": ["query"],
    },
)
def pubmed_search(query: str, retmax: int = 5) -> str:
    try:
        raw = _get(
            "esearch.fcgi",
            {"db": "pubmed", "term": query, "retmax": retmax, "retmode": "json"},
        )
        import json
        ids = json.loads(raw).get("esearchresult", {}).get("idlist", [])
        if not ids:
            return "(no results)"
        summ = _get(
            "esummary.fcgi",
            {"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
        )
        import json as _json
        data = _json.loads(summ).get("result", {})
        lines = []
        for pmid in ids:
            rec = data.get(pmid, {})
            title = rec.get("title", "(no title)")
            lines.append(f"{pmid} | {title}")
        return "\n".join(lines)
    except Exception as e:
        return f"ERROR pubmed_search: {e}"


@tool(
    "pubmed_fetch",
    "Fetch abstracts for one or more PMIDs (comma-separated or list).",
    {
        "type": "object",
        "properties": {
            "pmids": {"type": "string", "description": "Comma-separated PMIDs, e.g. '12345,67890'"},
        },
        "required": ["pmids"],
    },
)
def pubmed_fetch(pmids) -> str:
    try:
        if isinstance(pmids, (list, tuple)):
            ids = ",".join(str(p) for p in pmids)
        else:
            ids = str(pmids)
        raw = _get(
            "efetch.fcgi",
            {"db": "pubmed", "id": ids, "rettype": "abstract", "retmode": "xml"},
        )
        root = ET.fromstring(raw)
        out = []
        for art in root.iter("PubmedArticle"):
            pmid_el = art.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None else "?"
            title_el = art.find(".//ArticleTitle")
            title = "".join(title_el.itertext()) if title_el is not None else "(no title)"
            abst_parts = []
            for ab in art.findall(".//Abstract/AbstractText"):
                label = ab.get("Label")
                text = "".join(ab.itertext())
                abst_parts.append(f"{label}: {text}" if label else text)
            abstract = "\n".join(abst_parts) or "(no abstract)"
            out.append(f"PMID {pmid}\n{title}\n{abstract}")
        return "\n\n---\n\n".join(out) if out else "(no articles returned)"
    except Exception as e:
        return f"ERROR pubmed_fetch: {e}"
