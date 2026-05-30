"""
Tissue cell-pool + inter-individual frailty extension of the Armitage-Doll
k-hit model: does it reproduce the old-age deceleration / peak-and-decline of
cancer incidence? (open_questions item 4)

MODEL
-----
* Cell: time-to-malignancy ~ Erlang(k, mu) (k ordered hits, per-stage rate mu).
* Individual = a tissue of N_cells INDEPENDENT cells; cancer onset is the
  minimum over its cells. Because cells are i.i.d., tissue survival is
  S_tissue(t|mu) = S_cell(t|mu)^N and tissue hazard is EXACTLY
  h_tissue(t|mu) = N * h_cell(t|mu).
  The per-cell Erlang hazard is increasing and saturates to mu (Erlang is IFR),
  so a HOMOGENEOUS population gives a monotone-increasing tissue hazard that
  plateaus at N*mu -- deceleration, but never a decline. This is the null.
* Frailty: between individuals, mu ~ Gamma(mean mu0, coefficient of variation cv)
  -- shared by all of one individual's cells (per-cell i.i.d. frailty would
  average out within a large tissue by the LLN, so heterogeneity is placed at
  the individual level, as in the epidemiological frailty literature, PMID
  17722193 / 22306590). The OBSERVED population age-specific incidence rate is
  the survival-weighted mixture hazard
        h_pop(t) = E_mu[ h_ind(t|mu) S_ind(t|mu) ] / E_mu[ S_ind(t|mu) ].
  High-mu individuals are selectively depleted, so h_pop can PEAK then DECLINE.

ASSUMPTION (stated honestly): no competing (non-cancer) mortality. h_pop is the
incidence among cancer-free survivors of a pool that only leaves by cancer, so
it overstates old-age incidence relative to real cohorts (caveat for SEER, PMID
21953606). N_cells is an EFFECTIVE at-risk compartment, not a literal cell count.

WHAT THIS SCRIPT DOES
  1. Exact population hazard h_pop(t) by quadrature over the Gamma(mu) density,
     for cv in {0 (homogeneous), 0.3, 0.6, 0.9, 1.2}. (log-space S_cell^N.)
  2. Genuine cell-level Monte Carlo (draw mu_i, draw N_cells Erlang times, take
     the min) to VALIDATE the analytic h_pop independently.
  3. Reports per cv: median onset age, whether the hazard is monotone, peak age,
     post-peak decline fraction, and MC-vs-analytic agreement.

Run:  python simulations/cellpool_frailty_incidence.py
Outputs (simulations/output/):
  cellpool_frailty_hazard.csv   -- per (cv, age) analytic hazard + survival + MC
  cellpool_frailty_summary.csv  -- per cv: median age, peak, decline, MC error
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

OUT_DIR = Path(__file__).resolve().parent / "output"

K = 6
MU0 = 0.015
N_CELLS = 200
CVS = [0.0, 0.3, 0.6, 0.9, 1.2]
AGES = np.arange(1.0, 121.0, 1.0)
MC_INDIVIDUALS = 60_000
MC_CHUNK = 5_000
SEED = 20260530


def gamma_mu_grid(mu0: float, cv: float, n: int = 6000):
    """Quadrature grid over mu with normalised Gamma(mean=mu0, cv) weights.
    cv == 0 collapses to a single atom at mu0 (homogeneous)."""
    if cv <= 1e-9:
        return np.array([mu0]), np.array([1.0])
    a = 1.0 / (cv * cv)
    theta = mu0 / a
    grid = np.linspace(mu0 / 100.0, mu0 * (1.0 + 14.0 * cv), n)
    log_pdf = (a - 1.0) * np.log(grid) - grid / theta
    w = np.exp(log_pdf - log_pdf.max())
    return grid, w / w.sum()


def cell_log_survival_and_hazard(t: float, mu: np.ndarray, k: int):
    """log S_cell(t|mu) and h_cell(t|mu) for Erlang(k, mu), vectorised over mu."""
    x = mu * t
    a_k = np.ones_like(x)
    term = np.ones_like(x)
    for j in range(1, k):
        term = term * x / j
        a_k += term
    log_s_cell = np.log(a_k) - x
    log_top = (k - 1) * np.log(x) - math.lgamma(k)
    h_cell = mu * np.exp(log_top) / a_k
    return log_s_cell, h_cell


def analytic_pop_curve(ages, k, n_cells, mu_grid, w):
    """Survival-weighted mixture: h_pop(t) and S_pop(t) over ages."""
    h = np.empty_like(ages)
    s = np.empty_like(ages)
    for i, t in enumerate(ages):
        log_s_cell, h_cell = cell_log_survival_and_hazard(t, mu_grid, k)
        s_ind = np.exp(n_cells * log_s_cell)
        h_ind = n_cells * h_cell
        s_pop = float(np.sum(w * s_ind))
        s[i] = s_pop
        h[i] = float(np.sum(w * h_ind * s_ind) / s_pop) if s_pop > 0 else np.nan
    return h, s


def mc_pop_hazard(ages, k, n_cells, mu0, cv, rng):
    """Cell-level MC: draw mu_i, draw n_cells Erlang(k,mu_i) times, onset = min.
    Returns empirical age-binned hazard aligned to `ages` (bin midpoints)."""
    edges = np.concatenate(([0.0], ages))  # bins (0,1],(1,2],... midpoints ~ ages-0.5
    counts = np.zeros(len(ages))
    n_total = MC_INDIVIDUALS
    done = 0
    while done < n_total:
        m = min(MC_CHUNK, n_total - done)
        if cv <= 1e-9:
            mu_i = np.full(m, mu0)
        else:
            shape = 1.0 / (cv * cv)
            mu_i = rng.gamma(shape, mu0 / shape, size=m)
        # cell times: (m, n_cells) Erlang(k) = sum of k Exp(1) / mu_i
        scale = 1.0 / mu_i[:, None]
        exp_sum = rng.standard_gamma(k, size=(m, n_cells))  # Gamma(k,1)
        onset = (exp_sum * scale).min(axis=1)
        counts += np.histogram(onset, bins=edges)[0]
        done += m
    cum = np.cumsum(counts)
    at_risk_left = n_total - np.concatenate(([0], cum[:-1]))
    with np.errstate(divide="ignore", invalid="ignore"):
        hazard = counts / at_risk_left  # bin width = 1 yr
    return hazard, counts, at_risk_left


def summarise(cv, ages, h_an, s_an, h_mc, counts):
    finite = np.isfinite(h_an)
    med_age = float(ages[np.argmin(np.abs(s_an - 0.5))])
    peak_i = int(np.nanargmax(np.where(finite, h_an, -np.inf)))
    peak_age = float(ages[peak_i])
    post = h_an[peak_i:]
    decline_frac = float((h_an[peak_i] - np.nanmin(post)) / h_an[peak_i])
    monotone = bool(np.all(np.diff(h_an[finite]) >= -1e-12))
    # MC agreement only where both finite and MC has enough events
    ok = finite & np.isfinite(h_mc) & (counts >= 50)
    rel = np.abs(h_mc[ok] - h_an[ok]) / h_an[ok]
    return {
        "cv": cv,
        "median_onset_age": med_age,
        "monotone_hazard": monotone,
        "peak_age": peak_age,
        "hazard_at_peak": float(h_an[peak_i]),
        "hazard_at_120": float(h_an[-1]),
        "post_peak_decline_frac": decline_frac,
        "mc_median_rel_err": float(np.median(rel)) if rel.size else float("nan"),
        "mc_max_rel_err": float(np.max(rel)) if rel.size else float("nan"),
        "mc_bins_compared": int(ok.sum()),
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    haz_rows, summaries = [], []
    for cv in CVS:
        mu_grid, w = gamma_mu_grid(MU0, cv)
        h_an, s_an = analytic_pop_curve(AGES, K, N_CELLS, mu_grid, w)
        h_mc, counts, at_risk = mc_pop_hazard(AGES, K, N_CELLS, MU0, cv, rng)
        summaries.append(summarise(cv, AGES, h_an, s_an, h_mc, counts))
        for i, t in enumerate(AGES):
            haz_rows.append({
                "cv": cv, "age": float(t),
                "hazard_analytic": float(h_an[i]),
                "survival_analytic": float(s_an[i]),
                "hazard_mc": float(h_mc[i]),
                "events_mc": int(counts[i]),
            })

    haz_path = OUT_DIR / "cellpool_frailty_hazard.csv"
    sum_path = OUT_DIR / "cellpool_frailty_summary.csv"
    with haz_path.open("w", newline="") as f:
        w_ = csv.DictWriter(f, fieldnames=list(haz_rows[0].keys()))
        w_.writeheader(); w_.writerows(haz_rows)
    with sum_path.open("w", newline="") as f:
        w_ = csv.DictWriter(f, fieldnames=list(summaries[0].keys()))
        w_.writeheader(); w_.writerows(summaries)
    print(f"Wrote {haz_path}\nWrote {sum_path}")
    print(f"\nParams: k={K}, mu0={MU0}/yr, N_cells={N_CELLS} (effective pool), "
          f"MC N={MC_INDIVIDUALS}/cv")
    print(f"{'cv':>4} {'medAge':>7} {'monotone':>9} {'peakAge':>8} "
          f"{'decline':>8} {'mc_medErr':>10} {'mc_maxErr':>10}")
    for r in summaries:
        print(f"{r['cv']:>4.1f} {r['median_onset_age']:>7.0f} "
              f"{str(r['monotone_hazard']):>9} {r['peak_age']:>8.0f} "
              f"{r['post_peak_decline_frac']:>8.3f} "
              f"{r['mc_median_rel_err']:>10.4f} {r['mc_max_rel_err']:>10.4f}")


if __name__ == "__main__":
    main()
