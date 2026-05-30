"""
Senescence + competing-mortality extension of the cell-pool multistage model.
Tests whether an age-shrinking at-risk cell pool (senescence) and/or competing
non-cancer mortality can produce the EMPIRICAL late-life peak-and-decline
(peak ~75-90y, decline ≥15%) that frailty alone could not (see item 4 /
2026-05-30-cellpool-frailty-old-age-incidence-deceleration).

MODEL EXTENSION (over cellpool_frailty_incidence.py)
----------------------------------------------------
* Senescence: the effective at-risk cell pool shrinks with age:
      N(t) = N_0 · exp(-lambda_s · max(0, t - t_sen))
  where t_sen is the onset age of senescence-driven pool shrinkage.
* Tissue hazard becomes: h_tissue(t|mu) = N(t) · h_cell(t|mu)
  This eventually DECREASES as N(t) -> 0 even though h_cell(t) still rises.
* Tissue survival: S_tissue(t|mu) = exp(- integral_0^t N(s) h_cell(s|mu) ds)
  (computed by numerical cumulative trapezoid).
* Competing (non-cancer) mortality: Gompertz hazard
      mu_d(t) = a_gom · exp(b_gom · t)
  with a_gom=0.0001/yr, b_gom=0.085/yr (gives ~50% alive at 80y).
  S_alive(t|mu) = S_tissue(t|mu) · S_gompertz(t)   [independent risks]
* Population hazard (with optional frailty cv over mu):
      h_pop(t) = E_mu[h_tissue(t|mu) S_alive(t|mu)] / E_mu[S_alive(t|mu)]

SCENARIOS scanned: combinations of (lambda_s, competing_mort, cv).

Run:  python simulations/cellpool_senescence_incidence.py
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

OUT_DIR = Path(__file__).resolve().parent / "output"

# --- Model parameters ---
K = 6
MU0 = 0.015
N_CELLS = 200
T_SEN = 50.0  # senescence onset age (years)
LAMBDA_S_VALUES = [0.0, 0.01, 0.02, 0.03, 0.04]
CV_VALUES = [0.0, 0.6]  # no frailty vs moderate frailty
COMPETING_MORT = [False, True]

# Gompertz competing-mortality params (standard human all-cause approx)
A_GOM = 0.0001  # baseline hazard at age 0
B_GOM = 0.085   # exponential growth rate

# Age grid (fine for numerical integration)
DT = 0.5
AGES = np.arange(DT, 121.0, DT)
SEED = 20260530


def gamma_mu_grid(mu0: float, cv: float, n: int = 4000):
    """Quadrature grid for mu ~ Gamma(mu0, cv). cv=0 -> point mass."""
    if cv <= 1e-9:
        return np.array([mu0]), np.array([1.0])
    a = 1.0 / (cv * cv)
    theta = mu0 / a
    grid = np.linspace(mu0 / 80.0, mu0 * (1.0 + 12.0 * cv), n)
    log_pdf = (a - 1.0) * np.log(grid) - grid / theta
    w = np.exp(log_pdf - log_pdf.max())
    return grid, w / w.sum()


def erlang_hazard_vec(ages, mu, k):
    """h_cell(t|mu) for Erlang(k, mu), vectorised over ages. Scalar mu."""
    x = mu * ages
    a_k = np.ones_like(x)
    term = np.ones_like(x)
    for j in range(1, k):
        term = term * x / j
        a_k += term
    log_top = (k - 1) * np.log(np.maximum(x, 1e-300)) - math.lgamma(k)
    h_cell = mu * np.exp(log_top) / a_k
    return h_cell  # shape (len(ages),)


def n_pool(ages, lam_s, t_sen):
    """Effective pool size N(t) = N_0 * exp(-lam_s * max(0, t-t_sen))."""
    decay = np.where(ages > t_sen, lam_s * (ages - t_sen), 0.0)
    return N_CELLS * np.exp(-decay)


def gompertz_cum_hazard(ages):
    """Cumulative Gompertz hazard integral_0^t a*exp(b*s) ds."""
    return (A_GOM / B_GOM) * (np.exp(B_GOM * ages) - 1.0)


def compute_scenario(lam_s, cv, comp_mort):
    """Compute population hazard for one scenario. Returns (ages, h_pop, s_pop)."""
    mu_grid, w = gamma_mu_grid(MU0, cv)
    n_t = n_pool(AGES, lam_s, T_SEN)  # (n_ages,)

    # Gompertz survival (all-cause non-cancer)
    if comp_mort:
        s_gom = np.exp(-gompertz_cum_hazard(AGES))
    else:
        s_gom = np.ones_like(AGES)

    # For each mu, compute h_tissue(t) and S_tissue(t) numerically
    numerator = np.zeros_like(AGES)
    denominator = np.zeros_like(AGES)

    for i_mu, mu in enumerate(mu_grid):
        h_cell = erlang_hazard_vec(AGES, mu, K)  # (n_ages,)
        h_tissue = n_t * h_cell  # instantaneous tissue hazard

        # Cumulative tissue hazard by trapezoid rule
        cum_h = np.zeros_like(AGES)
        cum_h[0] = h_tissue[0] * DT
        for j in range(1, len(AGES)):
            cum_h[j] = cum_h[j - 1] + 0.5 * (h_tissue[j - 1] + h_tissue[j]) * DT
        s_tissue = np.exp(-cum_h)

        s_alive = s_tissue * s_gom  # joint survival
        numerator += w[i_mu] * h_tissue * s_alive
        denominator += w[i_mu] * s_alive

    with np.errstate(divide="ignore", invalid="ignore"):
        h_pop = np.where(denominator > 1e-30, numerator / denominator, np.nan)
    s_pop = denominator  # E[S_alive] (unnormalised is fine for shape)

    return h_pop, s_pop


def summarise_scenario(lam_s, cv, comp_mort, h_pop):
    """Extract peak age, decline fraction, etc."""
    finite = np.isfinite(h_pop)
    if not np.any(finite):
        return None
    peak_i = int(np.nanargmax(np.where(finite, h_pop, -np.inf)))
    peak_age = float(AGES[peak_i])
    post = h_pop[peak_i:]
    post_finite = post[np.isfinite(post)]
    if len(post_finite) > 1:
        decline_frac = float((h_pop[peak_i] - np.nanmin(post_finite)) / h_pop[peak_i])
    else:
        decline_frac = 0.0
    return {
        "lambda_s": lam_s,
        "cv": cv,
        "competing_mort": comp_mort,
        "peak_age": peak_age,
        "hazard_at_peak": float(h_pop[peak_i]),
        "post_peak_decline_frac": decline_frac,
        "meets_target": peak_age >= 70.0 and decline_frac >= 0.15,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summaries = []
    haz_rows = []

    for lam_s in LAMBDA_S_VALUES:
        for cv in CV_VALUES:
            for comp in COMPETING_MORT:
                h_pop, s_pop = compute_scenario(lam_s, cv, comp)
                s = summarise_scenario(lam_s, cv, comp, h_pop)
                if s:
                    summaries.append(s)
                # Store hazard curve (subsample to 1-yr for output)
                for i in range(0, len(AGES), int(1.0 / DT)):
                    haz_rows.append({
                        "lambda_s": lam_s, "cv": cv,
                        "competing_mort": comp,
                        "age": float(AGES[i]),
                        "hazard_pop": float(h_pop[i]) if np.isfinite(h_pop[i]) else "",
                    })

    # Write outputs
    sum_path = OUT_DIR / "senescence_summary.csv"
    haz_path = OUT_DIR / "senescence_hazard.csv"
    with sum_path.open("w", newline="") as f:
        w_ = csv.DictWriter(f, fieldnames=list(summaries[0].keys()))
        w_.writeheader(); w_.writerows(summaries)
    with haz_path.open("w", newline="") as f:
        w_ = csv.DictWriter(f, fieldnames=list(haz_rows[0].keys()))
        w_.writeheader(); w_.writerows(haz_rows)

    print(f"Wrote {sum_path}\nWrote {haz_path}")
    print(f"\nParams: k={K}, mu0={MU0}/yr, N0={N_CELLS}, t_sen={T_SEN}y")
    print(f"Gompertz competing mort: a={A_GOM}, b={B_GOM}")
    print(f"\n{'lam_s':>6} {'cv':>4} {'comp':>5} {'peakAge':>8} "
          f"{'decline':>8} {'target':>7}")
    for r in summaries:
        print(f"{r['lambda_s']:>6.3f} {r['cv']:>4.1f} "
              f"{'yes' if r['competing_mort'] else 'no':>5} "
              f"{r['peak_age']:>8.1f} "
              f"{r['post_peak_decline_frac']:>8.3f} "
              f"{'YES' if r['meets_target'] else 'no':>7}")


if __name__ == "__main__":
    main()
