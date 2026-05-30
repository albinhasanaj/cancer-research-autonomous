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

## Installed scientific stack

All packages below are in `requirements.txt` and verified importable on this environment (Windows, Python 3.13).

| Library | When to reach for it |
| --- | --- |
| `numpy` | Vectorised array math — the default numerical substrate; use it first |
| `scipy` | ODEs (`integrate`), stats distributions, sparse matrices, signal processing |
| `pandas` | Tabular data wrangling, CSV/Excel I/O, groupby aggregations |
| `statsmodels` | Proper regression/GLM/time-series with p-values and CIs — not hand-rolled |
| `scikit-learn` | ML (classifiers, regressors, clustering) with train/test splits and cross-val |
| `biopython` | Sequence parsing/alignment, NCBI Entrez I/O, PDB structure handling |
| `lifelines` | Kaplan-Meier curves, Cox proportional-hazards survival analysis |
| `gseapy` | Gene-set enrichment analysis (GSEA/GSVA), pathway over-representation |
| `pingouin` | Effect sizes, power analysis, robust parametric and non-parametric tests |
| `matplotlib` | Publication-quality 2-D figures and subplots |

### ML discipline (Tier-3 guard-rail)

ML on self-generated synthetic data proves nothing — only train and validate on
**real external data** with a proper held-out test split. Report effect sizes and
confidence intervals alongside metrics. PyTorch is **not** installed by default;
request it explicitly only when a real labelled dataset needs scale that
scikit-learn cannot handle.

## Gotchas

- `numba` first-call includes JIT compile time — time the *second* call.
- Set and record random seeds so Monte Carlo runs are reproducible.
- Long runs: respect the iteration model — one verifiable unit per pass; don't
  launch an unbounded simulation inside a single iteration.
- Update this skill as you learn what actually installs and runs cleanly here.
