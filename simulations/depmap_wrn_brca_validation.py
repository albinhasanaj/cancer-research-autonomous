"""
DepMap functional validation: Is WRN dependency enriched in BRCA-loss cell lines?

Question (item 11): The Boolean DDR model predicts BRCA+WRN synthetic lethality.
If true, cell lines with BRCA1/2 loss should show greater WRN dependency in
CRISPR screens — especially in MSS (microsatellite-stable) context to avoid the
MSI confound identified in item 9.

Approach:
1. Query DepMap API for available CRISPR datasets
2. Download WRN gene effect scores (custom subset)
3. Download BRCA1/BRCA2 mutation table
4. Cross-reference: compare WRN dependency in BRCA-mutant vs BRCA-WT lines
5. Stratify by MSI status if available
6. Statistical test: Mann-Whitney U (one-sided: BRCA-mut more dependent on WRN)

Data: DepMap 24Q4 (or latest available via API)
"""

import requests
import time
import json
import csv
import io
import sys
from pathlib import Path
from scipy import stats
import numpy as np

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

BASE_URL = "https://depmap.org/portal/api"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def get_datasets():
    """List available datasets for custom download."""
    resp = requests.get(f"{BASE_URL}/download/datasets", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def submit_custom_download(dataset_id, feature_labels=None, cell_line_ids=None,
                           add_metadata=True):
    """Submit a custom download task and return the task ID."""
    params = {"datasetId": dataset_id, "addCellLineMetadata": add_metadata}
    if feature_labels:
        params["featureLabels"] = feature_labels
    if cell_line_ids:
        params["cellLineIds"] = cell_line_ids
    params["dropEmpty"] = True

    resp = requests.post(f"{BASE_URL}/download/custom", json=params,
                         headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def submit_mutation_download(feature_labels=None, cell_line_ids=None):
    """Submit a mutation table download task."""
    params = {}
    if feature_labels:
        params["featureLabels"] = feature_labels
    if cell_line_ids:
        params["cellLineIds"] = cell_line_ids

    resp = requests.post(f"{BASE_URL}/download/custom_mutation_table",
                         json=params, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def poll_task(task_id, max_wait=120):
    """Poll a task until completion, return result."""
    elapsed = 0
    delay = 2
    while elapsed < max_wait:
        resp = requests.get(f"{BASE_URL}/task/{task_id}", headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        state = data.get("state")
        if state == "SUCCESS":
            return data.get("result")
        elif state == "FAILURE":
            raise RuntimeError(f"Task {task_id} failed: {data.get('message')}")
        time.sleep(delay)
        elapsed += delay
        delay = min(delay * 1.5, 10)
    raise TimeoutError(f"Task {task_id} did not complete within {max_wait}s")


def download_csv(url):
    """Download a CSV from a URL and return as list of dicts."""
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    text = resp.text
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def find_crispr_dataset(datasets):
    """Find the CRISPR gene effect dataset ID."""
    candidates = []
    for ds in datasets:
        name = (ds.get("display_name") or "").lower()
        data_type = (ds.get("data_type") or "").lower()
        if "crispr" in name and "gene effect" in name:
            candidates.append(ds)
        elif "crispr" in data_type and "gene" in name:
            candidates.append(ds)
    # Prefer the one with "Chronos" or latest
    for c in candidates:
        if "chronos" in (c.get("display_name") or "").lower():
            return c
    return candidates[0] if candidates else None


def main():
    print("=" * 70)
    print("DepMap WRN dependency vs BRCA1/2 loss — functional SL validation")
    print("=" * 70)

    # Step 1: Get available datasets
    print("\n[1] Fetching available datasets...")
    datasets = get_datasets()
    print(f"    Found {len(datasets)} datasets")

    # Find CRISPR gene effect dataset
    crispr_ds = find_crispr_dataset(datasets)
    if not crispr_ds:
        print("    Available datasets:")
        for ds in datasets:
            print(f"      - {ds.get('id')}: {ds.get('display_name')} "
                  f"({ds.get('data_type')})")
        sys.exit("ERROR: Could not find CRISPR gene effect dataset")

    # Also find the raw Chronos (Gene Effect) dataset
    chronos_ds = None
    for ds in datasets:
        name = (ds.get("display_name") or "").lower()
        if "chronos" in name and "crispr" in name:
            chronos_ds = ds
            break

    print(f"    Gene Dependency: {crispr_ds['display_name']} "
          f"(id={crispr_ds['id']})")
    if chronos_ds:
        print(f"    Gene Effect (Chronos): {chronos_ds['display_name']} "
              f"(id={chronos_ds['id']})")

    # Step 2: Download WRN scores from BOTH datasets
    print("\n[2] Requesting WRN gene dependency (probability) scores...")
    task_data = submit_custom_download(
        crispr_ds["id"],
        feature_labels=["WRN"],
        add_metadata=True
    )
    task_id = task_data["id"]
    print(f"    Task submitted: {task_id}")
    result = poll_task(task_id)
    download_url = result["downloadUrl"]
    print(f"    Downloading...")
    wrn_rows = download_csv(download_url)
    print(f"    Got {len(wrn_rows)} cell lines with WRN dependency prob")

    # Also get raw Chronos gene effect if available
    wrn_chronos_rows = []
    if chronos_ds:
        print("\n    Requesting WRN Chronos gene effect scores...")
        task_data = submit_custom_download(
            chronos_ds["id"],
            feature_labels=["WRN"],
            add_metadata=True
        )
        task_id = task_data["id"]
        result = poll_task(task_id)
        download_url = result["downloadUrl"]
        wrn_chronos_rows = download_csv(download_url)
        print(f"    Got {len(wrn_chronos_rows)} cell lines with Chronos scores")

    # Step 3: Download BRCA1/BRCA2/WRN mutations
    print("\n[3] Requesting BRCA1/BRCA2 mutation table...")
    task_data = submit_mutation_download(
        feature_labels=["BRCA1", "BRCA2"]
    )
    task_id = task_data["id"]
    print(f"    Task submitted: {task_id}")
    result = poll_task(task_id)
    download_url = result["downloadUrl"]
    print(f"    Downloading mutations...")
    mut_rows = download_csv(download_url)
    print(f"    Got {len(mut_rows)} mutation entries")

    # Step 4: Parse and cross-reference
    print("\n[4] Cross-referencing WRN dependency with BRCA status...")

    # Parse WRN scores: depmap_id -> score
    wrn_scores = {}
    for row in wrn_rows:
        # Find the depmap_id column and WRN score column
        depmap_id = row.get("depmap_id") or row.get("DepMap_ID") or row.get("")
        # Find WRN column (might be "WRN" or "WRN (7486)" etc.)
        wrn_val = None
        for k, v in row.items():
            if "WRN" in k.upper() and k not in ("depmap_id", "DepMap_ID",
                                                  "cell_line_name",
                                                  "cell_line_display_name",
                                                  "lineage_1", "lineage_2",
                                                  "lineage_3", "lineage_4"):
                try:
                    wrn_val = float(v)
                except (ValueError, TypeError):
                    continue
        if depmap_id and wrn_val is not None:
            wrn_scores[depmap_id] = {
                "wrn_score": wrn_val,
                "lineage": row.get("lineage_1", ""),
                "name": row.get("cell_line_display_name",
                                row.get("cell_line_name", ""))
            }

    print(f"    Parsed WRN scores for {len(wrn_scores)} cell lines")

    # Parse mutations: identify BRCA1/BRCA2-mutant cell lines
    # Use DepMap's own annotations: likely_lof, tumor_suppressor_high_impact,
    # vep_impact=HIGH, or variant_info containing frameshift/stop_gained/splice
    brca_mutant_lines = set()
    brca1_mutant_lines = set()
    brca2_mutant_lines = set()
    # Also track a broader set (any non-silent)
    brca_any_mut_lines = set()
    brca1_any_mut_lines = set()
    brca2_any_mut_lines = set()

    for row in mut_rows:
        depmap_id = row.get("depmap_id", "")
        gene = row.get("gene", "")
        likely_lof = row.get("likely_lof", "").strip().lower() == "true"
        ts_high = (row.get("tumor_suppressor_high_impact", "").strip().lower()
                   == "true")
        vep_impact = row.get("vep_impact", "").strip().upper()
        var_info = row.get("variant_info", "").lower()

        # Damaging = likely_lof OR tumor_suppressor_high_impact OR HIGH impact
        # OR variant contains frameshift/stop_gained/splice
        is_damaging = (
            likely_lof or ts_high or vep_impact == "HIGH"
            or "frameshift" in var_info or "stop_gained" in var_info
            or "splice" in var_info or "nonsense" in var_info
        )

        if not depmap_id or gene not in ("BRCA1", "BRCA2"):
            continue

        # Track any non-silent mutation
        if gene == "BRCA1":
            brca1_any_mut_lines.add(depmap_id)
            brca_any_mut_lines.add(depmap_id)
        elif gene == "BRCA2":
            brca2_any_mut_lines.add(depmap_id)
            brca_any_mut_lines.add(depmap_id)

        if is_damaging:
            if gene == "BRCA1":
                brca1_mutant_lines.add(depmap_id)
                brca_mutant_lines.add(depmap_id)
            elif gene == "BRCA2":
                brca2_mutant_lines.add(depmap_id)
                brca_mutant_lines.add(depmap_id)

    print(f"    BRCA1 damaging mutations in {len(brca1_mutant_lines)} lines")
    print(f"    BRCA2 damaging mutations in {len(brca2_mutant_lines)} lines")
    print(f"    Any BRCA1/2 damaging in {len(brca_mutant_lines)} lines")
    print(f"    Any BRCA1/2 non-silent in {len(brca_any_mut_lines)} lines")

    # Use damaging set if sufficient, else fall back to any non-silent
    if len(brca_mutant_lines) < 10:
        print("    WARNING: Few damaging mutations. Using all non-silent...")
        brca_mutant_lines = brca_any_mut_lines
        brca1_mutant_lines = brca1_any_mut_lines
        brca2_mutant_lines = brca2_any_mut_lines

    # Step 5: Compare WRN dependency
    print("\n[5] Statistical comparison of WRN dependency...")
    print("    NOTE: Gene Dependency = P(essential), higher = MORE dependent")

    # Split into BRCA-mutant vs WT (only lines with WRN scores)
    wrn_brca_mut = []
    wrn_brca_wt = []
    for depmap_id, info in wrn_scores.items():
        if depmap_id in brca_mutant_lines:
            wrn_brca_mut.append(info["wrn_score"])
        else:
            wrn_brca_wt.append(info["wrn_score"])

    print(f"    Lines with WRN score AND BRCA mut: {len(wrn_brca_mut)}")
    print(f"    Lines with WRN score AND BRCA WT:  {len(wrn_brca_wt)}")

    if len(wrn_brca_mut) < 3:
        print("    ERROR: Too few BRCA-mutant lines with WRN scores. "
              "Cannot perform statistical test.")
        if wrn_rows:
            print(f"    WRN row columns: {list(wrn_rows[0].keys())[:10]}")
        if mut_rows:
            print(f"    Mut row columns: {list(mut_rows[0].keys())[:10]}")
        sys.exit(1)

    wrn_brca_mut = np.array(wrn_brca_mut)
    wrn_brca_wt = np.array(wrn_brca_wt)

    # Gene Dependency: higher = more dependent (probability scale)
    print(f"\n    WRN dependency probability (higher = more dependent):")
    print(f"      BRCA-mut:  mean={wrn_brca_mut.mean():.4f}, "
          f"median={np.median(wrn_brca_mut):.4f}, n={len(wrn_brca_mut)}")
    print(f"      BRCA-WT:   mean={wrn_brca_wt.mean():.4f}, "
          f"median={np.median(wrn_brca_wt):.4f}, n={len(wrn_brca_wt)}")

    # Mann-Whitney U test (one-sided: BRCA-mut MORE dependent = higher scores)
    stat, p_greater = stats.mannwhitneyu(wrn_brca_mut, wrn_brca_wt,
                                         alternative='greater')
    print(f"\n    Mann-Whitney U (one-sided, BRCA-mut > BRCA-WT):")
    print(f"      U = {stat:.1f}, p = {p_greater:.4e}")

    # Effect size: rank-biserial correlation
    n1, n2 = len(wrn_brca_mut), len(wrn_brca_wt)
    r_rb = 1 - (2 * stat) / (n1 * n2)
    print(f"      Rank-biserial r = {r_rb:.4f}")

    # Two-sided for completeness
    _, p_two_sided = stats.mannwhitneyu(wrn_brca_mut, wrn_brca_wt,
                                        alternative='two-sided')
    print(f"      Two-sided p = {p_two_sided:.4e}")

    # Step 5b: Chronos confirmation if available
    if wrn_chronos_rows:
        print("\n[5b] Chronos gene effect confirmation...")
        print("     NOTE: Chronos: more negative = MORE dependent")
        chronos_scores = {}
        for row in wrn_chronos_rows:
            depmap_id = row.get("depmap_id") or row.get("DepMap_ID") or ""
            for k, v in row.items():
                if "WRN" in k.upper() and k not in (
                    "depmap_id", "DepMap_ID", "cell_line_display_name",
                    "cell_line_name", "lineage_1", "lineage_2",
                    "lineage_3", "lineage_4", "lineage_6"):
                    try:
                        chronos_scores[depmap_id] = float(v)
                    except (ValueError, TypeError):
                        pass

        chr_brca_mut = [chronos_scores[d] for d in brca_mutant_lines
                        if d in chronos_scores]
        chr_brca_wt = [chronos_scores[d] for d in chronos_scores
                       if d not in brca_mutant_lines]

        if len(chr_brca_mut) >= 3:
            chr_mut = np.array(chr_brca_mut)
            chr_wt = np.array(chr_brca_wt)
            print(f"     BRCA-mut: mean={chr_mut.mean():.4f}, "
                  f"median={np.median(chr_mut):.4f}, n={len(chr_mut)}")
            print(f"     BRCA-WT:  mean={chr_wt.mean():.4f}, "
                  f"median={np.median(chr_wt):.4f}, n={len(chr_wt)}")
            # One-sided: BRCA-mut more negative (more dependent)
            stat_chr, p_chr = stats.mannwhitneyu(chr_mut, chr_wt,
                                                 alternative='less')
            print(f"     Mann-Whitney U (BRCA-mut < BRCA-WT): "
                  f"p={p_chr:.4e}")

    # Step 6: MSI stratification
    print("\n[6] MSI stratification...")
    # For Gene Dependency (probability), MSI lines have HIGH WRN scores
    # Use threshold of 0.5 to identify likely MSI lines
    wrn_threshold = 0.5
    msi_proxy_lines = {did for did, info in wrn_scores.items()
                       if info["wrn_score"] > wrn_threshold}
    print(f"    Proxy MSI lines (WRN dep prob > {wrn_threshold}): "
          f"{len(msi_proxy_lines)}")

    # MSS-only analysis: exclude likely-MSI lines
    wrn_brca_mut_mss = [wrn_scores[d]["wrn_score"]
                        for d in brca_mutant_lines
                        if d in wrn_scores and d not in msi_proxy_lines]
    wrn_brca_wt_mss = [wrn_scores[d]["wrn_score"]
                       for d in wrn_scores
                       if d not in brca_mutant_lines
                       and d not in msi_proxy_lines]

    print(f"    MSS-only: BRCA-mut n={len(wrn_brca_mut_mss)}, "
          f"BRCA-WT n={len(wrn_brca_wt_mss)}")

    p_mss = None
    r_rb_mss = None
    if len(wrn_brca_mut_mss) >= 3:
        wrn_mut_mss = np.array(wrn_brca_mut_mss)
        wrn_wt_mss = np.array(wrn_brca_wt_mss)
        print(f"      BRCA-mut MSS: mean={wrn_mut_mss.mean():.4f}, "
              f"median={np.median(wrn_mut_mss):.4f}")
        print(f"      BRCA-WT MSS:  mean={wrn_wt_mss.mean():.4f}, "
              f"median={np.median(wrn_wt_mss):.4f}")
        stat_mss, p_mss = stats.mannwhitneyu(wrn_mut_mss, wrn_wt_mss,
                                             alternative='greater')
        r_rb_mss = 1 - (2 * stat_mss) / (len(wrn_mut_mss) * len(wrn_wt_mss))
        print(f"      Mann-Whitney U (one-sided, mut > WT): U={stat_mss:.1f}, "
              f"p={p_mss:.4e}")
        print(f"      Rank-biserial r = {r_rb_mss:.4f}")
    else:
        print("    Too few BRCA-mut MSS lines for stratified test")

    # Step 7: Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    significant = p_greater < 0.05
    print(f"  All lines: BRCA-mut WRN dependency "
          f"{'GREATER' if significant else 'NOT greater'} "
          f"than BRCA-WT (p={p_greater:.4e})")
    if p_mss is not None:
        sig_mss = p_mss < 0.05
        print(f"  MSS-only:  BRCA-mut WRN dependency "
              f"{'GREATER' if sig_mss else 'NOT greater'} "
              f"than BRCA-WT (p={p_mss:.4e})")
    print(f"\n  Interpretation:")
    if significant and (p_mss is not None and p_mss < 0.05):
        print(f"  POSITIVE: WRN dependency enriched in BRCA-mutant lines")
        print(f"  even after excluding MSI-proxy lines → supports BRCA+WRN SL")
    elif significant and (p_mss is None or p_mss >= 0.05):
        print(f"  CONFOUNDED: signal in all lines but absent in MSS-only")
        print(f"  → likely driven by MSI co-occurrence, not direct BRCA+WRN SL")
    else:
        print(f"  NEGATIVE: No evidence of enriched WRN dependency in BRCA-mut")
        print(f"  → DepMap does not support the BRCA+WRN SL prediction")

    # Save results
    results = {
        "analysis": "DepMap WRN dependency vs BRCA1/2 loss",
        "dataset": crispr_ds["display_name"],
        "score_type": "Gene Dependency probability (higher=more dependent)",
        "n_lines_wrn_scored": len(wrn_scores),
        "n_brca_mutant_damaging": len(brca_mutant_lines),
        "n_brca1_mutant": len(brca1_mutant_lines),
        "n_brca2_mutant": len(brca2_mutant_lines),
        "all_lines": {
            "brca_mut_mean": float(wrn_brca_mut.mean()),
            "brca_mut_median": float(np.median(wrn_brca_mut)),
            "brca_wt_mean": float(wrn_brca_wt.mean()),
            "brca_wt_median": float(np.median(wrn_brca_wt)),
            "mann_whitney_U": float(stat),
            "p_one_sided_greater": float(p_greater),
            "p_two_sided": float(p_two_sided),
            "rank_biserial_r": float(r_rb),
        },
        "mss_proxy": {
            "threshold": wrn_threshold,
            "n_msi_proxy": len(msi_proxy_lines),
            "n_brca_mut_mss": len(wrn_brca_mut_mss),
            "n_brca_wt_mss": len(wrn_brca_wt_mss),
            "p_one_sided_greater": float(p_mss) if p_mss is not None else None,
            "rank_biserial_r": (float(r_rb_mss)
                                if r_rb_mss is not None else None),
        }
    }

    out_path = OUTPUT_DIR / "depmap_wrn_brca_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to: {out_path}")


if __name__ == "__main__":
    main()
