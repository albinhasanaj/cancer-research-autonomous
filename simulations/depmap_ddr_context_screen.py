"""
Pan-DepMap SL screen: DDR target dependencies in driver-mutation contexts.

Question (item 12): Do DepMap CRISPR screens confirm that the bipartite
network's top-ranked targets (ATR, CHK1, WEE1 in TP53/ATM-loss context;
PARP1 in BRCA context) show preferential dependency?

Approach:
1. Download Chronos gene effect scores for DDR targets (ATR, CHK1, WEE1, PARP1)
2. Download mutation tables for driver genes (TP53, ATM, BRCA1, BRCA2)
3. For each target×driver pair: Mann-Whitney U comparing gene effect in
   driver-mut vs driver-WT (one-sided: mut more dependent = more negative)
4. Rank all pairs by effect size; compare to bipartite network predictions

Data: DepMap latest available via portal API.
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

# DDR targets to screen (from bipartite network item 7)
TARGET_GENES = ["ATR", "CHEK1", "WEE1", "PARP1"]
# Driver genes whose mutation creates the SL context
DRIVER_GENES = ["TP53", "ATM", "BRCA1", "BRCA2"]

# Expected SL pairs from bipartite network (item 7)
EXPECTED_SL = {
    ("TP53", "ATR"), ("TP53", "CHEK1"), ("TP53", "WEE1"),
    ("ATM", "ATR"), ("ATM", "CHEK1"), ("ATM", "WEE1"),
    ("BRCA1", "PARP1"), ("BRCA2", "PARP1"),
}


def submit_custom_download(dataset_id, feature_labels, add_metadata=True):
    """Submit a custom download task and return the task ID."""
    params = {
        "datasetId": dataset_id,
        "addCellLineMetadata": add_metadata,
        "featureLabels": feature_labels,
        "dropEmpty": True,
    }
    resp = requests.post(f"{BASE_URL}/download/custom", json=params,
                         headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def submit_mutation_download(feature_labels):
    """Submit a mutation table download task."""
    params = {"featureLabels": feature_labels}
    resp = requests.post(f"{BASE_URL}/download/custom_mutation_table",
                         json=params, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def poll_task(task_id, max_wait=180):
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
    reader = csv.DictReader(io.StringIO(resp.text))
    return list(reader)


def get_datasets():
    """List available datasets."""
    resp = requests.get(f"{BASE_URL}/download/datasets", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def find_chronos_dataset(datasets):
    """Find CRISPR Chronos gene effect dataset."""
    for ds in datasets:
        name = (ds.get("display_name") or "").lower()
        if "chronos" in name and "crispr" in name:
            return ds
    # Fallback: any CRISPR dataset that isn't confounders or dependency
    for ds in datasets:
        name = (ds.get("display_name") or "").lower()
        dtype = (ds.get("data_type") or "").lower()
        if "crispr" in dtype and "confounder" not in name and "dependency" not in name:
            return ds
    return None


def parse_gene_scores(rows, gene_list):
    """Parse downloaded CSV rows into {depmap_id: {gene: score}}."""
    scores = {}
    # Identify column names matching our genes
    if not rows:
        return scores
    cols = list(rows[0].keys())
    gene_cols = {}
    for gene in gene_list:
        for col in cols:
            if gene in col.upper() and col not in (
                "depmap_id", "DepMap_ID", "cell_line_display_name",
                "cell_line_name", "lineage_1", "lineage_2",
                "lineage_3", "lineage_4"):
                gene_cols[gene] = col
                break

    for row in rows:
        depmap_id = row.get("depmap_id") or row.get("DepMap_ID") or ""
        if not depmap_id:
            continue
        scores[depmap_id] = {}
        for gene, col in gene_cols.items():
            try:
                scores[depmap_id][gene] = float(row[col])
            except (ValueError, TypeError, KeyError):
                pass
    return scores


def parse_mutations(rows, driver_genes):
    """Parse mutation table into {driver: set of depmap_ids with damaging mut}."""
    mutant_lines = {g: set() for g in driver_genes}
    for row in rows:
        depmap_id = row.get("depmap_id", "")
        gene = row.get("gene", "")
        if not depmap_id or gene not in driver_genes:
            continue
        # Damaging criteria (same as item 11)
        likely_lof = row.get("likely_lof", "").strip().lower() == "true"
        ts_high = (row.get("tumor_suppressor_high_impact", "").strip().lower()
                   == "true")
        vep_impact = row.get("vep_impact", "").strip().upper()
        var_info = row.get("variant_info", "").lower()
        is_damaging = (
            likely_lof or ts_high or vep_impact == "HIGH"
            or "frameshift" in var_info or "stop_gained" in var_info
            or "splice" in var_info or "nonsense" in var_info
        )
        # For TP53: also include hotspot missense (gain-of-function)
        if gene == "TP53" and not is_damaging:
            is_hotspot = row.get("is_hotspot", "").strip().lower() == "true"
            if is_hotspot or vep_impact in ("HIGH", "MODERATE"):
                is_damaging = True
        if is_damaging:
            mutant_lines[gene].add(depmap_id)
    return mutant_lines


def run_comparison(target_scores, mutant_ids, all_ids):
    """Mann-Whitney comparing target gene effect in mut vs WT.

    Chronos: more negative = more dependent.
    One-sided test: mut < WT (mut more dependent).
    """
    mut_vals = [target_scores[d] for d in mutant_ids if d in target_scores]
    wt_vals = [target_scores[d] for d in all_ids
               if d in target_scores and d not in mutant_ids]
    if len(mut_vals) < 5 or len(wt_vals) < 5:
        return None
    mut_arr = np.array(mut_vals)
    wt_arr = np.array(wt_vals)
    stat, p_val = stats.mannwhitneyu(mut_arr, wt_arr, alternative='less')
    n1, n2 = len(mut_arr), len(wt_arr)
    # Rank-biserial: for 'less', r = 1 - 2U/(n1*n2)
    # But U from mannwhitneyu 'less' is U for first sample
    r_rb = 1 - (2 * stat) / (n1 * n2)
    return {
        "n_mut": n1,
        "n_wt": n2,
        "mut_mean": float(mut_arr.mean()),
        "mut_median": float(np.median(mut_arr)),
        "wt_mean": float(wt_arr.mean()),
        "wt_median": float(np.median(wt_arr)),
        "U": float(stat),
        "p_one_sided": float(p_val),
        "rank_biserial_r": float(r_rb),
        "cohen_d": float((wt_arr.mean() - mut_arr.mean())
                         / np.sqrt((mut_arr.var() + wt_arr.var()) / 2)),
    }


def main():
    print("=" * 70)
    print("Pan-DepMap DDR target screen in driver-mutation contexts")
    print("Testing bipartite network predictions (item 7) with CRISPR data")
    print("=" * 70)

    # Step 1: Find Chronos dataset
    print("\n[1] Fetching datasets...")
    datasets = get_datasets()
    chronos_ds = find_chronos_dataset(datasets)
    if not chronos_ds:
        sys.exit("ERROR: Could not find Chronos gene effect dataset")
    print(f"    Using: {chronos_ds['display_name']} (id={chronos_ds['id']})")

    # Step 2: Download target gene effect scores
    print(f"\n[2] Downloading Chronos scores for {TARGET_GENES}...")
    task_data = submit_custom_download(chronos_ds["id"], TARGET_GENES)
    task_id = task_data["id"]
    print(f"    Task: {task_id}")
    result = poll_task(task_id)
    target_rows = download_csv(result["downloadUrl"])
    print(f"    Downloaded {len(target_rows)} cell lines")

    scores = parse_gene_scores(target_rows, TARGET_GENES)
    all_line_ids = set(scores.keys())
    for gene in TARGET_GENES:
        n_with = sum(1 for d in scores if gene in scores[d])
        print(f"    {gene}: {n_with} lines with scores")

    # Step 3: Download driver mutations
    print(f"\n[3] Downloading mutations for {DRIVER_GENES}...")
    task_data = submit_mutation_download(DRIVER_GENES)
    task_id = task_data["id"]
    print(f"    Task: {task_id}")
    result = poll_task(task_id)
    mut_rows = download_csv(result["downloadUrl"])
    print(f"    Downloaded {len(mut_rows)} mutation entries")

    mutant_lines = parse_mutations(mut_rows, DRIVER_GENES)
    for driver in DRIVER_GENES:
        n_in_screen = len(mutant_lines[driver] & all_line_ids)
        print(f"    {driver} damaging mut: {len(mutant_lines[driver])} total, "
              f"{n_in_screen} in screen")

    # Step 4: Systematic comparison — all target × driver pairs
    print(f"\n[4] Comparing gene effect (Chronos) across contexts...")
    print("    Chronos: more negative = more dependent on target")
    print("    H1: driver-mut lines are MORE dependent (lower scores)")
    print()

    results_table = []
    for driver in DRIVER_GENES:
        for target in TARGET_GENES:
            # Get per-line scores for this target
            target_scores = {d: scores[d][target] for d in scores
                             if target in scores[d]}
            res = run_comparison(target_scores, mutant_lines[driver],
                                all_line_ids)
            pair_key = f"{driver}-mut → {target}"
            predicted = (driver, target) in EXPECTED_SL
            if res is None:
                print(f"    {pair_key:25s}  SKIP (too few lines)")
                results_table.append({
                    "driver": driver, "target": target,
                    "predicted_sl": predicted, "result": "insufficient_data"
                })
                continue

            sig = "***" if res["p_one_sided"] < 0.001 else (
                  "**" if res["p_one_sided"] < 0.01 else (
                  "*" if res["p_one_sided"] < 0.05 else "ns"))
            pred_mark = "✓" if predicted else " "
            print(f"  {pred_mark} {pair_key:25s}  d={res['cohen_d']:+.3f}  "
                  f"p={res['p_one_sided']:.2e}  r={res['rank_biserial_r']:+.3f}"
                  f"  n_mut={res['n_mut']:4d}  {sig}")

            results_table.append({
                "driver": driver, "target": target,
                "predicted_sl": predicted, "result": "tested", **res
            })

    # Step 5: Rank by effect size and summarize
    print("\n" + "=" * 70)
    print("RANKINGS by Cohen's d (positive = mut more dependent)")
    print("=" * 70)
    tested = [r for r in results_table if r["result"] == "tested"]
    tested.sort(key=lambda r: r["cohen_d"], reverse=True)
    for i, r in enumerate(tested, 1):
        pred = "PREDICTED" if r["predicted_sl"] else "not predicted"
        sig = "p<0.001" if r["p_one_sided"] < 0.001 else (
              "p<0.01" if r["p_one_sided"] < 0.01 else (
              "p<0.05" if r["p_one_sided"] < 0.05 else "ns"))
        print(f"  {i:2d}. {r['driver']}-mut → {r['target']:6s}  "
              f"d={r['cohen_d']:+.3f}  {sig:8s}  [{pred}]")

    # Summary statistics
    predicted_tested = [r for r in tested if r["predicted_sl"]]
    not_predicted = [r for r in tested if not r["predicted_sl"]]
    print(f"\n  Predicted SL pairs tested: {len(predicted_tested)}")
    if predicted_tested:
        n_sig = sum(1 for r in predicted_tested if r["p_one_sided"] < 0.05)
        mean_d = np.mean([r["cohen_d"] for r in predicted_tested])
        print(f"    Significant (p<0.05): {n_sig}/{len(predicted_tested)}")
        print(f"    Mean Cohen's d: {mean_d:+.3f}")
    if not_predicted:
        n_sig_np = sum(1 for r in not_predicted if r["p_one_sided"] < 0.05)
        mean_d_np = np.mean([r["cohen_d"] for r in not_predicted])
        print(f"  Non-predicted pairs tested: {len(not_predicted)}")
        print(f"    Significant (p<0.05): {n_sig_np}/{len(not_predicted)}")
        print(f"    Mean Cohen's d: {mean_d_np:+.3f}")

    # Save results
    output = {
        "analysis": "Pan-DepMap DDR target screen in driver contexts",
        "dataset": chronos_ds["display_name"],
        "targets": TARGET_GENES,
        "drivers": DRIVER_GENES,
        "expected_sl_pairs": [list(p) for p in EXPECTED_SL],
        "results": results_table,
    }
    out_path = OUTPUT_DIR / "depmap_ddr_context_screen.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to: {out_path}")

    # Also save a CSV summary
    csv_path = OUTPUT_DIR / "depmap_ddr_context_screen.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "driver", "target", "predicted_sl", "n_mut", "n_wt",
            "mut_mean", "wt_mean", "cohen_d", "rank_biserial_r",
            "p_one_sided", "significant"])
        writer.writeheader()
        for r in tested:
            writer.writerow({
                "driver": r["driver"], "target": r["target"],
                "predicted_sl": r["predicted_sl"],
                "n_mut": r["n_mut"], "n_wt": r["n_wt"],
                "mut_mean": f"{r['mut_mean']:.4f}",
                "wt_mean": f"{r['wt_mean']:.4f}",
                "cohen_d": f"{r['cohen_d']:.4f}",
                "rank_biserial_r": f"{r['rank_biserial_r']:.4f}",
                "p_one_sided": f"{r['p_one_sided']:.2e}",
                "significant": r["p_one_sided"] < 0.05,
            })
    print(f"  CSV summary: {csv_path}")


if __name__ == "__main__":
    main()
