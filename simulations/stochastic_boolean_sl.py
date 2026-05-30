"""
Stochastic Boolean network SL screen — probabilistic extension of the
deterministic DDR model (boolean_sl_network.py, item 8).

Extension (item 10): asynchronous random update + noise on rules →
SL penetrance as a continuous [0,1] score rather than binary.
Compares rank order to DepMap Cohen's d from item 12.

Method:
  - Asynchronous update: each step, one random node is selected for update.
  - Noise: with probability p_noise, the rule output for that node is flipped.
  - Run N_reps replicates per KO combination; penetrance = fraction dying.
  - Steady-state detection: if state unchanged for `patience` steps, stop.

Output: simulations/output/stochastic_sl_penetrance.csv
"""

import csv
import json
import os
import random
from itertools import combinations

import numpy as np

# ── Network definition (same topology as boolean_sl_network.py) ──────────────

NODES = [
    "DNA_damage", "ATM", "ATR", "TP53", "CHK1", "CHK2",
    "WEE1", "BRCA1", "BRCA2", "PARP1", "WRN", "RB1", "PLK1", "CELL_SURV",
]

KO_CANDIDATES = [n for n in NODES if n not in ("DNA_damage", "CELL_SURV")]


def compute_next_node(node, s):
    """Compute deterministic next value for a single node given state s."""
    if node == "DNA_damage":
        return 1
    elif node == "ATM":
        return int(s["DNA_damage"] and s["ATM"])
    elif node == "ATR":
        return int(s["DNA_damage"] and s["ATR"])
    elif node == "TP53":
        return int((s["ATM"] or s["CHK2"]) and s["TP53"])
    elif node == "CHK1":
        return int(s["ATR"] and s["CHK1"])
    elif node == "CHK2":
        return int(s["ATM"] and s["CHK2"])
    elif node == "WEE1":
        return int(s["CHK1"] and s["WEE1"])
    elif node in ("BRCA1", "BRCA2", "PARP1", "WRN", "RB1", "PLK1"):
        return s[node]  # constitutive unless KO
    elif node == "CELL_SURV":
        return _compute_survival(s)
    return s[node]


def _compute_survival(s):
    """Survival logic (same as deterministic model)."""
    hr_repair = s["BRCA1"] and s["BRCA2"]
    alt_repair = s["PARP1"] and s["WRN"]
    repair_ok = hr_repair or alt_repair

    # TP53 activation requires ATM or CHK2
    tp53_active = (s["ATM"] or s["CHK2"]) and s["TP53"]
    g2_checkpoint = s["CHK1"] and s["WEE1"]
    checkpoint_ok = tp53_active or g2_checkpoint

    rb1_stress = not s["RB1"]
    mitotic_ok = s["PLK1"]

    if not repair_ok:
        return 0
    if not checkpoint_ok:
        return 0
    if rb1_stress and not mitotic_ok:
        return 0
    return 1


# ── Stochastic simulation engine ─────────────────────────────────────────────

def make_state(knockouts=None):
    """All nodes ON (functional) except knockouts."""
    state = {n: 1 for n in NODES}
    if knockouts:
        for ko in knockouts:
            state[ko] = 0
    return state


def simulate_stochastic(knockouts=None, p_noise=0.05, max_steps=200,
                        patience=30, rng=None):
    """
    Asynchronous stochastic Boolean simulation.

    At each step:
      1. Pick a random updatable node (excludes KO'd nodes & DNA_damage).
      2. Compute deterministic next value.
      3. With probability p_noise, flip it.
      4. Update CELL_SURV deterministically (output node, no noise).

    Returns final CELL_SURV after convergence or max_steps.
    """
    if rng is None:
        rng = random.Random()

    state = make_state(knockouts)
    ko_set = set(knockouts) if knockouts else set()

    # Nodes eligible for stochastic update (not KO, not input, not output)
    updatable = [n for n in NODES
                 if n not in ko_set and n not in ("DNA_damage", "CELL_SURV")]

    if not updatable:
        # All nodes KO'd — compute survival directly
        state["CELL_SURV"] = _compute_survival(state)
        return state["CELL_SURV"]

    unchanged_count = 0
    prev_state = dict(state)

    for _ in range(max_steps):
        # Pick random node to update
        node = rng.choice(updatable)
        new_val = compute_next_node(node, state)

        # Apply noise
        if rng.random() < p_noise:
            new_val = 1 - new_val

        state[node] = new_val

        # Always update survival deterministically (output readout)
        state["CELL_SURV"] = _compute_survival(state)

        # Convergence check
        if state == prev_state:
            unchanged_count += 1
            if unchanged_count >= patience:
                break
        else:
            unchanged_count = 0
        prev_state = dict(state)

    return state["CELL_SURV"]


