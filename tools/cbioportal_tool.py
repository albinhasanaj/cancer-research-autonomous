"""cBioPortal cancer genomics tools via the public REST API.

No API key required. Base URL: https://www.cbioportal.org/api
We sleep 0.3s between calls to stay polite. All functions return strings;
errors surface as "ERROR <name>: ..." so the agent loop never crashes.
"""
import json
import time
import urllib.parse
import urllib.request
from collections import Counter

from tools.registry import tool

BASE = "https://www.cbioportal.org/api"
_SLEEP = 0.3
_TRUNC = 18_000


def _get(path: str, params: dict | None = None, timeout: int = 40) -> bytes:
    url = f"{BASE}/{path.lstrip('/')}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"User-Agent": "research-agent/1.0", "Accept": "application/json"}
    )
    time.sleep(_SLEEP)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), dict(r.headers)


def _get_json(path: str, params: dict | None = None) -> tuple:
    body, headers = _get(path, params)
    return json.loads(body) if body else [], headers


# ─── 1. Studies ──────────────────────────────────────────────────────────────

@tool(
    "cbioportal_studies",
    "List cBioPortal cancer studies. Pass keyword to filter by name/studyId.",
    {
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "Case-insensitive filter on study name or studyId (empty = return first ~40)",
            }
        },
        "required": [],
    },
)
def cbioportal_studies(keyword: str = "") -> str:
    try:
        kw = keyword.lower().strip()
        collected, page, per_page = [], 0, 500
        while len(collected) < 2000:
            data, _ = _get_json(
                "/studies",
                {"direction": "ASC", "pageNumber": page, "pageSize": per_page,
                 "projection": "SUMMARY"},
            )
            if not data:
                break
            for s in data:
                name = s.get("name", "")
                sid = s.get("studyId", "")
                if not kw or kw in name.lower() or kw in sid.lower():
                    collected.append(s)
            if len(data) < per_page:
                break
            page += 1
            time.sleep(_SLEEP)

        collected = collected[:40]
        if not collected:
            return f"(no studies matching '{keyword}')"
        lines = [f"{'studyId':<40} {'#samp':>6}  name"]
        lines.append("-" * 80)
        for s in collected:
            sid = s.get("studyId", "?")
            name = s.get("name", "?")
            n = s.get("allSampleCount", "?")
            lines.append(f"{sid:<40} {str(n):>6}  {name}")
        out = "\n".join(lines)
        return out[:_TRUNC]
    except Exception as e:
        return f"ERROR cbioportal_studies: {e}"


# ─── 2. Gene Mutations ────────────────────────────────────────────────────────

