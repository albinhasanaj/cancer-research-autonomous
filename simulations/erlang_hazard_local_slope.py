"""
Closed-form local log-log slope of the Erlang(k, mu) hazard.

This is the analytic companion to `age_incidence_power_law.py`. It substantiates
the asymptotic Armitage-Doll claim *without* any Monte Carlo, so it cannot be
contaminated by sampling noise or window-statistics artefacts.

Background.
  Time-to-malignancy in the k-ordered-hit model is T ~ Erlang(k, mu). Its hazard
  is
        h(t) = mu * [ x^(k-1) / (k-1)! ] / A_k(x),   x = mu * t,
        A_k(x) = sum_{j=0}^{k-1} x^j / j!.
  The Armitage-Doll age-incidence "power law" h(t) ~ t^(k-1) is the x -> 0 limit
  of this exact hazard.

Local log-log slope.
  s_k(t) := d log h / d log t. Since x = mu*t, d log x = d log t, and
        log h = const + (k-1) log x - log A_k(x),
  with A_k'(x) = sum_{j=1}^{k-1} x^(j-1)/(j-1)! = A_{k-1}(x), we get the exact
  closed form
        s_k(x) = (k - 1) - x * A_{k-1}(x) / A_k(x).

  Limits (proved, not fitted):
    * x -> 0 :  A_{k-1}, A_k -> 1, so s_k -> k - 1   (the power-law exponent).
    * x -> inf: A_{k-1}/A_k -> (k-1)/x, so s_k -> 0  (hazard saturates to mu).
  So the local exponent decreases monotonically from k-1 (at small mu*t) toward 0
  (at large mu*t). The "effective exponent" measured on any finite window with
  mu*t not << 1 is therefore *below* k-1 -- which is exactly what the Monte Carlo
  fit in age_incidence_power_law.py shows. The power law is asymptotic, not exact.

Outputs (in simulations/output/):
  * erlang_local_slope_curve.csv  -- s_k(x) on a grid of x = mu*t, for k = 2..7
  * erlang_local_slope_at_window.csv -- s_k evaluated at the mu*t_max of the MC
    early-fit window (from age_incidence_fits.csv), to connect the two scripts.

Run:
  python simulations/erlang_hazard_local_slope.py
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "output"
FITS_CSV = OUT_DIR / "age_incidence_fits.csv"

K_VALUES = [2, 3, 4, 5, 6, 7]
MU_PER_YEAR = 0.07  # must match the simulation scripts


def partial_exp_sum(x: np.ndarray, terms: int) -> np.ndarray:
    """A_terms(x) = sum_{j=0}^{terms-1} x^j / j!  (truncated exp series)."""
    total = np.zeros_like(x, dtype=float)
    term = np.ones_like(x, dtype=float)  # j = 0 -> 1
    total += term
    for j in range(1, terms):
        term = term * x / j
        total += term
    return total


def erlang_local_slope(x: np.ndarray, k: int) -> np.ndarray:
    """s_k(x) = (k-1) - x * A_{k-1}(x) / A_k(x). A_1(x) = 1."""
    a_k = partial_exp_sum(x, k)
    a_km1 = partial_exp_sum(x, k - 1) if k >= 2 else np.ones_like(x)
    return (k - 1) - x * a_km1 / a_k


def read_window_mu_t_max(path: Path) -> dict[int, float]:
    """Pull the mu*t_max of each k's MC early-fit window, if available."""
    out: dict[int, float] = {}
    if not path.exists():
        return out
    with path.open("r", newline="") as f:
        for row in csv.DictReader(f):
            val = row.get("fit_mu_t_max", "")
            try:
                v = float(val)
            except ValueError:
                continue
            if v == v:  # not NaN
                out[int(row["k"])] = v
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Dense log-spaced grid of x = mu*t spanning the asymptotic-to-saturated range.
    x_grid = np.geomspace(1e-3, 1e2, 400)

    curve_path = OUT_DIR / "erlang_local_slope_curve.csv"
    with curve_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["k", "mu_t", "t_years", "local_slope", "k_minus_1"])
        for k in K_VALUES:
            s = erlang_local_slope(x_grid, k)
            for x, sv in zip(x_grid, s):
                w.writerow([k, f"{x:.6g}", f"{x / MU_PER_YEAR:.6g}",
                            f"{sv:.6f}", k - 1])
    print(f"Wrote {curve_path}")

    # Connect to the MC: local slope at the window's mu*t_max should sit below
    # k-1 and bracket the MC's fitted/analytic window slope.
    window = read_window_mu_t_max(FITS_CSV)
    at_window_path = OUT_DIR / "erlang_local_slope_at_window.csv"
    rows = []
    for k in K_VALUES:
        xw = window.get(k)
        if xw is None:
            continue
        s_at = float(erlang_local_slope(np.array([xw]), k)[0])
        rows.append({
            "k": k,
            "mu_t_max_window": xw,
            "local_slope_at_mu_t_max": s_at,
            "k_minus_1": k - 1,
            "deficit_below_k_minus_1": (k - 1) - s_at,
        })
    if rows:
        with at_window_path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"Wrote {at_window_path}")

    # Console summary: verify the two analytic limits numerically.
    print()
    print("Limit check  s_k(x) -> k-1 as x->0,  s_k(x) -> 0 as x->inf:")
    print(f"{'k':>3} {'s(1e-3)':>10} {'k-1':>5} {'s(1e2)':>10}")
    for k in K_VALUES:
        s_small = float(erlang_local_slope(np.array([1e-3]), k)[0])
        s_large = float(erlang_local_slope(np.array([1e2]), k)[0])
        print(f"{k:>3} {s_small:>10.5f} {k - 1:>5} {s_large:>10.5f}")
    if rows:
        print()
        print("Local slope at the MC early-window mu*t_max (explains MC deficit):")
        print(f"{'k':>3} {'mu*t_max':>9} {'s_local':>9} {'k-1':>5} {'deficit':>9}")
        for r in rows:
            print(f"{r['k']:>3} {r['mu_t_max_window']:>9.3f} "
                  f"{r['local_slope_at_mu_t_max']:>9.3f} {r['k_minus_1']:>5} "
                  f"{r['deficit_below_k_minus_1']:>9.3f}")


if __name__ == "__main__":
    main()
