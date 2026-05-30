# simulations/

In-silico simulation scripts. Each script is self-contained, reproducible
(fixed seed), and writes outputs under `simulations/output/` (gitignored data
permitted; small CSVs may be committed if a downstream iteration needs them).

## Index

- `multistage_khit_montecarlo.py` — Armitage–Doll `k`-ordered-hit Monte Carlo
  of time-to-malignancy. Produces `output/khit_times.csv` (per-lineage `T_k`
  for `k = 2..7`) and `output/khit_summary.csv` (per-`k` empirical vs analytic
  Erlang moments). Finding note: [[2026-05-30_khit_montecarlo_baseline]].
- `age_incidence_power_law.py` — item 3 age-incidence check. Consumes
  `output/khit_times.csv`; bins it into an empirical hazard and (Q1) fits the
  log-log slope vs `k−1` on a high-survival window with an exact-Erlang control
  slope, (Q2) checks the empirical hazard against the exact Erlang hazard.
  Produces `output/age_incidence_{fits,exact_check,hazard}.csv`.
- `erlang_hazard_local_slope.py` — analytic companion (no Monte Carlo). Computes
  the closed-form Erlang-hazard local log-log slope `s_k(x)=(k−1)−x·A_{k−1}/A_k`
  on a grid of `x=μt`, showing `s_k→k−1` as `x→0`. Produces
  `output/erlang_local_slope_{curve,at_window}.csv`. Both feed finding note
  [[2026-05-30_age_incidence_power_law]].

## Conventions

- One script = one model / experiment. Split before a script crosses ~200
  lines (see `.github/skills/code-hygiene/SKILL.md`).
- Outputs go to `simulations/output/<descriptive_name>.csv`, never alongside
  the script itself.
- Every script's finding lives in `research/findings/` as a dated note;
  every script is referenced from this index.
