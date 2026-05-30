"""
Clonal-evolution Monte Carlo of time-to-malignancy under the Armitage-Doll
k-ordered-hit model.

Model (as restated in research/literature/2026-05-30_armitage_doll_multistage.md):

  A cell lineage must acquire k irreversible "stages" in order. Stage i is
  acquired in a given lineage as a Poisson process with rate mu (per year).
  The waiting time for stage i is Exponential(mu). Time-to-malignancy T_k for
  one lineage is therefore the sum of k i.i.d. Exponential(mu) variables,
  i.e. Gamma/Erlang(shape=k, rate=mu).

  This script samples T_k empirically for a range of k, summarises the
  distributions, and writes the per-lineage times to CSV so that
  open_questions item 3 (age-incidence power-law check) can consume them
  without re-running the simulation.

We deliberately keep this minimal and explicit:

  * No clonal expansion, no fitness, no senescence -- pure Armitage-Doll.
  * No cell-population scaling here; that goes into the incidence/hazard
    calculation in item 3.
  * The point is to have a clean, reproducible artifact whose output can be
    compared against the analytic Erlang(k, mu) mean k/mu and variance k/mu^2,
    so any later "incidence ~ t^(k-1)" check is grounded in a known baseline.

Run:
  python simulations/multistage_khit_montecarlo.py

Outputs (in simulations/output/):
  * khit_times.csv     -- one row per (k, lineage) with simulated T_k in years
  * khit_summary.csv   -- per-k empirical vs analytic mean/std/median
"""

from __future__ import annotations

import csv
import math
import os
from pathlib import Path

import numpy as np


# Parameters chosen to land time-to-malignancy in a biologically plausible
# 0-100+ year window for k in {2..7}. mu = 0.07 per year gives mean
# T_k = k/mu = {28.6, 42.9, 57.1, 71.4, 85.7, 100} years for k=2..7.
MU_PER_YEAR = 0.07
K_VALUES = [2, 3, 4, 5, 6, 7]
N_LINEAGES = 200_000
SEED = 20260530

OUT_DIR = Path(__file__).resolve().parent / "output"


def simulate_time_to_malignancy(k: int, mu: float, n: int, rng: np.random.Generator) -> np.ndarray:
    """Sample n independent T_k = sum of k Exp(mu) waiting times."""
    # Shape (n, k) of exponentials, summed along the k axis.
    waits = rng.exponential(scale=1.0 / mu, size=(n, k))
    return waits.sum(axis=1)


def summarise(k: int, mu: float, times: np.ndarray) -> dict:
    return {
        "k": k,
        "mu_per_year": mu,
        "n_lineages": times.size,
        "empirical_mean_years": float(np.mean(times)),
        "analytic_mean_years": k / mu,
        "empirical_std_years": float(np.std(times, ddof=1)),
        "analytic_std_years": math.sqrt(k) / mu,
        "empirical_median_years": float(np.median(times)),
        "empirical_p05_years": float(np.percentile(times, 5)),
        "empirical_p95_years": float(np.percentile(times, 95)),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    times_path = OUT_DIR / "khit_times.csv"
    summary_path = OUT_DIR / "khit_summary.csv"

    summaries: list[dict] = []

    with times_path.open("w", newline="") as f_times:
        w = csv.writer(f_times)
        w.writerow(["k", "lineage_index", "time_to_malignancy_years"])
        for k in K_VALUES:
            t = simulate_time_to_malignancy(k, MU_PER_YEAR, N_LINEAGES, rng)
            for i, ti in enumerate(t):
                w.writerow([k, i, f"{ti:.6f}"])
            summaries.append(summarise(k, MU_PER_YEAR, t))

    with summary_path.open("w", newline="") as f_sum:
        fieldnames = list(summaries[0].keys())
        w = csv.DictWriter(f_sum, fieldnames=fieldnames)
        w.writeheader()
        for row in summaries:
            w.writerow(row)

    print(f"Wrote {times_path}")
    print(f"Wrote {summary_path}")
    print()
    print("Per-k sanity check (empirical vs analytic mean and std, years):")
    print(f"{'k':>3} {'emp_mean':>10} {'ana_mean':>10} {'emp_std':>10} {'ana_std':>10} {'median':>10}")
    for row in summaries:
        print(
            f"{row['k']:>3} "
            f"{row['empirical_mean_years']:>10.3f} "
            f"{row['analytic_mean_years']:>10.3f} "
            f"{row['empirical_std_years']:>10.3f} "
            f"{row['analytic_std_years']:>10.3f} "
            f"{row['empirical_median_years']:>10.3f}"
        )


if __name__ == "__main__":
    main()
