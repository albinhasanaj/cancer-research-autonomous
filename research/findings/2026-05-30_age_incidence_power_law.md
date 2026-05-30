# Age-incidence power law: t^(k−1) is asymptotic, not exact in the simulated window

**Date:** 2026-05-30
**Type:** finding (KEEP)
**Thread:** [[00_index]] → multistage carcinogenesis
**Related:** [[2026-05-30_armitage_doll_multistage]] (the prediction),
[[2026-05-30_khit_montecarlo_baseline]] (the data it consumes); closes
[[open_questions]] item 3.

## Question

Item 3: does the simulated age-specific incidence (hazard) of the Armitage–Doll
`k`-ordered-hit model scale as `I(t) ∝ t^(k−1)`, as predicted in
[[2026-05-30_armitage_doll_multistage]]?

## What was done

Two scripts, both reproducible and pure-numpy:

1. `simulations/age_incidence_power_law.py` consumes the per-lineage times in
   `simulations/output/khit_times.csv` (`N = 200_000` lineages per `k`,
   `μ = 0.07/yr`, `k = 2..7`). It bins `T_k` into 1-year bins, forms the
   empirical hazard `ĥ(t) = events_in_bin / (n_at_risk_at_bin_left · Δt)`, and:
   - **Q1 (power-law fit):** on a high-survival window (survival ≥ 0.97) fits
     `log ĥ = a + b·log t`, comparing slope `b` to `k−1`. As a *control* it fits
     the **exact** Erlang hazard on the same bins (`analytic_window_slope`), to
     separate "simulation is wrong" from "window is not in the `μt→0` regime".
   - **Q2 (exactness):** on a broader window (survival ≥ 0.10) compares `ĥ`
     bin-by-bin to the exact Erlang hazard `h(t) = μ^k t^(k−1)e^(−μt)/((k−1)!·S(t))`.

2. `simulations/erlang_hazard_local_slope.py` is the analytic companion (no Monte
   Carlo). For `T ~ Erlang(k, μ)` the **exact local log-log slope** of the hazard
   is, with `x = μt` and `A_k(x) = Σ_{j=0}^{k−1} x^j/j!` (and `A_k′ = A_{k−1}`):

   ```
   s_k(x) = d log h / d log t = (k − 1) − x · A_{k−1}(x) / A_k(x).
   ```

   Limits (derived, then checked numerically): `s_k → k−1` as `x → 0`
   (the power-law exponent) and `s_k → 0` as `x → ∞` (hazard saturates to `μ`).

## Observed output

**Q1 — fitted exponent is well below `k−1`, but matches the exact-Erlang window
slope** (`simulations/output/age_incidence_fits.csv`):

| k | fit slope | k−1 | analytic window slope | fit − analytic | μt_max | R² |
|---|-----------|-----|-----------------------|----------------|--------|------|
| 3 | 1.679 | 2 | 1.711 | −0.033 | 0.665 | 0.9991 |
| 4 | 2.347 | 3 | 2.422 | −0.075 | 1.155 | 0.9971 |
| 5 | 2.904 | 4 | 2.959 | −0.055 | 1.715 | 0.9919 |
| 6 | 3.414 | 5 | 3.505 | −0.090 | 2.275 | 0.9882 |
| 7 | 4.063 | 6 | 3.943 | +0.120 | 2.905 | 0.9896 |

(`k = 2`: too few high-survival bins with ≥ 30 events to fit — n/a.)

**Q2 — the Monte Carlo reproduces the exact Erlang hazard**
(`age_incidence_exact_check.csv`): median relative error ≈ 2% for every `k`;
max 8–38% only in sparse tail bins.

**Analytic local-slope limits** (`erlang_hazard_local_slope.py`): `s_k(10⁻³) =
k−1` to 3 decimals for all `k`; `s_k(100) ≈ 0`. Evaluated at each `k`'s MC
window `μt_max`, the pointwise slope already sits far below `k−1` (e.g. `k = 7`:
`s_7(2.905) = 3.23` vs `k−1 = 6`), bracketing the window-averaged MC fit.

## Interpretation (the recorded claim)

1. **The `t^(k−1)` power law is NOT recovered in the statistically accessible
   window**: the fitted effective exponent is well below `k−1`, and the deficit
   grows with `k` (Δslope −0.32 → −1.94 for `k = 3 → 7`).
2. **This is not a simulation error.** The MC slope matches the exact-Erlang
   local slope on the same bins to within ≈ 0.1 (Q1 control), and Q2 shows the
   MC reproduces the exact Erlang hazard to ~2% median error. The deviation is a
   true property of the model in this regime, not sampling noise or a bug.
3. **Root cause = window, not model.** A high *survival* fraction is **not** the
   same as small `μt`: for larger `k` the survival-≥0.97 window already reaches
   `μt ≈ 1–3`, far outside the `μt → 0` limit where `t^(k−1)` is derived. The
   measured slope is an *effective* exponent on a finite window. The closed-form
   `s_k(x)` proves the true exponent is `k−1` only asymptotically and decays
   smoothly toward 0 as `μt` grows.
4. **The Armitage–Doll asymptotic is therefore confirmed, not falsified** — but
   only as an `μt → 0` statement, which a finite simulated cohort with realistic
   ages cannot fully enter for large `k`.

## What this does NOT show / caveats

- The small-`μt` regime is **statistically inaccessible for large `k`** at
  `N = 200_000`: reaching `k` hits at small `t` is exponentially rare, so bins
  there fall below the 30-event floor. We substantiate `slope → k−1`
  analytically (`s_k(x)`), not by pushing the MC window lower.
- The log-log fit is **unweighted OLS**; sparse bins get equal leverage. We did
  not add weighted/Poisson-GLM fits this iteration — the analytic `s_k(x)` curve
  is the primary substantiation and is fit-free, so this does not affect the
  conclusion. (Possible future robustness check.)
- The binned estimator `ĥ` approximates `(F(t+Δ)−F(t))/(S(t)·Δ)`, not the
  pointwise instantaneous hazard at the bin centre; at 1-year bins with
  `μ = 0.07` this discretisation is minor.
- Still pure Armitage–Doll: no clonal expansion, selection, senescence, or
  tissue cell-pool scaling, so no claim is made about real human age-incidence
  curves (e.g. the old-age plateau), per [[2026-05-30_armitage_doll_multistage]].

## Critic pass (KEEP / DEMOTE / REJECT)

- **Claim:** "Simulated incidence ∝ t^(k−1) over the simulated ages." →
  **REJECT** as stated: the finite-window exponent is below `k−1`.
- **Claim:** "The MC reproduces the exact Erlang hazard." → **KEEP** (Q2,
  ~2% median error; Q1 control slope agreement).
- **Claim:** "The `t^(k−1)` law is the `μt → 0` asymptotic and the deficit is a
  window/effective-exponent effect, not a model or simulation error." →
  **KEEP**, supported by both the MC control slope and the closed-form
  `s_k(x) → k−1` limit.
- No "solved / cure / breakthrough" language; in-silico textbook-model analysis.

## Pointers

- Scripts: `simulations/age_incidence_power_law.py`,
  `simulations/erlang_hazard_local_slope.py`
- Outputs: `simulations/output/age_incidence_fits.csv`,
  `age_incidence_exact_check.csv`, `age_incidence_hazard.csv`,
  `erlang_local_slope_curve.csv`, `erlang_local_slope_at_window.csv`
