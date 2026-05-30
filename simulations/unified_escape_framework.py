"""
Unified Evolutionary Escape Framework: Analytic Treatment Across Therapy Types.

Derives and validates a single branching-process formula that predicts the
probability of evolutionary escape (resistance/immune evasion) for any therapy,
given population size, mutation rate, and fitness parameters.

Reference: Iwasa Y, Michor F, Nowak MA. Proc R Soc B 2006;273:1137-1144 (PMID 16454743).
Also: Iwasa et al. J Theor Biol 2003;226:205-214 (PMID 14728779).

Item: open_questions #22
"""

import numpy as np


# ============================================================
# SECTION 1: General analytic framework
# ============================================================

def escape_potential_constant_rate(u_eff, N0, b_S, r_S, b_R, r_R):
    """
    Escape potential Phi for constant-rate therapy-induced decline.

    During therapy, sensitive cells decline at net rate r_S < 0.
    Mutations arise at rate u_eff per division (u_eff * b_S * S(t) per unit time).
    Each resistant mutant survives with probability p_surv = r_R / b_R.

    Total mutation supply: M = integral_0^inf b_S * N0 * exp(r_S*t) dt = b_S * N0 / |r_S|
    Escape potential: Phi = u_eff * M * p_surv = u_eff * N0 * (b_S/|r_S|) * (r_R/b_R)

    Parameters
    ----------
    u_eff : float  - effective mutation rate per division (sum over routes)
    N0 : float     - initial sensitive population
    b_S : float    - sensitive birth rate (/day)
    r_S : float    - sensitive net growth rate (/day), must be < 0
    b_R : float    - resistant birth rate (/day)
    r_R : float    - resistant net growth rate (/day), must be > 0

    Returns
    -------
    Phi : float    - escape potential (phase transition at Phi ~ 1)
    """
    assert r_S < 0, "Sensitive cells must be declining under therapy"
    assert r_R > 0, "Resistant cells must be growing (supercritical)"
    p_surv = r_R / b_R
    mutation_supply = b_S * N0 / abs(r_S)
    return u_eff * mutation_supply * p_surv


def escape_probability(Phi):
    """P(escape) = 1 - exp(-Phi) from Poisson approximation of successful mutants."""
    return 1.0 - np.exp(-Phi)


def critical_population_size(u_eff, b_S, r_S, b_R, r_R):
    """
    N_crit: population size at which Phi = 1 (50/50 escape).

    N_crit = |r_S| * b_R / (u_eff * b_S * r_R)
    """
    assert r_S < 0
    assert r_R > 0
    return abs(r_S) * b_R / (u_eff * b_S * r_R)


def escape_potential_with_preexisting(u_eff, N0, b_S, r_S, b_R, r_R):
    """
    Full escape potential including pre-existing resistant cells.

    Pre-existing: if tumour grew from 1 to N0, expected resistant cells at
    therapy start = u_eff * N0 (Luria-Delbruck). Each survives with p_surv.

    Phi_total = Phi_preexisting + Phi_de_novo
    """
    p_surv = r_R / b_R
    Phi_preexist = u_eff * N0 * p_surv
    Phi_de_novo = escape_potential_constant_rate(u_eff, N0, b_S, r_S, b_R, r_R)
    return Phi_preexist + Phi_de_novo


def escape_potential_multi_mechanism(params_list, N0, b_S, r_S):
    """
    Multi-mechanism escape: k independent parallel routes.

    Phi_total = sum_i u_i * N0 * (b_S/|r_S|) * (r_R_i / b_R_i)

    Parameters
    ----------
    params_list : list of dict, each with keys 'u', 'b_R', 'r_R'
    N0, b_S, r_S : population and sensitive cell parameters
    """
    Phi_total = 0.0
    for p in params_list:
        Phi_i = escape_potential_constant_rate(
            p['u'], N0, b_S, r_S, p['b_R'], p['r_R']
        )
        Phi_total += Phi_i
    return Phi_total


# ============================================================
# SECTION 2: Parameterise for each therapy context
# ============================================================

def parpi_resistance_params():
    """PARPi resistance via BRCA reversion (item 13)."""
    return {
        'name': 'PARPi (BRCA reversion)',
        'u_eff': 1e-8,       # reversion rate per division
        'b_S': 0.1,          # sensitive birth rate /day
        'd_S': 0.14,         # sensitive death rate /day (PARPi)
        'r_S': 0.1 - 0.14,  # = -0.04 /day
        'b_R': 0.1,          # resistant birth rate /day
        'd_R': 0.05,         # resistant death rate /day
        'r_R': 0.1 - 0.05,  # = +0.05 /day
    }