def compute_penetrance(knockouts, p_noise=0.05, n_reps=1000, seed=42):
    """Run n_reps stochastic simulations; return fraction that die."""
    rng = random.Random(seed)
    deaths = 0
    for _ in range(n_reps):
        surv = simulate_stochastic(knockouts=knockouts, p_noise=p_noise,
                                   rng=rng)
        if surv == 0:
            deaths += 1
    return deaths / n_reps


# ── Full screen ──────────────────────────────────────────────────────────────

def run_stochastic_screen(p_noise=0.05, n_reps=1000, seed=42):
    """Screen all single and double KOs; return penetrance scores."""
    print(f"Parameters: p_noise={p_noise}, n_reps={n_reps}, seed={seed}")

    # WT baseline
    wt_pen = compute_penetrance(None, p_noise=p_noise, n_reps=n_reps, seed=seed)
    print(f"  WT penetrance (death fraction): {wt_pen:.4f}")

    # Singles
    single_pen = {}
    for node in KO_CANDIDATES:
        pen = compute_penetrance([node], p_noise=p_noise, n_reps=n_reps,
                                 seed=seed)
        single_pen[node] = pen
    print(f"  Single KOs computed: {len(single_pen)}")

    # Doubles — SL penetrance = excess death beyond max of singles
    double_results = []
    pairs = list(combinations(KO_CANDIDATES, 2))
    for i, (n1, n2) in enumerate(pairs):
        pen = compute_penetrance([n1, n2], p_noise=p_noise, n_reps=n_reps,
                                 seed=seed)
        # SL score: excess over max single (capped at 0)
        expected_max = max(single_pen[n1], single_pen[n2])
        sl_score = max(0.0, pen - expected_max)
        double_results.append({
            "node1": n1, "node2": n2,
            "penetrance": pen,
            "single1_pen": single_pen[n1],
            "single2_pen": single_pen[n2],
            "sl_score": sl_score,
        })
        if (i + 1) % 20 == 0:
            print(f"  Double KOs: {i+1}/{len(pairs)}")

    print(f"  Double KOs computed: {len(double_results)}")
    return wt_pen, single_pen, double_results


# ── DepMap comparison ────────────────────────────────────────────────────────

# Map from DepMap (driver, target) → network KO pair (driver_node, target_node)
DEPMAP_TO_NETWORK = {
    ("BRCA1", "PARP1"): ("BRCA1", "PARP1"),
    ("BRCA2", "PARP1"): ("BRCA2", "PARP1"),
    ("BRCA1", "ATR"): ("BRCA1", "ATR"),
    ("BRCA2", "ATR"): ("BRCA2", "ATR"),
    ("BRCA1", "CHEK1"): ("BRCA1", "CHK1"),
    ("BRCA2", "CHEK1"): ("BRCA2", "CHK1"),
    ("BRCA1", "WEE1"): ("BRCA1", "WEE1"),
    ("BRCA2", "WEE1"): ("BRCA2", "WEE1"),
    ("TP53", "PARP1"): ("TP53", "PARP1"),
    ("TP53", "ATR"): ("TP53", "ATR"),
    ("TP53", "CHEK1"): ("TP53", "CHK1"),
    ("TP53", "WEE1"): ("TP53", "WEE1"),
    ("ATM", "PARP1"): ("ATM", "PARP1"),
    ("ATM", "ATR"): ("ATM", "ATR"),
    ("ATM", "CHEK1"): ("ATM", "CHK1"),
    ("ATM", "WEE1"): ("ATM", "WEE1"),
}


def load_depmap_results():
    """Load DepMap Cohen's d from item 12 output CSV."""
    path = "simulations/output/depmap_ddr_context_screen.csv"
    results = {}
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["driver"], row["target"])
            results[key] = float(row["cohen_d"])
    return results


