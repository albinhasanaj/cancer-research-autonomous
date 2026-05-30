---
name: simulation-engines
description: Peer-reviewed, ready-made tumour-evolution and Boolean-network simulators to use INSTEAD of hand-rolling a model from scratch (tugHall, SISTEM, CancerSim, BooLEVARD). Use when an OPEN question needs a clonal-evolution / mutation-accumulation / metastasis / Boolean-signalling simulation — reach for a validated engine first, only hand-roll when none fits.
---

# Simulation engines (don't reinvent the tumour model)

## When to use
You are about to write a tumour-evolution, mutation-accumulation, or Boolean
signalling simulation. Before hand-rolling, check whether a **peer-reviewed**
engine already does it — using one gives you validated dynamics, a citation, and
less code to defend in the critic pass. Hand-roll only when none fits, and say so.

All are install-on-demand (NOT in core `requirements.txt`); install in the
iteration that needs them and record the result in the finding note.

## The engines

| Engine | Lang / install | Use it for |
|---|---|---|
| **tugHall** | R (GitHub `sjp/tugHall`) | hallmarks-of-cancer cell-evolution: phenotypes stochastically determined, hallmarks probabilistically bias phenotype probabilities. Closest peer-reviewed analogue to this repo's hallmark-style models. |
| **SISTEM** | Python (check PyPI/GitHub name) | mutation profiles + simulated read counts with **ground-truth cell lineages** under customizable mutation/selection models, incl. metastasis/migration. Use when you need a known-truth dataset to validate an inference method. |
| **CancerSim** | Python (JOSS; check PyPI name) | 2-D spatial tumour growth, neutral-evolution / power-law allele-frequency questions. |
| **BooLEVARD** | Python (`pip install boolevard`) | counts activating/repressing paths leading to a node's state in a **Boolean** model — directly relevant to this repo's Boolean synthetic-lethality work (e.g. `simulations/stochastic_boolean_sl.py`). Pairs with the Boolean models you already build. |

## How to adopt one (discipline)
1. **Fetch current docs first** (PyPI/GitHub names and APIs drift — see
   `external-apis` skill). Confirm the install name before scripting.
2. Install in the working iteration; if it pulls a heavy stack (R, compilers),
   note that in the finding and consider whether the question justifies it.
3. Write the runnable script under `simulations/` (one verifiable unit per
   iteration) and **trace every empirical claim to that script** + the engine's
   citation — exactly as for hand-rolled sims (`AGENTS.md` > evidence rules).
4. If the engine's result merely re-derives known theory, that's an **ANSWERED**
   triage outcome — log it; don't dress it up as a new finding.

## Don't
- Don't vendor an engine's source into this repo; install it as a dependency.
- Don't trust an engine's defaults blindly — state the parameters you set and why.
- Don't reach for these for questions real data already answers (cBioPortal/DepMap
  via the `cancer-data` skill) — simulate only genuinely OPEN questions.
