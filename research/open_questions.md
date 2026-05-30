# Open Questions — priority queue

Pick the **single** highest-value unchecked item per iteration. Keep items
**independent** where possible so parallel workers can claim different ones
without colliding. To claim an item, check its box and tag it with your worker id.

- [x] **1. Survey the multi-hit / Armitage–Doll multistage model.** Read 3–5
  primary PMIDs (start: `pubmed_search("Armitage Doll multistage carcinogenesis", 5)`).
  Write a `literature` note restating the model, its assumptions, and the
  age-incidence prediction (incidence ∝ age^(k−1) for k stages). Cite every PMID.
  → Done 2026-05-30, see [[2026-05-30_armitage_doll_multistage]]
  (PMIDs 36307647, 34695806, 29383584, 28439564, 20838610).

- [ ] **2. Build a clonal-evolution Monte Carlo of time-to-malignancy vs required
  "hits".** Implement a stochastic simulation (via `run_python`, saved under
  `simulations/`) where a cell lineage acquires driver hits at some rate; record
  the distribution of time-to-malignancy as a function of the number of required
  hits k. Write a `finding` note with the script path and the observed output.

- [ ] **3. Compare the simulated age-incidence curve to the published power law.**
  Take the output of item 2 and test whether incidence scales as age^(k−1).
  Fit/plot, report the exponent, and compare to the Armitage–Doll prediction from
  item 1. Write a `finding` note; log honestly if it does NOT match.
