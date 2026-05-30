"""MHCflurry-backed neoantigen immunogenicity — replaces a hand-waved p_neo.

The immune-escape simulation models each driver mutation as immunogenic with a
flat probability `p_neo` (~0.5, a literature average). That abstraction has no
peptide- or HLA-specificity. This helper grounds it: given candidate mutant
peptides and an individual's class-I HLA genotype, MHCflurry predicts antigen
presentation, and we derive a data-driven p_neo (fraction of peptides presented)
and a mean presentation score (immune-visibility weight).

MHCflurry is an OPTIONAL heavy dependency (no NetMHC licence wall). Install on
demand:  pip install mhcflurry  &&  mhcflurry-downloads fetch models_class1_presentation
If unavailable, `neoantigen_immunogenicity` returns the literature default so the
simulation still runs — just without peptide-level teeth.

Refs: PMID 32942059 (MHCflurry 2.0, O'Donnell 2020); McGranahan 2016 (clonal
neoantigen burden & checkpoint response).
"""
from __future__ import annotations

# Literature-average fraction of drivers that yield a strong neoantigen, used as
# the fallback when MHCflurry / peptides are unavailable (McGranahan 2016).
LITERATURE_DEFAULT_P_NEO = 0.5

# A presentation_score at/above this is treated as a presented (immunogenic)
# peptide. MHCflurry presentation_score is a 0-1 logistic over affinity+processing.
PRESENTATION_THRESHOLD = 0.5

_PREDICTOR = None  # cached Class1PresentationPredictor (per-process)


def mhcflurry_available() -> bool:
    """True if mhcflurry imports and its presentation models can load."""
    return _load_predictor() is not None


def _load_predictor():
    """Lazily load and cache the MHCflurry presentation predictor, or None."""
    global _PREDICTOR
    if _PREDICTOR is not None:
        return _PREDICTOR
    try:
        from mhcflurry import Class1PresentationPredictor
        _PREDICTOR = Class1PresentationPredictor.load()
    except Exception:
        return None
    return _PREDICTOR


def predict_presentation(peptides: list[str], alleles: list[str]) -> list[float]:
    """Best-allele presentation_score (0-1) per peptide for an HLA genotype.

    Returns an empty list if MHCflurry is unavailable. `alleles` is the
    individual's class-I genotype (up to 6 HLA-A/B/C alleles); names like
    'A0201' or 'HLA-A*02:01' are both accepted (normalised by mhcnames).
    """
    predictor = _load_predictor()
    if predictor is None or not peptides:
        return []
    df = predictor.predict(peptides=list(peptides), alleles=list(alleles), verbose=0)
    return [float(x) for x in df["presentation_score"].tolist()]


def neoantigen_immunogenicity(
    peptides: list[str] | None = None,
    alleles: list[str] | None = None,
    threshold: float = PRESENTATION_THRESHOLD,
) -> dict:
    """Data-driven neoantigen immunogenicity for the immune-escape model.

    Returns a dict with:
      p_neo        fraction of peptides predicted presented (>= threshold), i.e.
                   the probability a candidate neoantigen is immunogenic;
      mean_score   mean presentation_score over presented peptides (visibility
                   weight), or 0.0 if none presented;
      n, n_presented, source ('mhcflurry' or 'literature_default').

    Falls back to LITERATURE_DEFAULT_P_NEO when MHCflurry or peptides are absent,
    so callers can always rely on a usable p_neo.
    """
    if not peptides or not alleles:
        return _fallback("no peptides/alleles supplied")
    scores = predict_presentation(peptides, alleles)
    if not scores:
        return _fallback("mhcflurry unavailable")
    presented = [s for s in scores if s >= threshold]
    p_neo = len(presented) / len(scores)
    mean_score = sum(presented) / len(presented) if presented else 0.0
    return {
        "p_neo": p_neo,
        "mean_score": mean_score,
        "n": len(scores),
        "n_presented": len(presented),
        "source": "mhcflurry",
    }


def _fallback(reason: str) -> dict:
    return {
        "p_neo": LITERATURE_DEFAULT_P_NEO,
        "mean_score": 0.0,
        "n": 0,
        "n_presented": 0,
        "source": f"literature_default ({reason})",
    }


if __name__ == "__main__":
    # Demo: viral/self peptides against a common HLA-A*02:01-bearing genotype.
    demo_peptides = ["NLVPMVATV", "SIINFEKL", "GILGFVFTL", "KSEYMTSWFY", "LLFGYPVYV"]
    demo_alleles = ["A0201", "A0301", "B0702", "B4402", "C0201", "C0702"]
    print(f"mhcflurry available: {mhcflurry_available()}")
    print(neoantigen_immunogenicity(demo_peptides, demo_alleles))
