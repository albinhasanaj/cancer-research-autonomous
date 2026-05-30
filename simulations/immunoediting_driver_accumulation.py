"""
Immunoediting shapes driver accumulation rate (item 21).

Extends the multistage k-hit model with immune negative selection on
immunogenic drivers. Each acquired driver has probability p_neo of generating
a neoantigen; immune surveillance eliminates clones at a rate proportional to
their neoantigen load.

Key questions:
  1. How does immunoediting change time-to-malignancy?
  2. Does it reduce the effective number of drivers in successful tumors?
  3. Does immune strength create a selection bottleneck that effectively
     lowers the driver accumulation rate?

Model structure (per lineage):
  - Clone acquires drivers one-at-a-time at rate mu/yr (same as Armitage-Doll)
  - Each driver independently immunogenic with prob p_neo
  - Clone experiences immune elimination hazard: alpha * n_neo (neoantigen count)
  - Clone must accumulate k drivers without being eliminated
  - Immune escape possible at rate u_escape per year (models HLA-LOH etc.)
  - After escape, no further immune elimination

Grounded in:
  - PMID 32929288 (Lakatos 2020): negative selection on neoantigens
  - PMID 30894752 (Rosenthal 2019): neoantigen depletion in NSCLC
  - PMID 30318143 (Angelova 2018): immunoediting eliminates clones

Author: autonomous research agent
Date: 2026-05-30
"""

import numpy as np
from pathlib import Path
import csv

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def simulate_lineages(
    k: int,
    mu: float,
    p_neo: float,
    alpha: float,
    u_escape: float,
    n_lineages: int,
    rng: np.random.Generator,
) -> dict:
    """
    Simulate n_lineages clones accumulating k drivers under immunoediting.

    Each lineage progresses through states 0..k (number of drivers acquired).
    At each step, it waits for either:
      (a) next driver hit (rate mu)
      (b) immune elimination (rate alpha * n_neo)
      (c) immune escape (rate u_escape)

    Returns dict with arrays of results for successful lineages.
    """
    times = []  # time-to-malignancy for successful lineages
    n_neos_at_malignancy = []  # neoantigen count at malignancy
    escaped_before_k = []  # whether lineage escaped immune surveillance
    eliminated_count = 0

    for _ in range(n_lineages):
        t = 0.0
        n_drivers = 0
        n_neo = 0
        immune_escaped = False

        while n_drivers < k:
            # Rates
            rate_hit = mu
            rate_elim = 0.0 if immune_escaped else alpha * n_neo
            rate_escape = 0.0 if immune_escaped else u_escape
            total_rate = rate_hit + rate_elim + rate_escape

            if total_rate <= 0:
                # Only driver acquisition (no immune pressure yet)
                dt = rng.exponential(1.0 / mu)
                t += dt
                n_drivers += 1
                if rng.random() < p_neo:
                    n_neo += 1
                continue

            # Time to next event
            dt = rng.exponential(1.0 / total_rate)
            t += dt

            # Which event?
            u = rng.random() * total_rate
            if u < rate_hit:
                # New driver acquired
                n_drivers += 1
                if rng.random() < p_neo:
                    n_neo += 1
            elif u < rate_hit + rate_elim:
                # Immune elimination — lineage dies
                eliminated_count += 1
                break
            else:
                # Immune escape
                immune_escaped = True
        else:
            # Successfully accumulated k drivers
            times.append(t)
            n_neos_at_malignancy.append(n_neo)
            escaped_before_k.append(immune_escaped)

    return {
        "times": np.array(times),
        "n_neos": np.array(n_neos_at_malignancy),
        "escaped": np.array(escaped_before_k),
        "n_success": len(times),
        "n_eliminated": eliminated_count,
        "n_lineages": n_lineages,
    }


def run_parameter_scan():
    """Scan over immune strength (alpha) and p_neo."""
    rng = np.random.default_rng(42)

    k = 6
    mu = 0.07  # per year (same as baseline k-hit model)
    n_lineages = 100_000
    u_escape = 0.005  # escape rate per year (rare but possible)

    # Parameter ranges
    alphas = [0.0, 0.01, 0.03, 0.05, 0.1, 0.2, 0.5]
    p_neos = [0.3, 0.5, 0.7]

    results = []
    print(f"{'alpha':>8} {'p_neo':>6} {'P(malig)':>9} {'mean_T':>8} "
          f"{'median_T':>9} {'mean_neo':>9} {'P(esc)':>7} {'T_ratio':>8}")
    print("-" * 80)

    # Baseline (no immune selection)
    baseline = simulate_lineages(k, mu, 0.0, 0.0, 0.0, n_lineages, rng)
    T_baseline = np.median(baseline["times"])

    for p_neo in p_neos:
        for alpha in alphas:
            res = simulate_lineages(k, mu, p_neo, alpha, u_escape, n_lineages, rng)
            p_malig = res["n_success"] / n_lineages
            if res["n_success"] > 0:
                mean_t = np.mean(res["times"])
                median_t = np.median(res["times"])
                mean_neo = np.mean(res["n_neos"])
                p_esc = np.mean(res["escaped"])
                t_ratio = median_t / T_baseline
            else:
                mean_t = median_t = mean_neo = p_esc = t_ratio = float("nan")

            print(f"{alpha:>8.3f} {p_neo:>6.2f} {p_malig:>9.4f} {mean_t:>8.1f} "
                  f"{median_t:>9.1f} {mean_neo:>9.2f} {p_esc:>7.3f} {t_ratio:>8.3f}")
            results.append({
                "alpha": alpha, "p_neo": p_neo, "k": k, "mu": mu,
                "u_escape": u_escape, "p_malignancy": p_malig,
                "mean_T": mean_t, "median_T": median_t,
                "mean_neoantigen": mean_neo, "p_escaped": p_esc,
                "T_ratio_vs_baseline": t_ratio,
            })

    return results, T_baseline


