"""NCI GDC (Genomic Data Commons / TCGA) REST API tools.

Base URL: https://api.gdc.cancer.gov — no API key required.
Uses urllib only; all functions return strings and never raise.

Three registered tools:
  gdc_projects        — list/search GDC projects
  gdc_gene_mutations  — count SSMs for a HUGO gene symbol
  gdc_case_count      — number of cases in a project
"""
import json
import time
import urllib.parse
import urllib.request

from tools.registry import tool

_BASE = "https://api.gdc.cancer.gov"
_SLEEP = 0.4   # polite delay between calls
_MAX_CHARS = 18_000


def _get(endpoint: str, params: dict, timeout: int = 30) -> dict:
    url = f"{_BASE}/{endpoint}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "research-agent/1.0"})
    time.sleep(_SLEEP)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


# ---------------------------------------------------------------------------
# gdc_projects
# ---------------------------------------------------------------------------

@tool(
    "gdc_projects",
    (
        "List GDC/TCGA projects (up to ~40). Optional keyword filters by "
        "project_id or name (case-insensitive). Returns lines: "
        "'project_id | name | primary_site'."
    ),
    {
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "Optional filter keyword, e.g. 'TCGA' or 'breast'.",
            }
        },
        "required": [],
    },
)
def gdc_projects(keyword: str = "") -> str:
    try:
        data = _get(
            "projects",
            {
                "size": 100,
                "fields": "project_id,name,primary_site",
                "format": "json",
            },
        )
        hits = data.get("data", {}).get("hits", [])
        kw = keyword.lower()
        lines = []
        for h in hits:
            pid = h.get("project_id", "")
            name = h.get("name", "")
            sites = h.get("primary_site", [])
            site_str = ", ".join(sites[:3]) if isinstance(sites, list) else str(sites)
            if kw and kw not in pid.lower() and kw not in name.lower() and kw not in site_str.lower():
                continue
            lines.append(f"{pid} | {name} | {site_str}")
            if len(lines) >= 40:
                break
        if not lines:
            return f"(no projects matched keyword={keyword!r})"
        return "\n".join(lines)
    except Exception as e:
        return f"ERROR gdc_projects: {e}"


# ---------------------------------------------------------------------------
# gdc_gene_mutations
# ---------------------------------------------------------------------------

@tool(
    "gdc_gene_mutations",
    (
        "Count simple somatic mutations (SSMs) in GDC for a HUGO gene symbol "
        "(e.g. 'TP53'), optionally restricted to a project (e.g. 'TCGA-BRCA'). "
        "Returns total SSM count and up to 15 distinct mutations with subtype."
    ),
    {
        "type": "object",
        "properties": {
            "gene": {
                "type": "string",
                "description": "HUGO gene symbol, e.g. 'TP53'.",
            },
            "project": {
                "type": "string",
                "description": "Optional GDC project ID, e.g. 'TCGA-BRCA'.",
            },
        },
        "required": ["gene"],
    },
)
def gdc_gene_mutations(gene: str, project: str = "") -> str:
    try:
        # Build filters
        gene_filter = {
            "op": "in",
            "content": {
                "field": "consequence.transcript.gene.symbol",
                "value": [gene.upper()],
            },
        }
        if project:
            filters = {
                "op": "and",
                "content": [
                    gene_filter,
                    {
                        "op": "in",
                        "content": {
                            "field": "cases.project.project_id",
                            "value": [project],
                        },
                    },
                ],
            }
        else:
            filters = gene_filter

        # First: total count (size=0)
        count_data = _get(
            "ssms",
            {
                "filters": json.dumps(filters),
                "size": 0,
                "format": "json",
            },
        )
        total = count_data.get("data", {}).get("pagination", {}).get("total", 0)

        # Then: up to 15 sample mutations
        sample_data = _get(
            "ssms",
            {
                "filters": json.dumps(filters),
                "size": 15,
                "fields": "genomic_dna_change,mutation_subtype",
                "format": "json",
            },
        )
        hits = sample_data.get("data", {}).get("hits", [])

        proj_label = f" in {project}" if project else " (all projects)"
        lines = [
            f"Gene: {gene.upper()}{proj_label}",
            f"Total SSMs: {total}",
            "",
            "Sample mutations (up to 15):",
        ]
        for h in hits:
            change = h.get("genomic_dna_change", "?")
            subtype = h.get("mutation_subtype", "?")
            lines.append(f"  {change}  [{subtype}]")

        result = "\n".join(lines)
        return result[:_MAX_CHARS]
    except Exception as e:
        return f"ERROR gdc_gene_mutations: {e}"


# ---------------------------------------------------------------------------
# gdc_case_count
# ---------------------------------------------------------------------------

@tool(
    "gdc_case_count",
    (
        "Return the total number of cases (patients) in a GDC project, "
        "e.g. 'TCGA-BRCA'."
    ),
    {
        "type": "object",
        "properties": {
            "project": {
                "type": "string",
                "description": "GDC project ID, e.g. 'TCGA-BRCA'.",
            }
        },
        "required": ["project"],
    },
)
def gdc_case_count(project: str) -> str:
    try:
        filters = {
            "op": "in",
            "content": {
                "field": "cases.project.project_id",
                "value": [project],
            },
        }
        data = _get(
            "cases",
            {
                "filters": json.dumps(filters),
                "size": 0,
                "format": "json",
            },
        )
        total = data.get("data", {}).get("pagination", {}).get("total", 0)
        return f"Project: {project}\nTotal cases: {total}"
    except Exception as e:
        return f"ERROR gdc_case_count: {e}"
