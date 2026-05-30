# SCOPE

This project is **in-silico only**. The agent investigates cancer biology
through computation and reasoning — never through physical experiment.

## In bounds

- Mathematical and statistical **modelling** of cancer dynamics.
- **Simulation** (Monte Carlo, agent-based, ODE/PDE, stochastic processes).
- **Literature synthesis** grounded in PubMed (every claim cites a PMID).
- **Hypothesis generation** that is explicitly framed as hypothesis.
- Re-analysis of **published, openly available** quantitative results
  (e.g. age-incidence curves, published parameter estimates).
- Pathway / network / synthetic-lethal analysis using public knowledge.

## Out of bounds

- **No wet-lab protocols** of any kind.
- **Nothing physically hazardous** — no synthesis routes, no lab procedures.
- **No medical advice** and nothing that could be construed as clinical guidance.
- **No "we cured cancer" / "breakthrough" / "solved" claims.** Those words are
  forbidden without a reproducible repo artifact and a passing check.
- No use of non-public, restricted, or patient-identifiable data.

## Tractable first targets

Concrete, single-iteration-friendly starting points (all purely computational):

1. **Multi-hit / Armitage–Doll multistage model** — survey and restate the
   classic multistage theory of carcinogenesis from primary literature.
2. **Clonal-evolution Monte Carlo** — simulate time-to-malignancy as a function
   of the number of required driver "hits".
3. **Age-incidence power law** — compare the simulated incidence-vs-age curve to
   the published power-law form (incidence ∝ age^(k−1) for k hits).
4. **Pathway / synthetic-lethal analysis** — explore known driver pathways and
   candidate synthetic-lethal pairs from public knowledge bases.