def run_k_scan():
    """How does immunoediting interact with the number of required hits?"""
    rng = np.random.default_rng(123)

    mu = 0.07
    p_neo = 0.5
    alpha = 0.1  # moderate immune pressure
    u_escape = 0.005
    n_lineages = 100_000
    ks = [2, 3, 4, 5, 6, 7]

    print("\n\n=== k-scan (alpha=0.1, p_neo=0.5) ===")
    print(f"{'k':>4} {'P(malig)':>9} {'median_T':>9} {'T_no_imm':>9} "
          f"{'delay_factor':>13} {'mean_neo':>9} {'P(esc)':>7}")
    print("-" * 72)

    results = []
    for k in ks:
        # No immune baseline
        base = simulate_lineages(k, mu, 0.0, 0.0, 0.0, n_lineages, rng)
        T_base = np.median(base["times"])

        # With immunoediting
        res = simulate_lineages(k, mu, p_neo, alpha, u_escape, n_lineages, rng)
        if res["n_success"] > 10:
            median_t = np.median(res["times"])
            delay = median_t / T_base
            mean_neo = np.mean(res["n_neos"])
            p_esc = np.mean(res["escaped"])
            p_malig = res["n_success"] / n_lineages
        else:
            median_t = delay = mean_neo = p_esc = float("nan")
            p_malig = res["n_success"] / n_lineages

        print(f"{k:>4} {p_malig:>9.4f} {median_t:>9.1f} {T_base:>9.1f} "
              f"{delay:>13.3f} {mean_neo:>9.2f} {p_esc:>7.3f}")
        results.append({
            "k": k, "p_malignancy": p_malig, "median_T": median_t,
            "T_no_immune": T_base, "delay_factor": delay,
            "mean_neoantigen": mean_neo, "p_escaped": p_esc,
        })

    return results


def run_neoantigen_depletion_analysis():
    """
    Compare neoantigen counts in successful vs expected under no selection.
    This tests Lakatos 2020's prediction of neoantigen depletion.
    """
    rng = np.random.default_rng(456)

    k = 6
    mu = 0.07
    p_neo = 0.5
    u_escape = 0.005
    n_lineages = 200_000
    alphas = [0.0, 0.05, 0.1, 0.2, 0.5]

    print("\n\n=== Neoantigen depletion analysis (k=6, p_neo=0.5) ===")
    print(f"{'alpha':>8} {'E[neo]_success':>14} {'E[neo]_neutral':>14} "
          f"{'depletion_ratio':>16} {'P(0_neo)':>9}")
    print("-" * 70)

    # Under neutrality, expected neoantigens = k * p_neo = 3.0 (Binomial)
    expected_neutral = k * p_neo

    results = []
    for alpha in alphas:
        res = simulate_lineages(k, mu, p_neo, alpha, u_escape, n_lineages, rng)
        if res["n_success"] > 100:
            mean_neo = np.mean(res["n_neos"])
            depletion = mean_neo / expected_neutral
            p_zero = np.mean(res["n_neos"] == 0)
        else:
            mean_neo = depletion = p_zero = float("nan")

        print(f"{alpha:>8.3f} {mean_neo:>14.3f} {expected_neutral:>14.3f} "
              f"{depletion:>16.4f} {p_zero:>9.4f}")
        results.append({
            "alpha": alpha, "mean_neo_success": mean_neo,
            "expected_neutral": expected_neutral,
            "depletion_ratio": depletion, "p_zero_neo": p_zero,
        })

    return results


def save_results(param_results, k_results, depletion_results, T_baseline):
    """Save main results to CSV."""
    # Parameter scan
    outpath = OUTPUT_DIR / "immunoediting_param_scan.csv"
    with open(outpath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=param_results[0].keys())
        w.writeheader()
        w.writerows(param_results)
    print(f"\nSaved: {outpath}")

    # k-scan
    outpath = OUTPUT_DIR / "immunoediting_k_scan.csv"
    with open(outpath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=k_results[0].keys())
        w.writeheader()
        w.writerows(k_results)
    print(f"Saved: {outpath}")

    # Depletion
    outpath = OUTPUT_DIR / "immunoediting_depletion.csv"
    with open(outpath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=depletion_results[0].keys())
        w.writeheader()
        w.writerows(depletion_results)
    print(f"Saved: {outpath}")


if __name__ == "__main__":
    print("=" * 80)
    print("IMMUNOEDITING AND DRIVER ACCUMULATION (item 21)")
    print("Model: k-hit with immune negative selection on immunogenic drivers")
    print("=" * 80)
    print()

    param_results, T_baseline = run_parameter_scan()
    k_results = run_k_scan()
    depletion_results = run_neoantigen_depletion_analysis()
    save_results(param_results, k_results, depletion_results, T_baseline)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Baseline (no immune) median T for k=6: {T_baseline:.1f} yr")
    print("See output CSVs for full results.")
