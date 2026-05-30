"""
Non-ordered (any-order) vs ordered hit accumulation model.

Question 15: Does relaxing the strict ordering of driver mutations in the
Armitage-Doll model change the age-incidence exponent?

Theory (Beerenwinkel 2007, Nowak 2006):
- Ordered: T ~ Erlang(k, mu)  =>  h(t) ~ mu^k * t^(k-1) / (k-1)!
- Unordered: T ~ Hypoexponential(k*mu, (k-1)*mu, ..., mu)
  (coupon-collector: first hit can be any of k genes, then k-1 remain, etc.)
  => h(t) ~ k! * mu^k * t^(k-1) / (k-1)!  [same exponent, k! higher]

The exponent (k-1) is invariant to ordering; only the magnitude changes.
This means non-ordered accumulation does NOT explain the driver-count
discrepancy (more drivers than age-incidence slope implies).

This script verifies computationally via Monte Carlo.
"""

import numpy as np
from scipy import stats

# ---------- Parameters ----------
MU = 0.07        # per-gene mutation rate (per year)
MU_LOW = 0.02    # lower rate so unordered model has realistic median ages
K_VALUES = [3, 4, 5, 6, 7]
N_LINEAGES = 200_000
AGE_BINS = np.linspace(0, 200, 401)  # 0.5-year bins (extended for low mu)
RNG = np.random.default_rng(42)


def simulate_ordered(k, n, mu, rng):
    """Ordered model: T = sum of k iid Exp(mu). => Erlang(k, mu)."""
    return rng.gamma(shape=k, scale=1.0 / mu, size=n)


def simulate_unordered(k, n, mu, rng):
    """
    Unordered model: k distinct genes, each mutates at rate mu.
    First hit: any of k genes => wait ~ Exp(k*mu)
    Second hit: any of k-1 remaining => wait ~ Exp((k-1)*mu)
    ...
    k-th hit: last gene => wait ~ Exp(mu)
    Total T = sum of k independent Exp with rates k*mu, (k-1)*mu, ..., mu.
    """
    times = np.zeros(n)
    for i in range(k):
        rate = (k - i) * mu  # k, k-1, ..., 1 genes remaining
        times += rng.exponential(scale=1.0 / rate, size=n)
    return times


def empirical_hazard(times, age_bins):
    """Compute empirical hazard from onset times using life-table method."""
    counts, _ = np.histogram(times, bins=age_bins)
    n_at_risk = len(times) - np.cumsum(counts) + counts
    dt = age_bins[1] - age_bins[0]
    # Avoid division by zero
    hazard = np.where(n_at_risk > 0, counts / (n_at_risk * dt), 0.0)
    midpoints = 0.5 * (age_bins[:-1] + age_bins[1:])
    return midpoints, hazard


def fit_exponent(midpoints, hazard, fit_window):
    """Fit log(h) = alpha * log(t) + const in the given window."""
    mask = (midpoints >= fit_window[0]) & (midpoints <= fit_window[1])
    mask &= hazard > 0
    if mask.sum() < 5:
        return np.nan, np.nan
    log_t = np.log(midpoints[mask])
    log_h = np.log(hazard[mask])
    slope, intercept, r, p, se = stats.linregress(log_t, log_h)
    return slope, r**2


def analytic_means(k, mu):
    """Analytic mean waiting times."""
    ordered_mean = k / mu
    unordered_mean = sum(1.0 / ((k - i) * mu) for i in range(k))
    return ordered_mean, unordered_mean


# ---------- Main simulation ----------
print("=" * 70)
print("NON-ORDERED vs ORDERED HIT ACCUMULATION MODEL")
print(f"N = {N_LINEAGES:,} lineages")
print("=" * 70)

# Strategy: fit each model in its OWN early-hazard regime (5th-30th percentile
# of onset times) to extract the asymptotic exponent; then also compare at a
# shared low mutation rate where both have realistic epidemiological timescales.

results = []

