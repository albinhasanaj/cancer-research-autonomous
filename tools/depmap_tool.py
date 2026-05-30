"""DepMap CRISPR Chronos gene-effect dependency tool.

Per-gene Chronos scores from the DepMap portal API, cached under
data/depmap/genes/<GENE>.csv (git-ignored). Chronos: more negative = more
essential; dependency threshold Chronos < -0.5. API: https://depmap.org/portal/api
"""
import csv
import io
import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from tools.registry import tool

_REPO_ROOT = Path(__file__).parent.parent
_CACHE_DIR = _REPO_ROOT / "data" / "depmap" / "genes"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

_BASE = "https://depmap.org/portal/api"
_HEADERS = {"User-Agent": "research-agent/1.0 (cancer-research-harness)"}
_TRUNC = 18_000
_DEP_THRESHOLD = -0.5  # Chronos: lines below this are considered "dependent"


def _post_json(url: str, payload: dict, timeout: int = 30) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={**_HEADERS, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _get_json(url: str, timeout: int = 30) -> object:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _download_text(url: str, timeout: int = 180) -> str:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def _find_chronos_dataset_id() -> str:
    """Resolve the Chronos CRISPR gene-effect dataset ID from the DepMap portal."""
    datasets = _get_json(f"{_BASE}/download/datasets")
    for ds in datasets:
        name = (ds.get("display_name") or "").lower()
        if "chronos" in name and "crispr" in name:
            return ds["id"]
    # Fallback: any non-confounder non-probability CRISPR dataset
    for ds in datasets:
        dtype = (ds.get("data_type") or "").lower()
        name = (ds.get("display_name") or "").lower()
        if ("crispr" in dtype and "confounder" not in name
                and "dependency" not in name and "probability" not in name):
            return ds["id"]
    raise RuntimeError("Could not locate a Chronos CRISPR gene-effect dataset on DepMap portal")


def _poll_task(task_id: str, max_wait: int = 240) -> str:
    """Poll a DepMap async download task; return the download URL on success."""
    elapsed, delay = 0, 2
    while elapsed < max_wait:
        result = _get_json(f"{_BASE}/task/{task_id}")
        state = result.get("state")
        if state == "SUCCESS":
            return result["result"]["downloadUrl"]
        if state == "FAILURE":
            raise RuntimeError(f"DepMap task {task_id} failed: {result.get('message')}")
        time.sleep(delay)
        elapsed += delay
        delay = min(delay * 1.5, 10)
    raise TimeoutError(f"DepMap task {task_id} did not finish within {max_wait}s")


_META_COLS = {
    "depmap_id", "DepMap_ID", "cell_line_display_name",
    "cell_line_name", "lineage_1", "lineage_2", "lineage_3", "lineage_4",
}


def _load_gene_effect(gene: str) -> pd.DataFrame:
    """Return a DataFrame with columns: depmap_id, cell_line_name, lineage, lineage2, score.

    Downloads from the DepMap portal on the first call for each gene; subsequent
    calls read from the local CSV cache at data/depmap/genes/<GENE>.csv.
    """
    gene_upper = gene.strip().upper()
    cache_file = _CACHE_DIR / f"{gene_upper}.csv"

    if cache_file.exists():
        return pd.read_csv(cache_file)

    # Download via DepMap portal custom-download API
    dataset_id = _find_chronos_dataset_id()
    task_resp = _post_json(
        f"{_BASE}/download/custom",
        {
            "datasetId": dataset_id,
            "addCellLineMetadata": True,
            "featureLabels": [gene_upper],
            "dropEmpty": True,
        },
    )
    download_url = _poll_task(task_resp["id"])
    csv_text = _download_text(download_url)

    rows = list(csv.DictReader(io.StringIO(csv_text)))
    if not rows:
        raise ValueError(f"DepMap returned no rows for gene '{gene_upper}'")

    # Find score column — any column whose name contains the gene symbol
    score_col = None
    for col in rows[0].keys():
        if gene_upper in col.upper() and col not in _META_COLS:
            score_col = col
            break
    if score_col is None:
        raise ValueError(f"Score column for '{gene_upper}' not found. Available: {list(rows[0].keys())}")

    records = []
    for row in rows:
        try:
            score = float(row[score_col])
        except (ValueError, TypeError):
            continue
        depmap_id = row.get("depmap_id") or row.get("DepMap_ID") or ""
        cell_line = row.get("cell_line_display_name") or row.get("cell_line_name") or depmap_id
        records.append({
            "depmap_id": depmap_id, "cell_line_name": cell_line,
            "lineage": row.get("lineage_1") or "", "lineage2": row.get("lineage_2") or "",
            "score": score,
        })

    df = pd.DataFrame(records)
    df.to_csv(cache_file, index=False)
    return df


def _filter_by_context(df: pd.DataFrame, context: str) -> pd.DataFrame:
    """Filter gene-effect DataFrame by lineage substring or comma-sep cell-line names."""
    ctx = context.strip()
    if not ctx:
        return df
    parts = [p.strip().lower() for p in ctx.split(",") if p.strip()]
    if len(parts) > 1:
        # Multiple tokens → try exact cell-line name match first, then substring
        mask = df["cell_line_name"].str.lower().isin(parts)
        if mask.sum() == 0:
            pattern = "|".join(urllib.parse.quote(p, safe="") for p in parts)
            mask = df["cell_line_name"].str.lower().str.contains(
                "|".join(parts), na=False, regex=False
            )
        return df[mask]
    token = parts[0]
    mask = (
        df["lineage"].str.lower().str.contains(token, na=False)
        | df["lineage2"].str.lower().str.contains(token, na=False)
        | df["cell_line_name"].str.lower().str.contains(token, na=False)
    )
    return df[mask]


def _stats_block(scores: np.ndarray, gene: str, label: str) -> str:
    n = len(scores)
    if n == 0:
        return f"  [{label}] No matching cell lines.\n"
    mean = float(np.mean(scores))
    median = float(np.median(scores))
    mn, mx = float(scores.min()), float(scores.max())
    n_dep = int(np.sum(scores < _DEP_THRESHOLD))
    return (
        f"  [{label}]  n={n}  mean={mean:+.4f}  median={median:+.4f}"
        f"  min={mn:+.4f}  max={mx:+.4f}"
        f"  n_dependent={n_dep} ({n_dep/n:.1%}, Chronos<{_DEP_THRESHOLD})\n"
    )


@tool(
    "depmap_query",
    (
        "Chronos gene-effect distribution for a HUGO gene across DepMap lines: "
        "n, mean, median, fraction dependent (Chronos < -0.5). Optional context "
        "(lineage substring e.g. 'breast'/'lung', or comma-separated cell-line names) "
        "reports subset stats alongside whole-panel stats."
    ),
    {
        "type": "object",
        "properties": {
            "gene": {"type": "string", "description": "HUGO gene symbol, e.g. 'BRCA1'"},
            "context": {"type": "string", "description": "Optional lineage substring or comma-sep cell-line names"},
        },
        "required": ["gene"],
    },
)
def depmap_query(gene: str, context: str = "") -> str:
    try:
        df = _load_gene_effect(gene.strip().upper())
        all_scores = df["score"].to_numpy()
        header = f"DepMap Chronos gene-effect — {gene.upper()}\n"
        full_block = _stats_block(all_scores, gene, "all lines")

        top_n = df.nsmallest(10, "score")[["cell_line_name", "lineage", "score"]]
        top_str = "\nTop-10 most dependent lines (global):\n" + top_n.to_string(index=False)

        if context.strip():
            sub = _filter_by_context(df, context)
            sub_scores = sub["score"].to_numpy()
            sub_block = _stats_block(sub_scores, gene, context)
            sub_top = sub.nsmallest(10, "score")[["cell_line_name", "lineage", "score"]]
            sub_top_str = (
                f"\nTop-10 most dependent in '{context}':\n" + sub_top.to_string(index=False)
            )
            out = header + full_block + sub_block + top_str + sub_top_str
        else:
            out = header + full_block + top_str

        return out[:_TRUNC]
    except Exception as e:
        return f"ERROR depmap_query: {e}"


@tool(
    "depmap_compare",
    (
        "Compare Chronos gene-effect for a HUGO gene between two cell-line groups. "
        "Each group is a lineage substring (e.g. 'breast', 'lung') or comma-separated "
        "cell-line names. Returns n, means, medians, Cohen's d, Mann-Whitney U p-value."
    ),
    {
        "type": "object",
        "properties": {
            "gene": {"type": "string", "description": "HUGO gene symbol"},
            "group_a": {"type": "string", "description": "Lineage substring or comma-sep cell-line names (group A)"},
            "group_b": {"type": "string", "description": "Lineage substring or comma-sep cell-line names (group B)"},
        },
        "required": ["gene", "group_a", "group_b"],
    },
)
def depmap_compare(gene: str, group_a: str, group_b: str) -> str:
    try:
        df = _load_gene_effect(gene.strip().upper())
        a_df = _filter_by_context(df, group_a)
        b_df = _filter_by_context(df, group_b)
        a = a_df["score"].to_numpy()
        b = b_df["score"].to_numpy()

        if len(a) == 0:
            return f"ERROR depmap_compare: no cell lines matched group_a='{group_a}'"
        if len(b) == 0:
            return f"ERROR depmap_compare: no cell lines matched group_b='{group_b}'"

        # Cohen's d (pooled SD)
        n_a, n_b = len(a), len(b)
        mean_a, mean_b = float(np.mean(a)), float(np.mean(b))
        sd_a = float(np.std(a, ddof=1)) if n_a > 1 else 0.0
        sd_b = float(np.std(b, ddof=1)) if n_b > 1 else 0.0
        if n_a + n_b > 2:
            pooled = math.sqrt(((n_a - 1) * sd_a**2 + (n_b - 1) * sd_b**2) / (n_a + n_b - 2))
            cohen_d = (mean_a - mean_b) / pooled if pooled > 0 else float("nan")
        else:
            cohen_d = float("nan")

        # Mann-Whitney U (two-sided)
        if n_a >= 2 and n_b >= 2:
            u_stat, p_val = stats.mannwhitneyu(a, b, alternative="two-sided")
        else:
            u_stat, p_val = float("nan"), float("nan")

        out = (
            f"DepMap Chronos comparison — {gene.upper()}\n"
            f"Dependency threshold: Chronos < {_DEP_THRESHOLD}\n\n"
            f"Group A '{group_a}':\n"
            f"  n={n_a}  mean={mean_a:+.4f}  median={float(np.median(a)):+.4f}"
            f"  sd={sd_a:.4f}  frac_dep={np.mean(a < _DEP_THRESHOLD):.1%}\n\n"
            f"Group B '{group_b}':\n"
            f"  n={n_b}  mean={mean_b:+.4f}  median={float(np.median(b)):+.4f}"
            f"  sd={sd_b:.4f}  frac_dep={np.mean(b < _DEP_THRESHOLD):.1%}\n\n"
            f"Statistics (A − B):\n"
            f"  Cohen's d = {cohen_d:+.4f}  (negative ⇒ A more dependent than B)\n"
            f"  Mann-Whitney U = {u_stat:.0f},  p = {p_val:.3e}  (two-sided)\n"
        )
        return out[:_TRUNC]
    except Exception as e:
        return f"ERROR depmap_compare: {e}"
