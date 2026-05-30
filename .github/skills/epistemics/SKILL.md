---
name: epistemics
description: How not to fool yourself in an autonomous research loop — the falsifiability gate for simulation results, the novelty-evidence ladder (why a null literature search is weak), confidence tagging + decay so findings stay revisable instead of compounding error, and multiple-testing discipline for wide screens (DepMap/enrichment). Use before recording ANY result, when judging novelty, when building on a prior finding, or when interpreting a screen.
---

# Epistemics: how not to fool yourself

## When to use
Before you record a result, claim novelty, build on an earlier finding, or read a
screen. This is the discipline that stops a fresh-context loop from confidently
constructing an edifice on its own overstatements. AGENTS.md > Epistemic
discipline is the always-on summary; this is the working playbook.

## The one framing
**Output = ranked, confidence-tagged hypotheses for a human to evaluate.** You are
a co-scientist, not an autonomous discoverer (even Google's AI co-scientist keeps a
human in the loop). "Agent generates ranked hypotheses a human then evaluates" =
legitimate. "Sim output IS a finding about cancer" = danger. Keep the human as the
verification layer; never let the loop close on itself.

## 1. The falsifiability gate (a sim result is not a finding)
A simulation reproduces what its structure implies — if you tuned a multi-hit model
to fit the age-incidence curve, of course it fits. Internal consistency is **not**
evidence. For every model/sim claim, answer:

> **What real, external observation would prove this wrong?**

- Names a concrete external test (a DepMap pattern, a TCGA mutation frequency, a
  published rate, a held-out dataset) → it's a **hypothesis with a test**; run the
  test if you can, and tag confidence by the outcome.
- "Nothing — it just has to be self-consistent" → it's a **hypothesis only**.
  Record it as `confidence: speculative`, framed as a question, never as a result.

Prefer testing the falsifier *this iteration* against real data (`cancer-data`
skill) over adding another self-consistent sim. A sim that *survives* an external
test it could have failed is worth ten that only re-derive their own premises.

## 2. The novelty-evidence ladder (a null search is weak)
"No PubMed hits" collapses four different worlds: genuinely novel · your terms
missed it · too obvious to publish · tried, failed, never published. An autonomous
agent *systematically over-claims novelty*. Rank your novelty evidence:

| Strength | What you actually did |
|---|---|
| Very weak | one PubMed query, no hits |
| Weak | a few queries, no hits |
| Moderate | multi-source (PubMed + bioRxiv + web + a review's reference list) + tried synonyms/MeSH + checked whether it's *assumed* (textbook-obvious) |
| Stronger | a provider deep-research pass found no prior art, AND a domain reason it's under-studied rather than known-and-boring |

Rules: vary search terms and synonyms before concluding absence; explicitly ask
"is this null because it's novel, or because it's obvious?"; default to **"plausibly
already known"** unless you reach at least Moderate. Record the queries you ran so
the next iteration doesn't re-derive the same false-novelty.

## 3. Confidence tagging + decay (kill compounding error)
Fresh context + on-disk state means a later iteration reads an earlier
`findings/` note as ground truth and *cites* it. If that note was overstated,
confidence never decays and you build on sand. Fix:

- **Tag every claim** with `confidence: speculative | tentative | supported |
  strong` (see ladder below) and its **falsifier**. `write_note` writes these
  frontmatter fields — fill them honestly.
- **Findings are revisable, not append-only.** When you rely on a prior note,
  re-state its confidence in your own words; if new evidence weakens it, **edit or
  demote the old note** (set `status: demoted`, add a "superseded by [[...]]"
  line) rather than silently contradicting it.
- **Periodic self-challenge is a first-class iteration.** Spending a pass trying to
  *break* a high-leverage earlier claim (re-run with perturbed assumptions, seek
  disconfirming data) is high-value work, recorded like any finding. Keep a
  recurring "audit a prior finding" item in `open_questions.md`.

Confidence ladder:
- **speculative** — hypothesis; no external test, or test not yet run.
- **tentative** — one internal/consistency check or a single weak external signal.
- **supported** — passed an external test it could have failed (real data / a
  falsifier survived), or independently corroborated.
- **strong** — multiple independent lines (data + literature + mechanism) agree;
  rare for this loop. Never use "solved/cure/breakthrough" (AGENTS.md).

## 4. Screens are false-positive factories
A wide scan (DepMap ~18k genes × ~1k lines; enrichment over thousands of sets;
mutation-frequency sweeps) yields chance "hits" constantly. Before calling any
screen hit real:
- **Correct for multiple testing** — Benjamini–Hochberg FDR (`statsmodels`
  `multipletests`), not raw p-values; report q-values and the number of tests.
- **Effect size, not just significance** — a tiny but "significant" dependency is
  usually noise; state the magnitude (e.g. Chronos/CERES gene-effect size).
- **Replication + mechanism + orthogonal evidence** — does it hold across cell
  lines/cohorts? is there a pathway reason? does an independent modality agree
  (expression, a known SL pair, literature)? The canonical SLs (WRN/MSI,
  PARP/BRCA) have all of these; a lone uncorrected hit has none.
- Treat a raw screen hit as a **lead to validate**, recorded `confidence:
  speculative`, never as a result.

## Quick pre-record checklist
1. Is this a sim result with no external falsifier? → label hypothesis, not finding.
2. Am I claiming novelty off a thin search? → climb the ladder or down-rank it.
3. Did I set `confidence` + `falsifier` honestly?
4. Am I citing a prior note as fact without re-checking its confidence?
5. Is this a screen hit without FDR + replication + mechanism? → it's a lead.
6. Does my wording keep me (the human) as the verifier, not the loop?
