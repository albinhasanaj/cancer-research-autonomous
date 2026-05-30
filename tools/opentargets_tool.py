"""Open Targets target-disease association tools via the public GraphQL API.

No API key. Endpoint: https://api.platform.opentargets.org/api/v4/graphql
Answers "is this target worth pursuing?" — genetic/genomic association scores,
tractability/druggability, and known drugs — so the agent can triage a target
against the curated evidence base instead of asserting from memory or a toy model.

All functions return plain strings; errors surface as "ERROR <name>: ..." so an
iteration never crashes.
"""
import json
import time
import urllib.request

from tools.registry import tool

_URL = "https://api.platform.opentargets.org/api/v4/graphql"
_HEADERS = {"Content-Type": "application/json", "User-Agent": "research-agent/1.0"}
_SLEEP = 0.2
_TRUNC = 18_000


def _gql(query: str, variables: dict, timeout: int = 40) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(_URL, data=body, headers=_HEADERS)
    time.sleep(_SLEEP)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        payload = json.loads(r.read())
    if "errors" in payload:
        raise RuntimeError(payload["errors"][0].get("message", "GraphQL error"))
    return payload["data"]


def _resolve_target(symbol: str) -> tuple[str, str]:
    """Resolve a HUGO symbol to (ensembl_id, approved_name). Raises if not found."""
    q = """query($s:String!){ search(queryString:$s, entityNames:["target"]){
        hits{ id name entity } } }"""
    hits = _gql(q, {"s": symbol})["search"]["hits"]
    for h in hits:
        if h["entity"] == "target" and h["name"].upper() == symbol.upper():
            return h["id"], h["name"]
    if hits:
        return hits[0]["id"], hits[0]["name"]
    raise ValueError(f"no Open Targets target found for '{symbol}'")


@tool(
    "opentargets_associations",
    (
        "Top disease associations for a HUGO gene from Open Targets: overall "
        "association score (0-1) plus per-datatype scores (genetic, somatic, "
        "drugs, literature). Use to triage 'is this target linked to disease X, "
        "and by what evidence?'."
    ),
    {
        "type": "object",
        "properties": {
            "gene": {"type": "string", "description": "HUGO gene symbol, e.g. 'PARP1'"},
            "n": {"type": "integer", "description": "Number of diseases (default 15)"},
        },
        "required": ["gene"],
    },
)
def opentargets_associations(gene: str, n: int = 15) -> str:
    try:
        ensembl_id, name = _resolve_target(gene)
        q = """query($id:String!, $n:Int!){
          target(ensemblId:$id){
            associatedDiseases(page:{index:0, size:$n}){
              count
              rows{ score disease{ name }
                datatypeScores{ id score } } } } }"""
        data = _gql(q, {"id": ensembl_id, "n": n})
        ad = data["target"]["associatedDiseases"]
        lines = [
            f"Open Targets associations — {name} ({ensembl_id})",
            f"total associated diseases: {ad['count']}\n",
            f"{'score':>6}  {'genetic':>7} {'somatic':>7} {'drug':>6} {'lit':>6}  disease",
        ]
        for row in ad["rows"]:
            dts = {d["id"]: d["score"] for d in row["datatypeScores"]}
            lines.append(
                f"{row['score']:>6.3f}  "
                f"{dts.get('genetic_association', 0):>7.3f} "
                f"{dts.get('somatic_mutation', 0):>7.3f} "
                f"{dts.get('known_drug', 0):>6.3f} "
                f"{dts.get('literature', 0):>6.3f}  "
                f"{row['disease']['name']}"
            )
        return "\n".join(lines)[:_TRUNC]
    except Exception as e:
        return f"ERROR opentargets_associations: {e}"


@tool(
    "opentargets_tractability",
    (
        "Druggability/tractability for a HUGO gene from Open Targets: small-molecule "
        "and antibody tractability buckets, plus known approved/clinical drugs. Use "
        "to judge 'can this target realistically be drugged, and is it already?'."
    ),
    {
        "type": "object",
        "properties": {
            "gene": {"type": "string", "description": "HUGO gene symbol"},
        },
        "required": ["gene"],
    },
)
def opentargets_tractability(gene: str) -> str:
    try:
        ensembl_id, name = _resolve_target(gene)
        q = """query($id:String!){
          target(ensemblId:$id){
            tractability{ label modality value }
            drugAndClinicalCandidates{ count
              rows{ maxClinicalStage drug{ name } } } } }"""
        data = _gql(q, {"id": ensembl_id})
        t = data["target"]
        lines = [f"Open Targets tractability — {name} ({ensembl_id})", "", "Tractability buckets (value=True ⇒ supported):"]
        by_mod: dict[str, list[str]] = {}
        for tr in t.get("tractability") or []:
            if tr.get("value"):
                by_mod.setdefault(tr["modality"], []).append(tr["label"])
        if by_mod:
            for mod, labels in by_mod.items():
                lines.append(f"  {mod}: {', '.join(labels)}")
        else:
            lines.append("  (none flagged)")

        kd = t.get("drugAndClinicalCandidates") or {"count": 0, "rows": []}
        lines.append(f"\nDrugs & clinical candidates: {kd['count']} total (showing up to 10)")
        for row in kd["rows"][:10]:
            drug = (row.get("drug") or {}).get("name", "?")
            lines.append(f"  {drug} — max clinical stage {row.get('maxClinicalStage', 'n/a')}")
        return "\n".join(lines)[:_TRUNC]
    except Exception as e:
        return f"ERROR opentargets_tractability: {e}"


if __name__ == "__main__":
    import sys
    fn = sys.argv[1] if len(sys.argv) > 1 else "opentargets_associations"
    arg = sys.argv[2] if len(sys.argv) > 2 else "PARP1"
    print({"opentargets_associations": opentargets_associations,
           "opentargets_tractability": opentargets_tractability}[fn](arg))
