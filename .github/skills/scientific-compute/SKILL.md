---
name: scientific-compute
description: The in-silico research toolbox — which Python libraries to use for which modelling task (ODE/PDE, Monte Carlo, Bayesian fitting, networks, data, plotting), and how to run compute including GPU checks, package installs, and offloading large jobs. Use when designing or running a simulation, fit, or analysis.
---

# Scientific compute toolbox

## When to use

You're designing or running a simulation, a model fit, or a quantitative
analysis and need to pick the right library and run it in this environment.

## Task → library map

| Task                                       | Library / approach              |
| ------------------------------------------ | ------------------------------- |
| ODE / PDE growth & kinetics models         | `scipy.integrate`, `diffrax`    |
| Agent-based / Monte Carlo clonal evolution | `numpy`, `numba` (JIT speedups) |
| Bayesian parameter fitting / inference     | `PyMC`                          |
| Networks / pathways / graph analysis       | `networkx`                      |
| Tabular data wrangling                     | `pandas`                        |
| Plots & figures                            | `matplotlib`                    |

Prefer vectorized `numpy`; reach for `numba` `@njit` only when a Monte Carlo /
loop is the measured bottleneck.

## Running compute

- **Check for a GPU:** run `nvidia-smi`. If present, GPU-capable libraries
  (e.g. JAX/diffrax, CuPy) can use it; otherwise stay on CPU.
- **CPU count:** `python -c "import os; print(os.cpu_count())"`.
- **Install packages:** `pip install <pkg>` (record any non-obvious install flag
  as a gotcha below). Reproducible deps belong in `requirements.txt`.
- **Save artifacts:** put runnable scripts under `simulations/` and reference the
  script path in the `research/` finding note (every empirical claim must trace
  to a script that produced it).

## Offloading large jobs

If a job is too big for local compute, offload (e.g. Google Colab for a free
GPU): export a self-contained script, run it there, bring back the numeric
outputs/figures, and still commit the script to `simulations/` for
reproducibility.

## Gotchas

- `numba` first-call includes JIT compile time — time the *second* call.
- Set and record random seeds so Monte Carlo runs are reproducible.
- Long runs: respect the iteration model — one verifiable unit per pass; don't
  launch an unbounded simulation inside a single iteration.
- Update this skill as you learn what actually installs and runs cleanly here.
