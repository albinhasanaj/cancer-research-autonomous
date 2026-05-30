"""GEO (Gene Expression Omnibus) dataset discovery via NCBI E-utilities.

Provides agent access to the NCBI GEO DataSets database (db=gds) using the
same free E-utilities API as pubmed_tool.  No new dependencies — stdlib only.
NCBI_API_KEY from env is forwarded when present for higher rate limits.
"""
import json
import os
import time
import urllib.parse
import urllib.request

from tools.registry import tool

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
_SLEEP = 0.34
_MAX_CHARS = 16_000


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


def _trunc(text: str) -> str:
    if len(text) > _MAX_CHARS:
        return text[:_MAX_CHARS] + "\n...[truncated]"
    return text


def _extract_summary_fields(rec: dict) -> dict:
    """Pull the fields we care about from an esummary result record.

    GEO esummary returns different shapes depending on entry type (GSE/GDS/GPL).
    We normalise them into a flat dict with safe defaults.
    """
    # Accession: prefer 'accession', fall back to constructing from entryType+uid
    accession = rec.get("accession", rec.get("Accession", ""))
    if not accession:
        entry_type = rec.get("entryType", rec.get("EntryType", ""))
        uid = rec.get("uid", "")
        accession = f"{entry_type}{uid}" if entry_type else uid

    title = rec.get("title", rec.get("Title", "(no title)"))
    summary = rec.get("summary", rec.get("Summary", rec.get("description", "")))
    organism = rec.get("taxon", rec.get("Taxon", rec.get("organism", "")))
    platform = rec.get("GPL", rec.get("gpl", ""))
    n_samples = rec.get("n_samples", rec.get("GSEsamples", rec.get("gdsType", "")))
    pdat = rec.get("pdat", rec.get("PDAT", rec.get("submissionDate", "")))
    ftp = rec.get("ftplink", rec.get("FTPLink", rec.get("ftp", "")))
    suppfile = rec.get("suppfile", rec.get("SuppFile", ""))

    return {
        "accession": accession,
        "title": title,
        "summary": summary,
        "organism": organism,
        "platform": platform,
        "n_samples": n_samples,
        "pdat": pdat,
        "ftp": ftp,
        "suppfile": suppfile,
    }


@tool(
    "geo_search",
    (
        "Search NCBI GEO DataSets for gene-expression datasets matching a query. "
        "Returns up to retmax hits formatted as 'ACCESSION | title | organism | nSamples'."
    ),
    {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Free-text GEO search query"},
            "retmax": {
                "type": "integer",
                "description": "Max results to return (default 10)",
            },
        },
        "required": ["query"],
    },
)
def geo_search(query: str, retmax: int = 10) -> str:
    try:
        raw = _get(
            "esearch.fcgi",
            {"db": "gds", "term": query, "retmax": retmax, "retmode": "json"},
        )
        ids = json.loads(raw).get("esearchresult", {}).get("idlist", [])
        if not ids:
            return "(no GEO results)"

        summ_raw = _get(
            "esummary.fcgi",
            {"db": "gds", "id": ",".join(ids), "retmode": "json"},
        )
        data = json.loads(summ_raw).get("result", {})

        lines = []
        for uid in ids:
            rec = data.get(uid, {})
            if not rec or uid == "uids":
                continue
            f = _extract_summary_fields(rec)
            n = f["n_samples"]
            lines.append(
                f"{f['accession']} | {f['title']} | {f['organism']} | {n}"
            )

        return _trunc("\n".join(lines)) if lines else "(no records in summary)"
    except Exception as e:
        return f"ERROR geo_search: {e}"


@tool(
    "geo_summary",
    (
        "Fetch a detailed summary for a GEO accession (e.g. 'GSE12345'). "
        "Returns title, description, organism, platform, sample count, "
        "submission date, and download URL."
    ),
    {
        "type": "object",
        "properties": {
            "accession": {
                "type": "string",
                "description": "GEO accession such as 'GSE12345' or 'GDS1234'",
            }
        },
        "required": ["accession"],
    },
)
def geo_summary(accession: str) -> str:
    try:
        accession = accession.strip()
        # Resolve accession → numeric UID via esearch
        search_raw = _get(
            "esearch.fcgi",
            {
                "db": "gds",
                "term": f"{accession}[ACCN]",
                "retmax": 5,
                "retmode": "json",
            },
        )
        ids = json.loads(search_raw).get("esearchresult", {}).get("idlist", [])
        if not ids:
            # Try without field tag as fallback
            search_raw2 = _get(
                "esearch.fcgi",
                {"db": "gds", "term": accession, "retmax": 5, "retmode": "json"},
            )
            ids = json.loads(search_raw2).get("esearchresult", {}).get("idlist", [])
        if not ids:
            return f"(no GEO record found for accession '{accession}')"

        summ_raw = _get(
            "esummary.fcgi",
            {"db": "gds", "id": ids[0], "retmode": "json"},
        )
        data = json.loads(summ_raw).get("result", {})
        rec = data.get(ids[0], {})
        if not rec:
            return f"(empty esummary for UID {ids[0]})"

        f = _extract_summary_fields(rec)

        parts = [
            f"Accession  : {f['accession']}",
            f"Title      : {f['title']}",
            f"Organism   : {f['organism']}",
            f"Platform   : {f['platform']}",
            f"Samples    : {f['n_samples']}",
            f"Submitted  : {f['pdat']}",
            f"FTP        : {f['ftp']}",
            f"Suppl.files: {f['suppfile']}",
            "",
            "Description:",
            f['summary'],
        ]
        return _trunc("\n".join(parts))
    except Exception as e:
        return f"ERROR geo_summary: {e}"
