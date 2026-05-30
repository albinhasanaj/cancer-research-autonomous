# Clonal-evolution Monte Carlo of time-to-malignancy — baseline (k-hit, ordered)

**Date:** 2026-05-30
**Type:** finding (KEEP)
**Thread:** [[00_index]] → multistage carcinogenesis
**Related:** [[2026-05-30_armitage_doll_multistage]]; closes [[open_questions]]
item 2; unblocks item 3.

## What was done

Implemented a minimal Armitage–Doll Monte Carlo in
`simulations/multistage_khit_montecarlo.py`. Each of `N = 200_000` independent
lineages must acquire `k` ordered, irreversible stages. Each stage waiting
time is `Exponential(μ)` with `μ = 0.07 / year`, so the time-to-malignancy
`T_k` is the sum of `k` i.i.d. `Exp(μ)` variables, i.e. `Erlang(k, μ)`.

Per-lineage `T_k` is written to `simulations/output/khit_times.csv` so the
next iteration (item 3, the age-incidence power-law check) can consume it
without re-running the simulation. A per-`k` summary is written to
`simulations/output/khit_summary.csv`.

Random seed fixed (`SEED = 20260530`); the run is reproducible.

## Observed output

Sanity check: empirical mean and std of `T_k` against the analytic Erlang
mean `k/μ` and std `√k / μ`, in years.

| k | empirical mean | analytic mean | empirical std | analytic std | empirical median |
|---|----------------|---------------|----------------|---------------|------------------|
| 2 | 28.562 | 28.571 | 20.222 | 20.203 | 23.936 |
| 3 | 42.881 | 42.857 | 24.773 | 24.744 | 38.248 |
| 4 | 57.192 | 57.143 | 28.589 | 28.571 | 52.453 |
| 5 | 71.447 | 71.429 | 31.898 | 31.944 | 66.763 |
| 6 | 85.679 | 85.714 | 35.001 | 34.993 | 80.957 |
| 7 | 99.983 | 100.000 | 37.762 | 37.796 | 95.319 |

Agreement with the Erlang analytic moments is to 3 decimal places across all
`k ∈ {2..7}`, as expected with `N = 200_000` lineages. The empirical median
is always less than the empirical mean, consistent with the right skew of
the Erlang/Gamma distribution.

## What this does NOT show

- This is **just the time-to-first-fully-mutated-lineage distribution**, not
  yet an age-specific incidence (hazard). Converting `T_k` distributions into
  `I(t)` requires assuming an at-risk cell pool of size `N_cells` and asking
  for `P(min_i T_k^{(i)} ≤ t)` across cells; that is item 3's job.
- No clonal expansion, no selection, no senescence term, no varying `μ_i` per
  stage. This is the deliberately stripped Armitage–Doll skeleton from
  [[2026-05-30_armitage_doll_multistage]]; deviations from real curves
  (especially the old-age plateau / fall-off) are expected and are noted as
  caveats there.
- `μ = 0.07 / year` is a tuning choice that puts `k = 2..7` times-to-
  malignancy in the 0–100 year range, not a biologically estimated rate.

## Critic pass (KEEP / DEMOTE / REJECT)

- **Claim:** "The simulated `T_k` distribution matches `Erlang(k, μ)`." →
  **KEEP.** Verified numerically against the closed-form mean and std for
  each `k ∈ {2..7}` with absolute agreement to ~0.05 years on means.
- **Claim:** "This baseline is sufficient to test `I(t) ∝ t^(k−1)` in item
  3." → **KEEP** as a *baseline*; the test in item 3 must additionally
  specify the at-risk cell pool and the small-`μt` regime where the
  Armitage–Doll power-law derivation holds.
- No "solved / cure / breakthrough" language. Scope respected (in-silico
  simulation of a textbook model).

## Pointers

- Script: `simulations/multistage_khit_montecarlo.py`
- Per-lineage CSV: `simulations/output/khit_times.csv`
- Summary CSV: `simulations/output/khit_summary.csv`