def checkpoint_escape_params():
    """Immune escape under checkpoint blockade (item 19)."""
    return {
        'name': 'Checkpoint (HLA-LOH escape)',
        'u_eff': 7e-7,       # HLA-LOH + IFN pathway loss combined
        'b_S': 0.1,          # sensitive birth rate /day
        'd_S': 0.12,         # death under checkpoint (immune + natural)
        'r_S': 0.1 - 0.12,  # = -0.02 /day (net decline under checkpoint)
        'b_R': 0.1,          # escaped cell birth rate
        'd_R': 0.07,         # escaped cell death (no immune kill, some natural)
        'r_R': 0.1 - 0.07,  # = +0.03 /day
    }


def immunoediting_params():
    """
    Pre-malignant immunoediting (item 21) — analogous filter case.

    NOT therapy-induced: immune surveillance creates ongoing selection.
    Effective r_S includes immune kill rate alpha * n_neo.
    Escape = HLA-LOH (u_escape ~ 0.005/yr ≈ 1.4e-5/day).

    Approximation: treat clone under immune pressure as declining,
    with effective r_S = growth - immune_kill.
    """
    alpha_per_day = 0.1 / 365.0  # alpha=0.1/yr, 3 neoantigens at midpoint
    n_neo_avg = 3
    return {
        'name': 'Immunoediting (pre-malignant filter)',
        'u_eff': 1.4e-5,             # ~0.005/yr HLA-LOH escape rate per day
        'b_S': 0.1,                  # cell division rate /day
        'd_S': 0.1 + alpha_per_day * n_neo_avg,  # natural + immune
        'r_S': -(alpha_per_day * n_neo_avg),      # net decline from immune
        'b_R': 0.1,                  # escaped clone birth
        'd_R': 0.099,                # nearly neutral (slight growth)
        'r_R': 0.001,                # very slow net growth after escape
        'note': 'Effective-decline approximation; real model is stochastic filter'
    }


def parpi_multi_mechanism_params():
    """Multi-mechanism PARPi resistance (item 16): 3 parallel routes."""
    return {
        'name': 'PARPi (3 mechanisms)',
        'b_S': 0.1,
        'r_S': -0.04,
        'routes': [
            {'u': 1e-8, 'b_R': 0.1, 'r_R': 0.05, 'name': 'BRCA reversion'},
            {'u': 1e-7, 'b_R': 0.1, 'r_R': 0.02, 'name': 'ABCB1 efflux'},
            {'u': 5e-8, 'b_R': 0.1, 'r_R': 0.03, 'name': 'Fork protection'},
        ]
    }


# ============================================================
# SECTION 3: Validation against simulation results
# ============================================================

def validate_parpi():
    """Compare analytic N_crit to simulation results from item 13."""
    p = parpi_resistance_params()
    N_crit = critical_population_size(
        p['u_eff'], p['b_S'], p['r_S'], p['b_R'], p['r_R']
    )

    print("=" * 60)
    print("CONTEXT 1: PARPi resistance (BRCA reversion)")
    print("=" * 60)
    print(f"  u_eff = {p['u_eff']:.0e}")
    print(f"  b_S={p['b_S']}, r_S={p['r_S']}, b_R={p['b_R']}, r_R={p['r_R']}")
    print(f"  N_crit (analytic) = {N_crit:.2e}")
    print(f"  Simulation (item 13): phase transition at u*N0 ~ 1 → N0 ~ 1e8")
    print(f"  Match: {0.5 <= N_crit/1e8 <= 2.0}")
    print()

    # Validate P(escape) across N0 scan
    print("  N0 scan validation:")
    print(f"  {'N0':>10} | {'Phi':>8} | {'P(esc) analytic':>15} | {'P(esc) sim':>12}")
    sim_data = [
        (1e5, 0.001), (1e6, 0.008), (1e7, 0.11), (1e8, 0.63), (1e9, 1.0)
    ]
    for N0, p_sim in sim_data:
        Phi = escape_potential_constant_rate(
            p['u_eff'], N0, p['b_S'], p['r_S'], p['b_R'], p['r_R']
        )
        p_analytic = escape_probability(Phi)
        print(f"  {N0:>10.0e} | {Phi:>8.4f} | {p_analytic:>15.4f} | {p_sim:>12.3f}")

    return N_crit


