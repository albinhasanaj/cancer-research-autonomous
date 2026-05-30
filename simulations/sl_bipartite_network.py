"""
Bipartite driver-loss ↔ druggable-target network for synthetic lethality.

Builds a weighted bipartite graph from:
  - SL pairs surveyed in research/literature/2026-05-30_synthetic_lethality_survey.md
  - Published TCGA/COSMIC pan-cancer driver-mutation frequencies

Computes:
  - Target-side degree (how many driver contexts each target covers)
  - Weighted degree (sum of driver frequencies reachable per target)
  - Betweenness centrality on the bipartite projection
  - Population-impact score = Σ freq(driver_i) for each target

Output: simulations/output/sl_network_summary.csv
"""

import csv
import os
from collections import defaultdict

# ── SL edges: (driver_loss, target) ──────────────────────────────────────────
# Grounded in PMID references from the survey note.
SL_EDGES = [
    # BRCA–PARP (PMID 42092061)
    ("BRCA1_loss", "PARP1"),
    ("BRCA2_loss", "PARP1"),
    # MTAP–PRMT5/MAT2A (PMID 42198893)
    ("MTAP_del", "PRMT5"),
    ("MTAP_del", "MAT2A"),
    # MSI-H–WRN (PMID 41962327)
    ("dMMR_MSIH", "WRN"),
    # TP53/ATM–DDR axis (PMID 40759474)
    ("TP53_mut", "ATR"),
    ("TP53_mut", "CHK1"),
    ("TP53_mut", "WEE1"),
    ("ATM_loss", "ATR"),
    ("ATM_loss", "CHK1"),
    ("ATM_loss", "WEE1"),
    # RB1–mitotic kinases (PMID 34359636)
    ("RB1_loss", "AURKA"),
    ("RB1_loss", "AURKB"),
    ("RB1_loss", "PLK1"),
    ("RB1_loss", "TTK"),
    # KRAS–PARP combination (PMID 41735281)
    ("KRAS_mut", "PARP1"),
]

# ── Driver-loss pan-cancer frequencies (approximate % of solid tumours) ──────
# Sources: TCGA pan-cancer (PMID 29625053 Bailey et al. 2018), COSMIC v99.
# These are approximate pan-cancer frequencies used for ranking.
DRIVER_FREQ = {
    "TP53_mut": 0.50,      # ~50% solid tumours
    "KRAS_mut": 0.25,      # ~25% (pancreatic 90%, CRC 40%, NSCLC 30%)
    "MTAP_del": 0.15,      # ~15% (co-deleted with CDKN2A on 9p21)
    "dMMR_MSIH": 0.12,     # ~12-15% CRC/endometrial; ~4% pan-cancer → use 12%
    "RB1_loss": 0.08,      # ~8% pan-cancer (higher in SCLC, retinoblastoma)
    "ATM_loss": 0.07,      # ~7% (prostate, bladder, lung)
    "BRCA1_loss": 0.03,    # ~3% (breast/ovarian germline + somatic)
    "BRCA2_loss": 0.03,    # ~3%
}


def build_network():
    """Build adjacency and compute metrics."""
    # Adjacency: target -> list of (driver, freq)
    target_drivers = defaultdict(list)
    driver_targets = defaultdict(list)

    for driver, target in SL_EDGES:
        freq = DRIVER_FREQ.get(driver, 0.01)
        target_drivers[target].append((driver, freq))
        driver_targets[driver].append(target)

    # ── Target metrics ────────────────────────────────────────────────────────
    target_metrics = []
    for target, drivers in sorted(target_drivers.items()):
        degree = len(drivers)
        weighted_degree = sum(f for _, f in drivers)
        driver_names = [d for d, _ in drivers]
        target_metrics.append({
            "target": target,
            "degree": degree,
            "population_coverage": round(weighted_degree, 3),
            "drivers_covered": "; ".join(driver_names),
        })

    # Sort by population coverage (highest first)
    target_metrics.sort(key=lambda x: -x["population_coverage"])

    # ── Driver metrics ────────────────────────────────────────────────────────
    driver_metrics = []
    for driver, targets in sorted(driver_targets.items()):
        freq = DRIVER_FREQ.get(driver, 0.01)
        driver_metrics.append({
            "driver": driver,
            "frequency": freq,
            "n_targets": len(targets),
            "targets": "; ".join(targets),
        })
    driver_metrics.sort(key=lambda x: -x["frequency"])

    # ── Betweenness centrality (bipartite) ────────────────────────────────────
    # Simple betweenness: for each target, count how many driver-pairs it
    # connects (a target on the shortest path between two drivers in the
    # bipartite projection). In a bipartite graph, a target t connects
    # drivers d_i and d_j iff both share target t → betweenness ∝ C(deg, 2).
    for m in target_metrics:
        d = m["degree"]
        m["betweenness_pairs"] = d * (d - 1) // 2  # driver-pairs bridged

    return target_metrics, driver_metrics


def main():
    target_metrics, driver_metrics = build_network()

    os.makedirs("simulations/output", exist_ok=True)

    # Write target summary
    target_path = "simulations/output/sl_network_targets.csv"
    with open(target_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "target", "degree", "population_coverage",
            "betweenness_pairs", "drivers_covered"])
        w.writeheader()
        w.writerows(target_metrics)

    # Write driver summary
    driver_path = "simulations/output/sl_network_drivers.csv"
    with open(driver_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "driver", "frequency", "n_targets", "targets"])
        w.writeheader()
        w.writerows(driver_metrics)

    # Print results
    print("=" * 70)
    print("BIPARTITE SL NETWORK: TARGET RANKING BY POPULATION COVERAGE")
    print("=" * 70)
    print(f"{'Target':<8} {'Deg':>3} {'Pop.Cov':>8} {'Betw':>5}  Drivers")
    print("-" * 70)
    for m in target_metrics:
        print(f"{m['target']:<8} {m['degree']:>3} "
              f"{m['population_coverage']:>8.3f} "
              f"{m['betweenness_pairs']:>5}  {m['drivers_covered']}")

    print()
    print("=" * 70)
    print("DRIVER-LOSS SIDE: MUTATION FREQUENCY & TARGETABILITY")
    print("=" * 70)
    print(f"{'Driver':<12} {'Freq':>6} {'#Tgt':>4}  Targets")
    print("-" * 70)
    for m in driver_metrics:
        print(f"{m['driver']:<12} {m['frequency']:>6.2f} "
              f"{m['n_targets']:>4}  {m['targets']}")

    print()
    print("KEY FINDINGS:")
    top = target_metrics[0]
    print(f"  Highest-coverage target: {top['target']} "
          f"(covers {top['population_coverage']*100:.1f}% of tumours "
          f"across {top['degree']} driver contexts)")
    print(f"  Output: {target_path}, {driver_path}")


if __name__ == "__main__":
    main()
