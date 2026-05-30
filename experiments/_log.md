# Experiments Log

One line per iteration. Record dead ends too — so work is never repeated.

Format: `DATE | tried | outcome`

---
2026-05-30 | Surveyed Armitage–Doll multistage model via PubMed (5 PMIDs fetched: 36307647, 34695806, 29383584, 28439564, 20838610) | KEEP; literature note `research/literature/2026-05-30_armitage_doll_multistage.md` written; open-questions item 1 closed; items 2 & 3 (Monte Carlo + power-law check) unblocked.
2026-05-30 | Implemented Armitage–Doll k-hit Monte Carlo `simulations/multistage_khit_montecarlo.py` (μ=0.07/yr, k∈{2..7}, N=200_000 lineages); compared empirical T_k moments to analytic Erlang(k, μ) | KEEP; agreement to 3 decimals across all k; per-lineage CSV `simulations/output/khit_times.csv` written for item 3; finding note `research/findings/2026-05-30_khit_montecarlo_baseline.md`; open-questions item 2 closed; item 3 (age-incidence power-law check) unblocked.
2026-05-30 | Item 3 age-incidence power-law check: built `simulations/age_incidence_power_law.py` (empirical hazard fit vs k−1, + exact-Erlang controls) and analytic companion `simulations/erlang_hazard_local_slope.py` (closed-form local slope s_k(x)=(k−1)−x·A_{k−1}/A_k); re-ran both, verified reproducible | KEEP (honest negative on naive form): finite-window fitted exponent is BELOW k−1 (deficit grows with k) because survival≥0.97 still reaches μt≈1–3; NOT a sim error — MC matches exact Erlang hazard to ~2% median, and s_k(x)→k−1 as x→0 proves t^(k−1) is purely asymptotic. Finding `research/findings/2026-05-30_age_incidence_power_law.md`; item 3 closed; multistage thread complete; new items 4 (cell-pool/old-age plateau) and 5 (synthetic-lethal thread) added.
