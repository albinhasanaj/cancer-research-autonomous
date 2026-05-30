"""ClinicalTrials.gov v2 API tool — "has anyone tried this in humans?".

No API key. Endpoint: https://clinicaltrials.gov/api/v2/studies
A killer ANSWERED/OPEN triage signal: before modelling whether a drug or
combination could work, check whether it has already been tested clinically and
with what status/phase/outcome.

Returns plain strings; errors surface as "ERROR <name>: ..." so the loop never
crashes.
"""
import json
import time
import urllib.parse
import urllib.request

from tools.registry import tool

_BASE = "https://clinicaltrials.gov/api/v2/studies"
_HEADERS = {"User-Agent": "research-agent/1.0", "Accept": "application/json"}
_SLEEP = 0.2
_TRUNC = 18_000


def _get(params: dict, timeout: int = 40) -> dict:
    url = _BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=_HEADERS)
    time.sleep(_SLEEP)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


@tool(
    "clinicaltrials_search",
    (
        "Search ClinicalTrials.gov (v2 API) for human trials matching a query "
        "(drug, gene, disease, or combination). Returns NCT id, status, phase, "
        "enrollment and title per trial, plus the total count. Use as an "
        "ANSWERED/OPEN triage signal: has this been tested in humans, and how far?"
    ),
    {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Free-text, e.g. 'olaparib BRCA' or 'WRN MSI-high'"},
            "n": {"type": "integer", "description": "Max trials to list (default 10)"},
        },
        "required": ["query"],
    },
)
def clinicaltrials_search(query: str, n: int = 10) -> str:
    try:
        data = _get({
            "query.term": query,
            "pageSize": max(1, min(n, 50)),
            "countTotal": "true",
            "format": "json",
        })
        total = data.get("totalCount", "?")
        studies = data.get("studies", [])
        lines = [
            f"ClinicalTrials.gov — '{query}'",
            f"total matching trials: {total} (showing {len(studies)})\n",
            f"{'NCT':>11}  {'status':>12}  {'phase':>10}  {'N':>6}  title",
        ]
        for st in studies:
            ps = st.get("protocolSection", {})
            ident = ps.get("identificationModule", {})
            status = ps.get("statusModule", {}).get("overallStatus", "n/a")
            design = ps.get("designModule", {})
            phases = design.get("phases") or ["NA"]
            enroll = (design.get("enrollmentInfo") or {}).get("count", "?")
            lines.append(
                f"{ident.get('nctId','?'):>11}  {status:>12}  "
                f"{'/'.join(phases):>10}  {str(enroll):>6}  "
                f"{ident.get('briefTitle','')[:70]}"
            )
        return "\n".join(lines)[:_TRUNC]
    except Exception as e:
        return f"ERROR clinicaltrials_search: {e}"


@tool(
    "clinicaltrials_phase_summary",
    (
        "Aggregate ClinicalTrials.gov trials for a query by phase and status — a "
        "compact 'how mature is this clinically?' view. Returns counts per phase "
        "and per overall status across up to 200 matching trials."
    ),
    {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Free-text query"},
        },
        "required": ["query"],
    },
)
def clinicaltrials_phase_summary(query: str) -> str:
    try:
        data = _get({
            "query.term": query,
            "pageSize": 200,
            "countTotal": "true",
            "format": "json",
        })
        total = data.get("totalCount", "?")
        studies = data.get("studies", [])
        phase_counts: dict[str, int] = {}
        status_counts: dict[str, int] = {}
        for st in studies:
            ps = st.get("protocolSection", {})
            status = ps.get("statusModule", {}).get("overallStatus", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1
            phases = (ps.get("designModule", {}) or {}).get("phases") or ["NA"]
            key = "/".join(phases)
            phase_counts[key] = phase_counts.get(key, 0) + 1
        lines = [
            f"ClinicalTrials.gov phase/status summary — '{query}'",
            f"total matching: {total} (aggregated over {len(studies)})\n",
            "By phase:",
        ]
        for k, v in sorted(phase_counts.items(), key=lambda kv: -kv[1]):
            lines.append(f"  {k:>12}: {v}")
        lines.append("\nBy status:")
        for k, v in sorted(status_counts.items(), key=lambda kv: -kv[1]):
            lines.append(f"  {k:>22}: {v}")
        return "\n".join(lines)[:_TRUNC]
    except Exception as e:
        return f"ERROR clinicaltrials_phase_summary: {e}"


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "olaparib BRCA"
    print(clinicaltrials_search(q))