def compare_to_depmap(double_results):
    """Compute Spearman correlation between SL penetrance and DepMap d."""
    depmap = load_depmap_results()

    # Build lookup for network SL scores
    net_lookup = {}
    for r in double_results:
        pair = tuple(sorted([r["node1"], r["node2"]]))
        net_lookup[pair] = r["sl_score"]

    # Match pairs
    matched_net = []
    matched_dep = []
    labels = []
    for dep_key, net_pair in DEPMAP_TO_NETWORK.items():
        pair_norm = tuple(sorted(net_pair))
        if pair_norm in net_lookup and dep_key in depmap:
            matched_net.append(net_lookup[pair_norm])
            matched_dep.append(depmap[dep_key])
            labels.append(f"{dep_key[0]}→{dep_key[1]}")

    if len(matched_net) < 3:
        print("  Too few matched pairs for correlation.")
        return None, labels, matched_net, matched_dep

    # Spearman rank correlation
    from scipy.stats import spearmanr
    rho, pval = spearmanr(matched_net, matched_dep)
    return (rho, pval), labels, matched_net, matched_dep


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("STOCHASTIC BOOLEAN DDR NETWORK — SL PENETRANCE SCREEN")
    print("=" * 70)

    # Run at two noise levels to test robustness
    noise_levels = [0.02, 0.05, 0.10]
    all_screen_results = {}

    for p_noise in noise_levels:
        print(f"\n{'─'*60}")
        print(f"  Noise level p = {p_noise}")
        print(f"{'─'*60}")
        wt_pen, single_pen, double_results = run_stochastic_screen(
            p_noise=p_noise, n_reps=2000, seed=42
        )
        all_screen_results[p_noise] = (wt_pen, single_pen, double_results)

    # Use middle noise level (0.05) as primary
    primary_noise = 0.05
    wt_pen, single_pen, double_results = all_screen_results[primary_noise]

    # Sort by SL score
    ranked = sorted(double_results, key=lambda r: r["sl_score"], reverse=True)

    # Report top SL pairs
    print(f"\n{'='*70}")
    print(f"TOP SL PAIRS (p_noise={primary_noise}, ranked by SL score)")
    print(f"{'='*70}")
    print(f"{'Pair':<20} {'Penetrance':>11} {'Single1':>8} {'Single2':>8} "
          f"{'SL_score':>9}")
    print("-" * 60)
    for r in ranked[:15]:
        pair_str = f"{r['node1']}+{r['node2']}"
        print(f"{pair_str:<20} {r['penetrance']:>11.4f} "
              f"{r['single1_pen']:>8.4f} {r['single2_pen']:>8.4f} "
              f"{r['sl_score']:>9.4f}")

    # Robustness: compare ranks across noise levels
    print(f"\n── Robustness across noise levels ──")
    for p in noise_levels:
        _, _, dr = all_screen_results[p]
        top5 = sorted(dr, key=lambda r: r["sl_score"], reverse=True)[:5]
        pairs_str = ", ".join(f"{r['node1']}+{r['node2']}" for r in top5)
        print(f"  p={p:.2f}: top-5 = {pairs_str}")

    # DepMap comparison
    print(f"\n{'='*70}")
    print("COMPARISON TO DEPMAP COHEN'S d (item 12)")
    print(f"{'='*70}")
    corr_result, labels, net_scores, dep_scores = compare_to_depmap(
        double_results)

    print(f"\n{'Pair':<18} {'Net SL score':>12} {'DepMap d':>9}")
    print("-" * 42)
    for lbl, ns, ds in sorted(zip(labels, net_scores, dep_scores),
                               key=lambda x: x[2], reverse=True):
        print(f"  {lbl:<16} {ns:>12.4f} {ds:>9.4f}")

    if corr_result:
        rho, pval = corr_result
        print(f"\n  Spearman ρ = {rho:.3f}, p = {pval:.4f}")
        print(f"  N pairs matched = {len(labels)}")
        if pval < 0.05:
            print("  → Significant rank correlation between topology-derived "
                  "SL penetrance and functional DepMap effect sizes.")
        else:
            print("  → No significant rank correlation (topology ≠ function "
                  "in this small comparison).")
    else:
        print("  (Insufficient matched pairs for correlation)")

    # Write output CSV
    os.makedirs("simulations/output", exist_ok=True)
    out_path = "simulations/output/stochastic_sl_penetrance.csv"
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["node1", "node2", "penetrance", "single1_pen",
                    "single2_pen", "sl_score", "p_noise"])
        for r in ranked:
            w.writerow([r["node1"], r["node2"], f"{r['penetrance']:.4f}",
                        f"{r['single1_pen']:.4f}", f"{r['single2_pen']:.4f}",
                        f"{r['sl_score']:.4f}", primary_noise])

    # Also save multi-noise results as JSON for reproducibility
    json_path = "simulations/output/stochastic_sl_multi_noise.json"
    json_data = {}
    for p in noise_levels:
        _, sp, dr = all_screen_results[p]
        json_data[str(p)] = {
            "single_penetrance": sp,
            "top10_sl": [
                {"pair": f"{r['node1']}+{r['node2']}",
                 "sl_score": round(r["sl_score"], 4),
                 "penetrance": round(r["penetrance"], 4)}
                for r in sorted(dr, key=lambda x: x["sl_score"],
                                reverse=True)[:10]
            ]
        }
    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)

    print(f"\n  Output: {out_path}")
    print(f"  Multi-noise: {json_path}")
    print(f"\n{'='*70}")
    print("DONE")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