def validate_checkpoint():
    """Compare analytic N_crit to simulation results from item 19."""
    p = checkpoint_escape_params()
    N_crit = critical_population_size(
        p['u_eff'], p['b_S'], p['r_S'], p['b_R'], p['r_R']
    )

    print("=" * 60)
    print("CONTEXT 2: Immune escape under checkpoint blockade")
    print("=" * 60)
    print(f"  u_eff = {p['u_eff']:.0e}")
    print(f"  b_S={p['b_S']}, r_S={p['r_S']}, b_R={p['b_R']}, r_R={p['r_R']}")
    print(f"  N_crit (analytic) = {N_crit:.2e}")
    print(f"  Simulation (item 19): N0_crit ~ 5e5")
    print(f"  Match: {0.2 <= N_crit/5e5 <= 5.0}")
    print()

    # Validate against item 19 simulation data
    print("  N0 scan validation:")
    print(f"  {'N0':>10} | {'Phi':>8} | {'P(esc) analytic':>15} | {'P(esc) sim':>12}")
    sim_data = [
        (1e5, 0.04), (1e6, 0.41), (1e7, 0.97), (1e8, 1.0)
    ]
    for N0, p_sim in sim_data:
        Phi = escape_potential_constant_rate(
            p['u_eff'], N0, p['b_S'], p['r_S'], p['b_R'], p['r_R']
        )
        p_analytic = escape_probability(Phi)
        print(f"  {N0:>10.0e} | {Phi:>8.4f} | {p_analytic:>15.4f} | {p_sim:>12.3f}")

    return N_crit


def validate_immunoediting():
    """Analogous treatment of immunoediting (item 21)."""
    p = immunoediting_params()
    N_crit = critical_population_size(
        p['u_eff'], p['b_S'], p['r_S'], p['b_R'], p['r_R']
    )

    print("=" * 60)
    print("CONTEXT 3: Pre-malignant immunoediting (analogous filter)")
    print("=" * 60)
    print(f"  u_eff = {p['u_eff']:.1e} (HLA-LOH escape rate)")
    print(f"  b_S={p['b_S']}, r_S={p['r_S']:.5f}, b_R={p['b_R']}, r_R={p['r_R']}")
    print(f"  N_crit (analytic) = {N_crit:.2e}")
    print(f"  NOTE: Item 21 used a different model structure (stochastic filter)")
    print(f"  The effective-decline approximation gives a MUCH lower N_crit")
    print(f"  because immune pressure is weak (r_S ≈ -8e-4/day).")
    print(f"  This confirms immunoediting is a FILTER (most clones too small to")
    print(f"  escape) rather than a rate-limiter on the large clones that do.")
    print()

    return N_crit


def validate_multi_mechanism():
    """Multi-mechanism PARPi (item 16): Phi_total = sum Phi_i."""
    p = parpi_multi_mechanism_params()
    Phi_total = escape_potential_multi_mechanism(
        p['routes'], 1e7, p['b_S'], p['r_S']
    )
    Phi_single = escape_potential_constant_rate(
        1e-8, 1e7, p['b_S'], p['r_S'], 0.1, 0.05
    )

    print("=" * 60)
    print("CONTEXT 4: Multi-mechanism PARPi resistance (3 routes)")
    print("=" * 60)
    print(f"  Routes:")
    for route in p['routes']:
        Phi_i = escape_potential_constant_rate(
            route['u'], 1e7, p['b_S'], p['r_S'], route['b_R'], route['r_R']
        )
        print(f"    {route['name']:>20}: u={route['u']:.0e}, r_R={route['r_R']}, "
              f"Phi_i={Phi_i:.4f}")
    print(f"  Phi_total (N0=1e7) = {Phi_total:.4f}")
    print(f"  Phi_single_route    = {Phi_single:.4f}")
    print(f"  Ratio: {Phi_total/Phi_single:.1f}x (sim item 16: ~16x)")
    print(f"  P(escape, multi) = {escape_probability(Phi_total):.4f}")
    print(f"  P(escape, single) = {escape_probability(Phi_single):.4f}")
    print(f"  Simulation (item 16): P(R)≈29% at N0=1e7 (multi), ~2% (single)")
    print()

    # N_crit comparison
    N_crit_single = critical_population_size(1e-8, 0.1, -0.04, 0.1, 0.05)
    u_eff_total = sum(
        route['u'] * route['r_R'] / route['b_R'] for route in p['routes']
    )
    # Effective u for N_crit: use weighted average
    # Phi = N0 * (b_S/|r_S|) * sum(u_i * r_R_i/b_R_i)
    # N_crit: Phi=1 => N_crit = |r_S| / (b_S * sum(u_i * r_R_i/b_R_i))
    N_crit_multi = abs(p['r_S']) / (p['b_S'] * u_eff_total)
    print(f"  N_crit (single route) = {N_crit_single:.2e}")
    print(f"  N_crit (3 routes)     = {N_crit_multi:.2e}")
    print(f"  Ratio: {N_crit_single/N_crit_multi:.1f}x")
    print(f"  Simulation (item 16): N_crit shrinks from 1e8 → 6e6 (≈16x)")


