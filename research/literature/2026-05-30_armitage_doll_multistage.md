# Armitage–Doll multistage model of carcinogenesis — survey

**Date:** 2026-05-30
**Type:** literature note
**Thread:** [[00_index]] → multistage carcinogenesis
**Related:** [[open_questions]] item 1; sets up items 2 and 3.

## The model (restated)

Armitage & Doll (1954) proposed that a normal cell becomes malignant only
after passing through a fixed sequence of `k` irreversible, rare, heritable
"stages" (typically interpreted today as driver mutations / epigenetic hits).
Each stage `i` occurs in a given cell as a Poisson process with small rate
`μ_i`. Stages must be acquired in order (or at least all of them, with the
ordered version being the canonical derivation).

### Core assumptions

1. **Stages are independent and rare.** `μ_i · t ≪ 1` over a lifetime, so the
   probability of any one stage having occurred by age `t` in a given lineage is
   small.
2. **Stages are sequential / cumulative.** A cell needs all `k` hits; once
   acquired, hits are not lost.
3. **Stage rates are roughly constant over life.** No strong age-dependence of
   `μ_i` itself (this assumption is what later "senescence" extensions relax).
4. **Cell population at risk is approximately constant** (or at least not
   shrinking faster than the hazard grows).
5. **One transformed cell → clinical cancer**, after a roughly fixed lag.

### Age-incidence prediction

Under those assumptions, the probability that a single cell has acquired all
`k` ordered hits by age `t` is approximately

```
P_k(t) ≈ (μ_1 μ_2 … μ_k / k!) · t^k
```

so the **age-specific incidence (hazard) scales as a power law**:

```
I(t) ∝ t^(k − 1)
```

This is the headline empirical prediction. On a log–log plot of incidence vs
age, the slope estimates `k − 1`, giving the number of required stages.
Historically, slopes of ~5–6 were observed for many adult epithelial cancers,
which is where the textbook "6 hits to cancer" figure comes from.

## Empirical status, 70 years on

- **The qualitative shape holds.** A power-law-like rise of incidence with age,
  followed by a plateau / fall in extreme old age, is seen across most adult
  solid tumours. PMID **36307647** (2022, "Age distribution and a multi-stage
  theory of carcinogenesis: 70 years on") reviews that the model still
  organises clinical and molecular observations: timing of carcinogen exposure
  (early vs midlife vs late) has very different impact on lifetime risk
  precisely because of the staged structure.

- **Pan-cancer fit with a senescence factor.** PMID **34695806** fits a
  multistage-senescence variant (Armitage–Doll combined with a Pompei–Wilson
  senescence term) to SEER data across 20+ TCGA cancer types. They find a
  strong linear relation between estimated number of stages and the
  per-stage transition rate, a remarkably consistent senescence tumour-
  suppression factor (~0.0099 ± 0.0005) across non-reproductive cancers, and
  that driver gene mutations account for only ~⅓ of the inferred stages —
  i.e. the rest are presumably epigenetic / micro-environmental / clonal-
  expansion steps that the original model lumps into `k`.

- **Asymptotic relative-risk results.** PMID **29383584** proves, for a
  simplified Armitage–Doll model formulated as a generalised Erlang process,
  asymptotic relative-risk results consistent with large clinical studies of
  former smokers and transplant recipients (long-tail elevated risk after
  exposure ceases). Importantly, the paper also shows that some of these
  theorems do **not** extend to other variants — the model is sensitive to
  exactly which "simplified" form is used.

- **Why pure mutation-rate scaling is insufficient.** PMID **28439564**
  reviews phenomena the strict mutation-centric Armitage–Doll picture cannot
  explain on its own: Peto's paradox (no scaling of cancer with body size),
  and the scaling of incidence with species lifespan rather than chronological
  age. Their argument is that physiological aging and evolved tumour
  suppression have to be added to the multistage skeleton.

- **Weibull-like fit and parameter interpretation.** PMID **20838610** derives
  a three-parameter Weibull-like hazard from the Armitage–Doll concept plus a
  Poisson assumption on the number of transformed clones, and shows it fits
  SEER lung-cancer hazards (white men and women, 1975–2004) well. Parameters
  map to: `r` = number of carcinogenic stages, `λ` = mean clones produced per
  year from mutated cells, plus an offset for fraction-ever-affected. They
  also note an additional parameter `A` (age at onset of carcinogenesis) is
  needed for good fits, and that across sexes `r` and `λ` look similar while
  `A` and the prevalence offset differ.

## Implications for the next iterations

The model gives a sharp, falsifiable, single-number prediction:

> **If carcinogenesis requires `k` ordered rare hits, the age-specific
> incidence on a log–log scale should rise with slope `k − 1`.**

This sets up [[open_questions]] item 2 (build a Monte Carlo of a `k`-stage
clonal-evolution model and record time-to-malignancy) and item 3 (check
whether the simulated age-incidence curve obeys `I(t) ∝ t^(k−1)`, and what
exponent is recovered).

Caveats already visible in the literature, to keep honest in items 2 & 3:

- Real incidence curves bend over / decline at very old age — pure Armitage–
  Doll without a senescence / cell-pool term will NOT reproduce that tail.
- Driver mutations alone are not enough "hits" to match inferred `k` for many
  tumours (PMID 34695806); the model's `k` is an effective stage count, not
  literally the number of point mutations in driver genes.
- The model assumes a constant population of at-risk cells; tissues with
  major clonal expansion (e.g. haematopoietic) violate this.

## Citations (all PMIDs fetched via `pubmed_fetch` this iteration)

- PMID **36307647** — Age distribution and a multi-stage theory of
  carcinogenesis: 70 years on.
- PMID **34695806** — Profound synchrony of age-specific incidence rates and
  tumor suppression … multistage-senescence model.
- PMID **29383584** — Asymptotic relative-risk results from a simplified
  Armitage and Doll model of carcinogenesis.
- PMID **28439564** — The evolution of lifespan and age-dependent cancer
  risk.
- PMID **20838610** — Weibull-like model of cancer development in aging.

The original Armitage & Doll (1954) *Br J Cancer* paper is referenced by all
of the above but was not directly fetched this iteration; treat the
restatement above as the consensus form used by these modern reviews, not as
a direct quote of the 1954 paper.

## Critic pass (KEEP / DEMOTE / REJECT)

- **Claim:** "Armitage–Doll predicts `I(t) ∝ t^(k−1)`." → **KEEP.** Stated as
  the prediction of the model under its stated assumptions, not as a claim
  about reality. Consistent with all five fetched abstracts.
- **Claim:** "The model still organises observations 70 years on." →
  **KEEP**, attributed to PMID 36307647.
- **Claim:** "Pure mutation-rate scaling is insufficient; senescence / cell-
  pool effects are needed for the old-age fall-off." → **KEEP**, attributed
  to PMIDs 34695806, 28439564, 20838610.
- **Claim:** "Driver mutations only account for ~⅓ of inferred stages." →
  **KEEP**, but explicitly attributed to PMID 34695806's fit, not asserted
  generally.
- **Falsifier for the next iteration:** if the Monte Carlo of item 2,
  implemented under the model's own assumptions, does not yield a log–log
  slope ≈ `k − 1` over the young/middle-age range, either the implementation
  or the textbook restatement is wrong — log honestly either way.

No "solved / cure / breakthrough" language used. Scope respected (in-silico
literature synthesis only).
