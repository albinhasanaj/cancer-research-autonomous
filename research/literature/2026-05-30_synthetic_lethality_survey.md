# Synthetic Lethality in Cancer — Survey of Principles and Key Pairs

**Date:** 2026-05-30  
**Type:** literature  
**Thread:** synthetic-lethal  
**Status:** KEEP  

## Definition

Synthetic lethality (SL) is a genetic interaction where the simultaneous loss
of function of two genes kills the cell, while loss of either alone is viable
(PMID 42207998). In cancer therapy, tumour-specific loss of gene A makes the
tumour selectively dependent on gene B; pharmacological inhibition of B then
kills cancer cells while sparing normal tissue with intact A.

## Historical proof-of-concept: BRCA–PARP

The paradigm-defining example: BRCA1/2-deficient cancers cannot perform
homologous recombination (HR) repair; PARP inhibitors trap PARP1 on DNA,
causing replication-coupled double-strand breaks that require HR to resolve →
selective lethality (PMID 42092061). Two decades of clinical translation have
led to approved PARP inhibitors (olaparib, niraparib, rucaparib, talazoparib)
for BRCA-mutant breast, ovarian, prostate, and pancreatic cancers.

**Lessons from BRCA–PARP** (PMID 42092061):

- Proof that germline biomarker → companion diagnostic → targeted therapy works.
- Resistance emerges (BRCA reversion mutations, loss of 53BP1/RIF1, PARP1
  mutations); combination strategies needed.
- Stimulated genome-wide CRISPR screens to discover new SL pairs at scale.

## Established and emerging SL pairs

### 1. MTAP-deletion → PRMT5 inhibition

- **Driver event:** Homozygous deletion of 9p21.3 (CDKN2A/B + MTAP), one of
  the most frequent genomic losses across cancers (~15% of all tumours).
- **Mechanism:** MTAP loss accumulates MTA (methylthioadenosine), which
  partially inhibits PRMT5 in a substrate-competitive manner; tumour cells
  become uniquely dependent on residual PRMT5 activity → pharmacological PRMT5
  inhibition is selectively lethal (PMID 42198893).
- **Agents in trials:** MTA-cooperative PRMT5 inhibitors (e.g. TNG908,
  MRTX1719), MAT2A inhibitors (PMID 42207998).
- **Cancer types:** Glioblastoma, mesothelioma, NSCLC, pancreatic, bladder.

### 2. MSI-H → WRN helicase inhibition

- **Driver event:** Defective mismatch repair (dMMR) / microsatellite
  instability-high (MSI-H), found in ~15% of colorectal, endometrial, gastric
  cancers.
- **Mechanism:** MSI-H genomes accumulate (TA)n dinucleotide repeats that form
  non-B DNA structures during replication; WRN helicase resolves these. WRN
  loss in MSI-H cells → replication fork collapse, DSBs, and apoptosis (PMID
  41962327).
- **Agents in trials:** Covalent and non-covalent WRN inhibitors (early
  clinical phase) (PMID 41962327).
- **Cancer types:** Colorectal, endometrial, gastric, ovarian (MSI-H subset).

### 3. TP53/ATM loss → ATR–CHK1–WEE1 axis inhibition

- **Driver event:** TP53 mutation (most common somatic mutation in cancer,
  ~50% of solid tumours) or ATM loss; both ablate the G1/S checkpoint.
- **Mechanism:** Cells rely entirely on the S/G2 checkpoint (ATR → CHK1 →
  WEE1) to avoid mitotic catastrophe. Inhibiting this axis forces premature
  mitotic entry with unresolved DNA damage → synthetic lethality (PMID
  40759474).
- **Agents in trials:** WEE1i (adavosertib/AZD1775), ATRi (ceralasertib,
  elimusertib), CHK1i (prexasertib) (PMID 40759474).
- **Cancer types:** Broad (ovarian, SCLC, HNSCC, haematologic); biomarker =
  TP53mut or ATM-deficient.

### 4. RB1 loss → mitotic kinase / Aurora / AURKB inhibition

- **Driver event:** RB1 deletion/mutation, characteristic of retinoblastoma,
  SCLC, castration-resistant prostate cancer, and late-stage many cancers.
- **Mechanism:** RB1 loss deregulates E2F, upregulates mitotic gene expression
  and creates dependence on mitotic fidelity. Inhibiting mitotic kinases
  (Aurora A/B, PLK1, TTK/MPS1) selectively kills RB1-null cells (PMID
  34359636).
- **Collateral lethality:** RB1-neighbouring gene PTEN2/SUCLA2 is often
  co-deleted → targetable metabolic vulnerability (PMID 34359636).
- **Cancer types:** SCLC, prostate, bladder.

### 5. KRAS-G12D → PARP / DDR / metabolic combinations

- **Driver event:** KRAS mutations (G12D, G12C, G12V), dominant in pancreatic
  (>90%), NSCLC (~30%), colorectal (~40%) cancers.
- **Mechanism:** Direct KRAS inhibitors (sotorasib for G12C, MRTX1133 for
  G12D) now exist; combining with PARP inhibition exploits KRAS-driven
  replication stress → enhanced DNA damage beyond repair capacity (PMID
  41735281).
- **Cancer types:** Pancreatic ductal adenocarcinoma primarily (PMID 41735281).

## Overarching framework (PMID 41537447)

| Category | Tumour defect | Therapeutic target | Example |
|----------|--------------|-------------------|---------|
| DDR-DDR | HR loss (BRCA) | PARP | Olaparib |
| DDR-DDR | dMMR / MSI-H | WRN helicase | TBD |
| DDR-checkpoint | TP53/ATM loss | ATR/CHK1/WEE1 | Adavosertib |
| Metabolic | MTAP deletion | PRMT5 / MAT2A | TNG908 |
| Cell-cycle | RB1 loss | Aurora B / PLK1 | Alisertib |
| Oncogene-DDR | KRAS-mut | PARP + KRASi | Combination |

## Computational angles for this project

The following are tractable in-silico extensions from this literature:

1. **Network modelling:** Build a bipartite graph (driver-loss ↔ druggable
   dependency) from the pairs above; compute centrality to identify
   high-coverage targets (one drug covers many driver contexts).
2. **Combinatorial fragility simulation:** Agent-based or Boolean network model
   where knocking out two nodes simultaneously → cell-death attractor,
   single-knockout → survival. Explore how network topology determines SL
   density.
3. **Frequency × druggability ranking:** Combine TCGA/COSMIC driver-mutation
   frequencies with druggability scores from public databases (e.g. DGIdb) to
   rank SL pairs by expected population impact.

## References (all grounded)

- PMID 42207998 — Novel Synthetic Lethal Therapeutic Strategies in Precision
  Oncology.
- PMID 42092061 — Two decades of PARP inhibitor synthetic lethality in cancer.
- PMID 41537447 — Synthetic lethality in cancer therapy: Mechanisms, models
  and clinical translation for overcoming therapeutic resistance.
- PMID 42198893 — MTAP Deficiency as a Metabolic Vulnerability in Cancer:
  Implications for Synthetic Lethal Therapy.
- PMID 41962327 — Targeting WRN helicase in MSI-H tumors: Synthetic
  lethality, small molecule discovery, and therapeutic perspectives.
- PMID 40759474 — Therapeutic Targeting of DNA Damage Response Pathways in
  TP53- and ATM-Mutated Tumors.
- PMID 34359636 — Targeting RB1 Loss in Cancers.
- PMID 41735281 — Combination of PARP and KRAS(G12D) inhibitors enhances
  therapeutic efficacy in PDAC.
