"""
Age-incidence power-law check for the Armitage-Doll k-hit Monte Carlo.

Consumes the per-lineage simulated times in
`simulations/output/khit_times.csv` (produced by
`multistage_khit_montecarlo.py`) and asks two distinct questions.

Q1. EARLY-REGIME POWER LAW.
    Armitage-Doll predicts h(t) ~ mu^k t^(k-1) / (k-1)! for mu*t << 1.
    We fit log h vs log t on a tight early window (survival fraction
    at bin left edge >= EARLY_SURVIVAL_FLOOR, default 0.97). The
    fitted slope should approach k-1 and the intercept should approach
    log(mu^k / (k-1)!) = k*log(mu) - lgamma(k).

Q2. EXACT ERLANG HAZARD AGREEMENT (BROAD RANGE).
    The Monte Carlo samples T_k = sum of k Exp(mu), i.e. Erlang(k, mu).
    The exact hazard is h_exact(t) = f_Erlang(t) / S_Erlang(t).
    Outside the early window the t^(k-1) power law breaks down because
    S(t) and the e^(-mu t) factor in f start mattering. So we ALSO
    compare empirical hazard to h_exact bin-by-bin (max relative error)
    on a broader window (survival >= BROAD_SURVIVAL_FLOOR, default 0.10),
    to confirm the simulation matches the exact distribution everywhere.

Method (pure numpy, no external fit libs):
  * Bin lineage T_k into 1-year age bins.
  * Empirical hazard at bin midpoint t_m:
        h_hat(t_m) = events_in_bin / (n_at_risk_at_bin_left * bin_width)
  * Drop bins with < MIN_EVENTS_PER_BIN events to keep things stable.
  * Q1: filter to survival >= EARLY_SURVIVAL_FLOOR; least-squares
        fit log(h_hat) = a + b log(t_m); report slope vs (k-1) and
        intercept vs analytic a_pred.
  * Q2: filter to survival >= BROAD_SURVIVAL_FLOOR; compute
        h_exact(t_m) from the exact Erlang(k, mu) PDF/CDF; report the
        max |h_hat - h_exact| / h_exact across bins.

Outputs (in simulations/output/):
  * age_incidence_fits.csv         -- per-k early-regime slope/intercept/R^2 vs prediction
  * age_incidence_exact_check.csv  -- per-k max relative error vs exact Erlang hazard
  * age_incidence_hazard.csv       -- per-(k, bin) empirical hazard with exact reference

Run:
  python simulations/age_incidence_power_law.py
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
TIMES_CSV = HERE / "output" / "khit_times.csv"
OUT_DIR = HERE / "output"

# Tight early window for the Armitage-Doll t^(k-1) approximation.
EARLY_SURVIVAL_FLOOR = 0.97
# Broader window for the exact-Erlang agreement check.
BROAD_SURVIVAL_FLOOR = 0.10
BIN_WIDTH_YEARS = 1.0
MIN_EVENTS_PER_BIN = 30  # avoid log(0)/noise from sparse tails
MU_PER_YEAR = 0.07       # must match the simulation script


def load_times_by_k(path: Path) -> dict[int, np.ndarray]:
    """Stream khit_times.csv into {k: array of T_k}."""
    buckets: dict[int, list[float]] = {}
    with path.open("r", newline="") as f:
        reader = csv.reader(f)
        next(reader)  # header
        for row in reader:
            k = int(row[0])
            t = float(row[2])
            buckets.setdefault(k, []).append(t)
    return {k: np.asarray(v, dtype=float) for k, v in buckets.items()}


def empirical_hazard(times: np.ndarray, bin_width: float, survival_floor: float):
    """
    Return (bin_mid, hazard, n_events, n_at_risk, survival_left) for bins
    where the survival fraction at the bin's left edge is >= survival_floor
    AND the bin has at least MIN_EVENTS_PER_BIN events.
    """
    n_total = times.size
    t_max = times.max()
    edges = np.arange(0.0, t_max + bin_width, bin_width)
    counts, _ = np.histogram(times, bins=edges)
    cum_events = np.cumsum(counts)
    n_at_risk_left = n_total - np.concatenate(([0], cum_events[:-1]))
    survival_left = n_at_risk_left / n_total

    bin_mid = 0.5 * (edges[:-1] + edges[1:])
    with np.errstate(divide="ignore", invalid="ignore"):
        hazard = counts / (n_at_risk_left * bin_width)

    keep = (
        (survival_left >= survival_floor)
        & (counts >= MIN_EVENTS_PER_BIN)
        & (bin_mid > 0)
    )
    return (
        bin_mid[keep],
        hazard[keep],
        counts[keep],
        n_at_risk_left[keep],
        survival_left[keep],
    )


def exact_erlang_hazard(t: np.ndarray, k: int, mu: float) -> np.ndarray:
    """
    h(t) = f(t)/S(t) for T ~ Erlang(k, mu) with integer k.
    f(t) = mu^k t^(k-1) e^(-mu t) / (k-1)!
    S(t) = sum_{j=0}^{k-1} (mu t)^j e^(-mu t) / j!
    The e^(-mu t) cancels:
        h(t) = (mu^k t^(k-1) / (k-1)!) / sum_{j=0}^{k-1} (mu t)^j / j!
    """
    x = mu * t
    log_num = k * math.log(mu) - math.lgamma(k) + (k - 1) * np.log(t)
    num = np.exp(log_num)
    # Sum_{j=0}^{k-1} x^j / j!
    denom = np.zeros_like(x)
    term = np.ones_like(x)  # j=0 -> 1
    denom += term
    for j in range(1, k):
        term = term * x / j
        denom += term
    return num / denom


def loglog_fit(t: np.ndarray, h: np.ndarray) -> tuple[float, float, float]:
    """Least-squares fit log h = a + b log t. Returns (slope, intercept, R^2)."""
    x = np.log(t)
    y = np.log(h)
    b, a = np.polyfit(x, y, 1)
    y_hat = a + b * x
    ss_res = float(np.sum((y - y_hat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return float(b), float(a), r2


def analytic_log_intercept(k: int, mu: float) -> float:
    """Predicted intercept a_pred from h(t) ~ mu^k t^(k-1) / (k-1)!."""
    return k * math.log(mu) - math.lgamma(k)  # log((k-1)!) = lgamma(k)


def main() -> None:
    if not TIMES_CSV.exists():
        raise SystemExit(
            f"Missing {TIMES_CSV}. Run simulations/multistage_khit_montecarlo.py first."
        )
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    times_by_k = load_times_by_k(TIMES_CSV)

    fits: list[dict] = []
    exact_rows: list[dict] = []
    hazard_rows: list[dict] = []

    for k in sorted(times_by_k):
        t_samples = times_by_k[k]

        # --- Q1: early-regime power-law fit
        bin_mid_e, hazard_e, counts_e, at_risk_e, _ = empirical_hazard(
            t_samples, BIN_WIDTH_YEARS, EARLY_SURVIVAL_FLOOR
        )
        a_pred = analytic_log_intercept(k, MU_PER_YEAR)
        if bin_mid_e.size >= 5:
            slope, intercept, r2 = loglog_fit(bin_mid_e, hazard_e)
            # What slope would the EXACT Erlang hazard itself give on this
            # same window? If slope ≈ analytic_window_slope ≠ k-1, the
            # discrepancy is "window too far from mu*t→0", not "MC wrong".
            h_exact_e = exact_erlang_hazard(bin_mid_e, k, MU_PER_YEAR)
            analytic_slope, _, _ = loglog_fit(bin_mid_e, h_exact_e)
            t_min, t_max = float(bin_mid_e.min()), float(bin_mid_e.max())
        else:
            slope = intercept = r2 = analytic_slope = float("nan")
            t_min = t_max = float("nan")
        fits.append({
            "k": k,
            "n_bins_used": int(bin_mid_e.size),
            "early_survival_floor": EARLY_SURVIVAL_FLOOR,
            "fit_t_min_years": t_min,
            "fit_t_max_years": t_max,
            "fit_mu_t_max": (t_max * MU_PER_YEAR) if t_max == t_max else float("nan"),
            "fitted_slope": slope,
            "predicted_slope_k_minus_1": k - 1,
            "analytic_window_slope": analytic_slope,
            "slope_minus_prediction": (slope - (k - 1)) if slope == slope else float("nan"),
            "slope_minus_analytic_window": (slope - analytic_slope) if slope == slope else float("nan"),
            "fitted_intercept": intercept,
            "analytic_intercept": a_pred,
            "intercept_minus_analytic": (intercept - a_pred) if intercept == intercept else float("nan"),
            "r_squared": r2,
            "bin_width_years": BIN_WIDTH_YEARS,
            "min_events_per_bin": MIN_EVENTS_PER_BIN,
        })

        # --- Q2: exact Erlang hazard agreement on a broader window
        bin_mid_b, hazard_b, counts_b, at_risk_b, surv_b = empirical_hazard(
            t_samples, BIN_WIDTH_YEARS, BROAD_SURVIVAL_FLOOR
        )
        h_exact_b = exact_erlang_hazard(bin_mid_b, k, MU_PER_YEAR)
        rel_err = np.abs(hazard_b - h_exact_b) / h_exact_b
        exact_rows.append({
            "k": k,
            "broad_survival_floor": BROAD_SURVIVAL_FLOOR,
            "n_bins_used": int(bin_mid_b.size),
            "t_min_years": float(bin_mid_b.min()) if bin_mid_b.size else float("nan"),
            "t_max_years": float(bin_mid_b.max()) if bin_mid_b.size else float("nan"),
            "max_rel_err_vs_exact": float(rel_err.max()) if rel_err.size else float("nan"),
            "median_rel_err_vs_exact": float(np.median(rel_err)) if rel_err.size else float("nan"),
        })
        for tm, h, c, nr, s, he in zip(
            bin_mid_b, hazard_b, counts_b, at_risk_b, surv_b, h_exact_b
        ):
            hazard_rows.append({
                "k": k,
                "bin_mid_years": float(tm),
                "hazard_per_year_empirical": float(h),
                "hazard_per_year_exact_erlang": float(he),
                "rel_err": float(abs(h - he) / he),
                "survival_left": float(s),
                "events_in_bin": int(c),
                "n_at_risk_left": int(nr),
            })

    fits_path = OUT_DIR / "age_incidence_fits.csv"
    exact_path = OUT_DIR / "age_incidence_exact_check.csv"
    haz_path = OUT_DIR / "age_incidence_hazard.csv"

    for path, rows in [(fits_path, fits), (exact_path, exact_rows), (haz_path, hazard_rows)]:
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"Wrote {path}")

    print()
    print(
        f"Q1: early-regime power-law fit (survival>={EARLY_SURVIVAL_FLOOR}, "
        f"bin={BIN_WIDTH_YEARS}y):"
    )
    print(f"{'k':>3} {'bins':>5} {'t_rng':>10} {'mu*t_max':>9} "
          f"{'slope':>8} {'k-1':>5} {'Δslope':>8} {'Δa':>8} {'R^2':>7}")
    for r in fits:
        trange = (
            f"{r['fit_t_min_years']:.1f}-{r['fit_t_max_years']:.1f}"
            if r['fit_t_min_years'] == r['fit_t_min_years'] else "n/a"
        )
        print(
            f"{r['k']:>3} {r['n_bins_used']:>5} {trange:>10} "
            f"{r['fit_mu_t_max']:>9.3f} "
            f"{r['fitted_slope']:>8.3f} {r['predicted_slope_k_minus_1']:>5} "
            f"{r['slope_minus_prediction']:>8.3f} "
            f"{r['intercept_minus_analytic']:>8.3f} {r['r_squared']:>7.4f}"
        )
    print()
    print(f"Q2: exact Erlang hazard agreement (survival>={BROAD_SURVIVAL_FLOOR}):")
    print(f"{'k':>3} {'bins':>5} {'t_rng':>14} {'max_rel_err':>12} {'med_rel_err':>12}")
    for r in exact_rows:
        trange = f"{r['t_min_years']:.1f}-{r['t_max_years']:.1f}"
        print(
            f"{r['k']:>3} {r['n_bins_used']:>5} {trange:>14} "
            f"{r['max_rel_err_vs_exact']:>12.4f} {r['median_rel_err_vs_exact']:>12.4f}"
        )


if __name__ == "__main__":
    main()
