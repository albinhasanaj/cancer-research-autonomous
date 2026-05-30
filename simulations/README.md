# simulations/

In-silico simulation scripts. Each script is self-contained, reproducible
(fixed seed), and writes outputs under `simulations/output/` (gitignored data
permitted; small CSVs may be committed if a downstream iteration needs them).

## Index

- `multistage_khit_montecarlo.py` — Armitage–Doll `k`-ordered-hit Monte Carlo
  of time-to-malignancy. Produces `output/khit_times.csv` (per-lineage `T_k`
  for `k = 2..7`) and `output/khit_summary.csv` (per-`k` empirical vs analytic
  Erlang moments). Finding note: [[2026-05-30_khit_montecarlo_baseline]].

## Conventions

- One script = one model / experiment. Split before a script crosses ~200
  lines (see `.github/skills/code-hygiene/SKILL.md`).
- Outputs go to `simulations/output/<descriptive_name>.csv`, never alongside
  the script itself.
- Every script's finding lives in `research/findings/` as a dated note;
  every script is referenced from this index.