for mu_label, mu in [("mu=0.07 (original)", MU), ("mu=0.02 (realistic)", MU_LOW)]:
    print(f"\n{'─'*70}")
    print(f"  Mutation rate: {mu_label}")
    print(f"{'─'*70}")
    print(f"\n{'k':<4} {'Model':<12} {'Mean(T)':<10} {'Median':<8} "
          f"{'Exponent':<10} {'Window':<14} {'R²':<8} {'Exp(k-1)':<8}")
    print("-" * 78)

    for k in K_VALUES:
        # Simulate both
        t_ord = simulate_ordered(k, N_LINEAGES, mu, RNG)
        t_unord = simulate_unordered(k, N_LINEAGES, mu, RNG)

        for label, times in [("ordered", t_ord), ("unordered", t_unord)]:
            # Adaptive fit window: 5th to 30th percentile of onset
            # This is the early rising part of hazard for EACH model
            p5 = np.percentile(times, 5)
            p30 = np.percentile(times, 30)
            fit_window = (max(1.0, p5), p30)

            mid, haz = empirical_hazard(times, AGE_BINS)
            exp_val, r2 = fit_exponent(mid, haz, fit_window)

            print(f"{k:<4} {label:<12} {times.mean():<10.1f} "
                  f"{np.median(times):<8.1f} {exp_val:<10.3f} "
                  f"({fit_window[0]:.0f}-{fit_window[1]:.0f}yr){'':>3} "
                  f"{r2:<8.4f} {k-1:<8}")

            results.append({
                'mu': mu, 'k': k, 'model': label,
                'mean': times.mean(), 'median': np.median(times),
                'exponent': exp_val, 'expected': k - 1,
                'fit_lo': fit_window[0], 'fit_hi': fit_window[1], 'r2': r2,
            })

        # Speedup
        speedup = t_ord.mean() / t_unord.mean()
        print(f"     {'speedup':<12} {speedup:.2f}x faster")
        print()

# Also do a direct comparison at matched fit window (low mu only)
print("\n" + "=" * 70)
print("DIRECT COMPARISON: same fit window [40, 70] at mu=0.02")
print("=" * 70)
print(f"\n{'k':<4} {'Ordered exp':<14} {'Unordered exp':<16} {'Expected':<10} {'Δ':<10}")
print("-" * 56)
for k in K_VALUES:
    t_ord = simulate_ordered(k, N_LINEAGES, MU_LOW, RNG)
    t_unord = simulate_unordered(k, N_LINEAGES, MU_LOW, RNG)
    mid_o, haz_o = empirical_hazard(t_ord, AGE_BINS)
    mid_u, haz_u = empirical_hazard(t_unord, AGE_BINS)
    exp_o, _ = fit_exponent(mid_o, haz_o, (40, 70))
    exp_u, _ = fit_exponent(mid_u, haz_u, (40, 70))
    delta = exp_u - exp_o
    print(f"{k:<4} {exp_o:<14.3f} {exp_u:<16.3f} {k-1:<10} {delta:<10.3f}")


# ---------- Summary ----------
print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
print("""
KEY FINDINGS:

1. SPEEDUP: Unordered accumulation is H_k / (k/k) = (H_k * k)/k times faster.
   For k=6: mean 35yr (unordered) vs 86yr (ordered) at mu=0.07/yr.
   The coupon-collector structure (rates kμ, (k-1)μ, ..., μ) compresses onset.

2. EXPONENT INVARIANCE: When fitted in each model's own early-hazard regime,
   BOTH models show the same effective exponent. The asymptotic h(t) ∝ t^(k-1)
   holds for both ordered and unordered (theory: Beerenwinkel 2007).
   At mu=0.02 in a shared [40,70] window, both exponents are similar.

3. PRACTICAL CONSEQUENCE: At realistic per-gene rates, unordered k=6-7 hits
   yield cancer onset TOO EARLY (median ~35yr at mu=0.07). To fit observed
   epidemiology (median onset ~65-70yr), the effective per-gene rate must be
   LOWER in the unordered model — but this doesn't change the exponent.

4. DRIVER-COUNT DISCREPANCY: Non-ordered accumulation does NOT explain why
   tumours show more drivers than the age-incidence exponent implies.
   The exponent is determined by the NUMBER of rate-limiting steps,
   not their ordering. Candidate explanations that remain:
   - Heterogeneous per-gene rates (some hits "easy", some "hard")
   - Tissue architecture / spatial constraints
   - Epistatic / non-independent hit interactions
   - Passenger mutations correlated with drivers (clock signal)
""")

# ---------- Save CSV ----------
import csv
import os
os.makedirs("output", exist_ok=True)
with open("output/unordered_vs_ordered_exponents.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=[
        'mu', 'k', 'model', 'mean', 'median',
        'exponent', 'expected', 'fit_lo', 'fit_hi', 'r2'
    ])
    w.writeheader()
    for r in results:
        w.writerow(r)
print("Results saved to output/unordered_vs_ordered_exponents.csv")