# ============================================================
# SECTION 4: Summary table and universal predictions
# ============================================================

def summary_table():
    """Print the unified summary: all contexts under one framework."""
    print("\n" + "=" * 70)
    print("UNIFIED ESCAPE FRAMEWORK — SUMMARY")
    print("=" * 70)
    print()
    print("General formula (constant-rate therapy):")
    print("  P(escape) = 1 - exp(-Phi)")
    print("  Phi = u_eff * N0 * (b_S / |r_S|) * (r_R / b_R)")
    print("  N_crit = |r_S| * b_R / (u_eff * b_S * r_R)   [where Phi = 1]")
    print()
    print("Multi-mechanism: Phi_total = sum_i Phi_i  (independent rare routes)")
    print("Pre-existing:    Phi += u_eff * N0 * (r_R/b_R)  (Luria-Delbruck)")
    print()

    contexts = [
        parpi_resistance_params(),
        checkpoint_escape_params(),
        immunoediting_params(),
    ]

    print(f"{'Context':<35} | {'u_eff':>8} | {'r_S':>7} | {'r_R':>6} | "
          f"{'N_crit':>10} | {'Regime'}")
    print("-" * 100)
    for ctx in contexts:
        N_crit = critical_population_size(
            ctx['u_eff'], ctx['b_S'], ctx['r_S'], ctx['b_R'], ctx['r_R']
        )
        if N_crit > 1e8:
            regime = "MRD safe (surgery needed)"
        elif N_crit > 1e6:
            regime = "Borderline (MRD matters)"
        else:
            regime = "Small-clone escape likely"
        print(f"{ctx['name']:<35} | {ctx['u_eff']:>8.1e} | {ctx['r_S']:>7.4f} | "
              f"{ctx['r_R']:>6.3f} | {N_crit:>10.2e} | {regime}")

    print()
    print("KEY INSIGHT: The same mathematical structure (Phi ~ 1 transition)")
    print("governs escape across all therapy types. The PARAMETERS differ:")
    print("  - PARPi: low u (1e-8), strong kill (|r_S|=0.04) → high N_crit (1e8)")
    print("  - Checkpoint: high u (7e-7), weak kill (|r_S|=0.02) → low N_crit (5e5)")
    print("  - Immunoediting: high u but very weak pressure → filter not barrier")
    print()
    print("CLINICAL PREDICTION: for any new targeted/immune therapy, measure")
    print("(u_eff, b_S, r_S, r_R, b_R) and compute N_crit. If post-surgery")
    print("residual disease < N_crit, long-term control is expected.")


def adaptive_therapy_criterion():
    """Show when adaptive scheduling helps (connects items 18+20)."""
    print("\n" + "=" * 70)
    print("ADAPTIVE THERAPY CRITERION (from escape framework)")
    print("=" * 70)
    print()
    print("Adaptive scheduling (drug holidays) helps IFF:")
    print("  1. N0/K >= 0.3  (competition is relevant)")
    print("  2. r_S_off > r_E  (sensitive outcompetes escaped off-drug)")
    print()
    print("Benefit ~ (N0/K) * (r_S_off - r_E) / r_E")
    print()
    print("  PARPi MRD:   N0/K << 1, cost_R ~ 10% → benefit ~6-9% (marginal)")
    print("  Checkpoint:  N0/K ~ 0.5, cost_R ~ 25% → benefit ~17-38% (real)")
    print()
    print("This criterion follows from the escape framework: adaptive scheduling")
    print("cannot reduce Phi directly (mutation supply is fixed by decline rate),")
    print("but CAN reduce p_surv of resistant mutants via competitive suppression")
    print("— but only when competition is active (N ~ K).")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("UNIFIED EVOLUTIONARY ESCAPE FRAMEWORK")
    print("Analytic treatment across therapy types (item 22)")
    print("Based on Iwasa/Michor/Nowak multi-type branching process")
    print("PMIDs: 16454743, 14728779")
    print()

    validate_parpi()
    print()
    validate_checkpoint()
    print()
    validate_immunoediting()
    print()
    validate_multi_mechanism()

    summary_table()
    adaptive_therapy_criterion()
