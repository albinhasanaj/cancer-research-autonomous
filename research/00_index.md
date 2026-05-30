# 00 — Index (home base)

This is the map of the research vault. Every iteration updates it.

## Navigation

- [[SCOPE]] — what is in and out of bounds
- [[open_questions]] — the priority queue (pick ONE item per iteration)
- `experiments/_log.md` — chronological log of every attempt, including dead ends

## Findings

- [[2026-05-30_khit_montecarlo_baseline]] — Armitage–Doll `k`-ordered-hit
  Monte Carlo of time-to-malignancy (`k = 2..7`, `μ = 0.07/yr`,
  `N = 200_000`). Empirical moments match `Erlang(k, μ)` to 3 decimals.
  Script: `simulations/multistage_khit_montecarlo.py`; output:
  `simulations/output/khit_{times,summary}.csv`.
- [[2026-05-30_age_incidence_power_law]] — age-incidence check (item 3). The
  `t^(k−1)` law is the `μt→0` asymptotic, **not** exact on the simulated window:
  the fitted effective exponent is below `k−1` (deficit grows with `k`), yet the
  MC reproduces the exact Erlang hazard to ~2% (Q2) and the closed-form local
  slope `s_k(x)=(k−1)−x·A_{k−1}/A_k → k−1` as `x→0` confirms the asymptotic.
  Scripts: `simulations/age_incidence_power_law.py`,
  `simulations/erlang_hazard_local_slope.py`.

## Literature notes

- [[2026-05-30_armitage_doll_multistage]] — restatement of the Armitage–Doll
  multistage model and its age-incidence prediction `I(t) ∝ t^(k−1)`, with
  modern status from 5 fetched PMIDs. Sets up open-questions items 2 & 3.

## Active hypotheses

_(none yet — open hypotheses under review will be linked here)_

## Thread map

- **Multistage carcinogenesis thread.** Question 1 (literature, this iter) →
  Question 2 (Monte Carlo of `k`-hit time-to-malignancy) → Question 3
  (compare simulated age-incidence to `t^(k−1)` power law). **All three closed.**
  Thread conclusion: the multistage age-incidence power law is asymptotic
  (`μt→0`); finite cohorts show a lower effective exponent. Next directions are
  open (e.g. add the old-age plateau / cell-pool scaling, or move to a new
  thread such as synthetic-lethal analysis).

## System changes

_(none yet — log any agent self-extension of tools/ or structure here)_