@tool(
    "cbioportal_gene_mutations",
    "Summarise mutations for a HUGO gene in a cBioPortal study.",
    {
        "type": "object",
        "properties": {
            "study_id": {"type": "string", "description": "cBioPortal studyId, e.g. 'brca_tcga_pub'"},
            "gene": {"type": "string", "description": "HUGO gene symbol, e.g. 'TP53'"},
        },
        "required": ["study_id", "gene"],
    },
)
def cbioportal_gene_mutations(study_id: str, gene: str) -> str:
    try:
        gene = gene.strip().upper()
        study_id = study_id.strip()

        # Resolve Entrez ID
        gene_data, _ = _get_json(f"/genes/{urllib.parse.quote(gene)}")
        if not isinstance(gene_data, dict):
            return f"ERROR cbioportal_gene_mutations: gene '{gene}' not found"
        entrez_id = gene_data.get("entrezGeneId")
        if not entrez_id:
            return f"ERROR cbioportal_gene_mutations: no entrezGeneId for '{gene}'"

        profile_id = f"{study_id}_mutations"
        sample_list_id = f"{study_id}_all"

        # Fetch META to get total count
        _, meta_headers = _get(
            f"/molecular-profiles/{profile_id}/mutations",
            {"sampleListId": sample_list_id, "entrezGeneId": entrez_id,
             "projection": "META"},
        )
        total_muts = int(meta_headers.get("Total-Count", 0))
        total_samps = int(meta_headers.get("Sample-Count", 0))

        # Fetch all mutations (up to 10k) to build protein-change histogram
        mutations, page, per_page = [], 0, 500
        while len(mutations) < 10_000:
            data, _ = _get_json(
                f"/molecular-profiles/{profile_id}/mutations",
                {"sampleListId": sample_list_id, "entrezGeneId": entrez_id,
                 "projection": "SUMMARY", "pageSize": per_page, "pageNumber": page},
            )
            if not data:
                break
            mutations.extend(data)
            if len(data) < per_page:
                break
            page += 1
            time.sleep(_SLEEP)

        pc_counter: Counter = Counter()
        type_counter: Counter = Counter()
        for m in mutations:
            pc = m.get("proteinChange") or "unknown"
            mt = m.get("mutationType") or "unknown"
            pc_counter[pc] += 1
            type_counter[mt] += 1

        lines = [
            f"Study:            {study_id}",
            f"Gene:             {gene} (Entrez {entrez_id})",
            f"Profile:          {profile_id}",
            f"Mutated samples:  {total_samps}",
            f"Total mutations:  {total_muts}",
            "",
            "── Top 15 protein changes ──",
        ]
        for pc, cnt in pc_counter.most_common(15):
            lines.append(f"  {pc:<20} {cnt}")
        lines.append("")
        lines.append("── Mutation types ──")
        for mt, cnt in type_counter.most_common():
            lines.append(f"  {mt:<35} {cnt}")

        return "\n".join(lines)
    except Exception as e:
        return f"ERROR cbioportal_gene_mutations: {e}"


# ─── 3. Clinical Data ─────────────────────────────────────────────────────────

@tool(
    "cbioportal_clinical",
    "Summarise a clinical attribute for all patients in a cBioPortal study.",
    {
        "type": "object",
        "properties": {
            "study_id": {"type": "string", "description": "cBioPortal studyId"},
            "attribute": {
                "type": "string",
                "description": "Clinical attribute ID, e.g. 'OS_MONTHS', 'CANCER_TYPE_DETAILED'",
            },
        },
        "required": ["study_id"],
    },
)
def cbioportal_clinical(study_id: str, attribute: str = "OS_MONTHS") -> str:
    try:
        study_id = study_id.strip()
        attribute = attribute.strip()

        # Paginate through all patient clinical data for the attribute
        values, page, per_page = [], 0, 1000
        while True:
            data, _ = _get_json(
                f"/studies/{study_id}/clinical-data",
                {"clinicalDataType": "PATIENT", "attributeId": attribute,
                 "projection": "SUMMARY", "pageSize": per_page, "pageNumber": page},
            )
            if not data:
                break
            values.extend(v.get("value", "") for v in data)
            if len(data) < per_page:
                break
            page += 1
            time.sleep(_SLEEP)

        n = len(values)
        if n == 0:
            return f"(no data for attribute '{attribute}' in study '{study_id}')"

        # Try numeric summary
        numeric = []
        for v in values:
            try:
                numeric.append(float(v))
            except (ValueError, TypeError):
                pass

        lines = [
            f"Study:     {study_id}",
            f"Attribute: {attribute}",
            f"Count:     {n}",
        ]

        if len(numeric) >= 0.5 * n:
            numeric.sort()
            mean = sum(numeric) / len(numeric)
            mid = len(numeric) // 2
            median = (
                numeric[mid] if len(numeric) % 2 == 1
                else (numeric[mid - 1] + numeric[mid]) / 2
            )
            lines += [
                f"Mean:      {mean:.3f}",
                f"Median:    {median:.3f}",
                f"Min:       {numeric[0]:.3f}",
                f"Max:       {numeric[-1]:.3f}",
            ]
        else:
            freq: Counter = Counter(values)
            lines.append("── Top 20 value frequencies ──")
            for val, cnt in freq.most_common(20):
                lines.append(f"  {val:<40} {cnt}")

        return "\n".join(lines)
    except Exception as e:
        return f"ERROR cbioportal_clinical: {e}"
