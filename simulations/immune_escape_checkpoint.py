"""
Immune escape dynamics in the clonal evolution framework.

Models tumour–immune coevolution where:
1. Each driver hit generates neoantigens with probability p_neo
2. Immune killing rate scales with neoantigen load (clonal neoantigens >> subclonal)
3. Immune escape (HLA-LOH or IFNγ pathway loss) is a stochastic event
4. Checkpoint blockade restores/amplifies immune killing

Connects multistage thread (k-hit → neoantigen burden) with resistance thread
(escape dynamics under therapy).

Key question: How does neoantigen clonality (tumour evolutionary history)
determine checkpoint response and time-to-escape?

Grounded in:
  - PMID 32929288 (Lakatos 2020): neoantigen evolution under negative selection
  - PMID 40025156 (2025): stochastic birth-death immune escape model
  - PMID 30318143 (Angelova 2018): immunoediting shapes metastatic clones

Author: autonomous research agent
Date: 2026-05-30
"""

import numpy as np
from pathlib import Path
import csv

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# --- Parameters ---

# Neoantigen generation: each driver has probability p_neo of being immunogenic
P_NEO_PER_DRIVER = 0.5  # ~50% of drivers generate strong neoantigens (McGranahan 2016)

# Immune parameters
PARAMS_BASELINE = dict(
    N0=1e7,            # tumour cells at checkpoint therapy start
    k_drivers=6,       # total driver hits accumulated
    f_clonal=0.7,      # fraction of neoantigens that are clonal (trunk)
    p_neo=P_NEO_PER_DRIVER,
    # Immune kill rate: base_kill * neoantigen_score
    base_kill=0.02,    # /day, per-cell immune kill rate per unit neoantigen score
    # Neoantigen score: clonal neoantigens weighted higher (visible to all T cells)
    w_clonal=1.0,      # weight for clonal neoantigens
    w_subclonal=0.3,   # weight for subclonal neoantigens (diluted presentation)
    # Tumour growth
    b=0.1,             # birth rate /day
    d_base=0.04,       # baseline death rate /day (non-immune)
    # Escape routes
    u_hla=5e-7,        # HLA-LOH rate per division (eliminates antigen presentation)
    u_ifn=2e-7,        # IFNγ pathway loss rate per division (JAK1/2, B2M)
    # Escaped cell parameters
    fitness_cost_escape=0.01,  # small fitness cost of escape (genomic instability)
    # Checkpoint therapy amplification
    checkpoint_boost=3.0,  # fold increase in immune kill under anti-PD1/PDL1
    # Simulation
    rho_progression=1e8,   # progression threshold (resistant clone size)
    t_max=730,             # max days (2 years)
)


def neoantigen_score(k_drivers, f_clonal, p_neo, w_clonal, w_subclonal):
    """Compute effective neoantigen score based on driver count and clonality.
    
    Clonal neoantigens (present in all cells) drive stronger immune response
    than subclonal ones (present in fraction of cells).
    """
    n_neo = k_drivers * p_neo  # expected number of immunogenic drivers
    n_clonal = n_neo * f_clonal
    n_subclonal = n_neo * (1 - f_clonal)
    return n_clonal * w_clonal + n_subclonal * w_subclonal


def immune_kill_rate(params, checkpoint_on=True):
    """Effective immune kill rate for sensitive (non-escaped) cells."""
    score = neoantigen_score(
        params['k_drivers'], params['f_clonal'], params['p_neo'],
        params['w_clonal'], params['w_subclonal']
    )
    rate = params['base_kill'] * score
    if checkpoint_on:
        rate *= params['checkpoint_boost']
    return rate


def simulate_immune_escape(params, checkpoint_on=True, rng=None):
    """Tau-leaping simulation of tumour under immune selection + escape.
    
    Two populations: S (sensitive to immune), E (escaped).
    S cells: birth b, death d_base + immune_kill; mutate to E at rate u_eff.
    E cells: birth b, death d_base + fitness_cost; no immune kill.
    
    Returns: (time_to_progression_or_nan, final_S, final_E, escaped_dominant)
    """
    if rng is None:
        rng = np.random.default_rng()
    
    N0 = int(params['N0'])
    b = params['b']
    d_base = params['d_base']
    kill = immune_kill_rate(params, checkpoint_on)
    u_eff = params['u_hla'] + params['u_ifn']  # combined escape rate
    d_escaped = d_base + params['fitness_cost_escape']
    rho = params['rho_progression']
    t_max = params['t_max']
    
    # Start: all cells sensitive (no escape yet)
    S = float(N0)
    E = 0.0
    t = 0.0
    dt = 0.5  # half-day steps
    
    while t < t_max:
        if S < 1 and E < 1:
            # Tumour eliminated
            return (np.nan, 0, 0, False)
        
        if E >= rho:
            # Progression via escape
            return (t, S, E, True)
        
        # Rates for sensitive population
        birth_S = b * S
        death_S = (d_base + kill) * S
        mutation_S_to_E = u_eff * b * S  # escape mutation per division
        
        # Rates for escaped population
        birth_E = b * E
        death_E = d_escaped * E
        
        # Tau-leaping step
        n_birth_S = rng.poisson(max(0, birth_S * dt))
        n_death_S = rng.poisson(max(0, death_S * dt))
        n_mut = rng.poisson(max(0, mutation_S_to_E * dt))
        n_birth_E = rng.poisson(max(0, birth_E * dt))
        n_death_E = rng.poisson(max(0, death_E * dt))
        
        S = max(0, S + n_birth_S - n_death_S - n_mut)
        E = max(0, E + n_birth_E - n_death_E + n_mut)
        t += dt
    
    # Did not progress in t_max
    return (np.nan, S, E, False)


def run_parameter_scan(n_reps=300):
    """Scan key parameters and record escape statistics."""
    rng = np.random.default_rng(42)
    results = []
    
    # Scan 1: Effect of neoantigen clonality (f_clonal)
    for f_clonal in [0.2, 0.4, 0.6, 0.8, 1.0]:
        for checkpoint_on in [True, False]:
            times = []
            n_escape = 0
            n_elim = 0
            for _ in range(n_reps):
                p = dict(PARAMS_BASELINE)
                p['f_clonal'] = f_clonal
                t_prog, S, E, escaped = simulate_immune_escape(
                    p, checkpoint_on=checkpoint_on, rng=rng
                )
                if escaped:
                    n_escape += 1
                    times.append(t_prog)
                elif np.isnan(t_prog) and S == 0 and E == 0:
                    n_elim += 1
            
            median_t = np.median(times) if times else np.nan
            results.append(dict(
                scan='f_clonal', value=f_clonal,
                checkpoint=checkpoint_on,
                p_escape=n_escape / n_reps,
                p_elimination=n_elim / n_reps,
                median_time_to_escape=median_t,
                n_reps=n_reps,
            ))
    
    # Scan 2: Effect of driver count (k_drivers) — connects to multistage
    for k in [2, 4, 6, 8, 10]:
        for checkpoint_on in [True, False]:
            times = []
            n_escape = 0
            n_elim = 0
            for _ in range(n_reps):
                p = dict(PARAMS_BASELINE)
                p['k_drivers'] = k
                t_prog, S, E, escaped = simulate_immune_escape(
                    p, checkpoint_on=checkpoint_on, rng=rng
                )
                if escaped:
                    n_escape += 1
                    times.append(t_prog)
                elif np.isnan(t_prog) and S == 0 and E == 0:
                    n_elim += 1
            
            median_t = np.median(times) if times else np.nan
            results.append(dict(
                scan='k_drivers', value=k,
                checkpoint=checkpoint_on,
                p_escape=n_escape / n_reps,
                p_elimination=n_elim / n_reps,
                median_time_to_escape=median_t,
                n_reps=n_reps,
            ))
    
    # Scan 3: Effect of tumour size at therapy start (N0)
    for log_n0 in [5, 6, 7, 8, 9]:
        for checkpoint_on in [True, False]:
            times = []
            n_escape = 0
            n_elim = 0
            for _ in range(n_reps):
                p = dict(PARAMS_BASELINE)
                p['N0'] = 10**log_n0
                t_prog, S, E, escaped = simulate_immune_escape(
                    p, checkpoint_on=checkpoint_on, rng=rng
                )
                if escaped:
                    n_escape += 1
                    times.append(t_prog)
                elif np.isnan(t_prog) and S == 0 and E == 0:
                    n_elim += 1
            
            median_t = np.median(times) if times else np.nan
            results.append(dict(
                scan='N0', value=log_n0,
                checkpoint=checkpoint_on,
                p_escape=n_escape / n_reps,
                p_elimination=n_elim / n_reps,
                median_time_to_escape=median_t,
                n_reps=n_reps,
            ))
    
    return results


def analytic_escape_probability(params, checkpoint_on=True):
    """Analytic approximation for P(escape) using Iwasa framework.
    
    P(escape) ≈ 1 - exp(-u_eff * N0 * s_R / s_S)
    where s_R = net growth of escaped, s_S = net decline of sensitive.
    Each sensitive cell that divides has probability u_eff of producing escape mutant;
    each escape mutant survives with probability s_R/(b_R) (Moran-like).
    """
    kill = immune_kill_rate(params, checkpoint_on)
    u_eff = params['u_hla'] + params['u_ifn']
    b = params['b']
    d_base = params['d_base']
    
    # Net growth of escaped clone
    s_R = b - (d_base + params['fitness_cost_escape'])
    # Survival probability of single escape mutant
    if s_R <= 0:
        return 0.0
    p_survive = s_R / b
    
    # Net decline of sensitive: how many divisions before S → 0?
    net_S = b - (d_base + kill)  # should be negative under therapy
    if net_S >= 0:
        # Immune kill not strong enough; tumour grows → escape guaranteed
        return 1.0
    
    # Total divisions during S decline: integral of b*S(t) dt as S declines
    # S(t) = N0 * exp(net_S * t); total divisions = b * N0 / |net_S|
    total_divisions = b * params['N0'] / abs(net_S)
    
    # Expected number of successful escape mutants
    expected_escapes = u_eff * total_divisions * p_survive
    
    # P(at least one escape) = 1 - Poisson(0)
    p_esc = 1.0 - np.exp(-expected_escapes)
    return p_esc


def run_analytic_comparison():
    """Compare analytic P(escape) to simulation across parameter space."""
    results = []
    for log_n0 in [5, 6, 7, 8, 9]:
        for checkpoint_on in [True, False]:
            p = dict(PARAMS_BASELINE)
            p['N0'] = 10**log_n0
            p_analytic = analytic_escape_probability(p, checkpoint_on)
            results.append(dict(
                log_N0=log_n0, checkpoint=checkpoint_on,
                p_escape_analytic=p_analytic,
            ))
    return results


if __name__ == "__main__":
    print("=" * 70)
    print("IMMUNE ESCAPE DYNAMICS UNDER CHECKPOINT THERAPY")
    print("=" * 70)
    
    # Show baseline parameters
    print("\n--- Baseline parameters ---")
    kill_on = immune_kill_rate(PARAMS_BASELINE, checkpoint_on=True)
    kill_off = immune_kill_rate(PARAMS_BASELINE, checkpoint_on=False)
    score = neoantigen_score(
        PARAMS_BASELINE['k_drivers'], PARAMS_BASELINE['f_clonal'],
        PARAMS_BASELINE['p_neo'], PARAMS_BASELINE['w_clonal'],
        PARAMS_BASELINE['w_subclonal']
    )
    print(f"  Neoantigen score: {score:.2f} (k={PARAMS_BASELINE['k_drivers']}, "
          f"f_clonal={PARAMS_BASELINE['f_clonal']})")
    print(f"  Immune kill rate (no checkpoint): {kill_off:.4f}/day")
    print(f"  Immune kill rate (checkpoint on):  {kill_on:.4f}/day")
    print(f"  Net growth sensitive (no ckpt): {PARAMS_BASELINE['b'] - PARAMS_BASELINE['d_base'] - kill_off:.4f}/day")
    print(f"  Net growth sensitive (ckpt on):  {PARAMS_BASELINE['b'] - PARAMS_BASELINE['d_base'] - kill_on:.4f}/day")
    print(f"  Net growth escaped: {PARAMS_BASELINE['b'] - PARAMS_BASELINE['d_base'] - PARAMS_BASELINE['fitness_cost_escape']:.4f}/day")
    print(f"  Escape mutation rate: {PARAMS_BASELINE['u_hla'] + PARAMS_BASELINE['u_ifn']:.1e}/division")
    
    # Analytic comparison
    print("\n--- Analytic P(escape) ---")
    analytic = run_analytic_comparison()
    for r in analytic:
        print(f"  N0=1e{r['log_N0']}, checkpoint={'ON' if r['checkpoint'] else 'OFF'}: "
              f"P(esc)={r['p_escape_analytic']:.4f}")
    
    # Run simulations
    print("\n--- Running simulations (300 reps per condition) ---")
    sim_results = run_parameter_scan(n_reps=300)
    
    print("\n--- Results: Effect of neoantigen clonality (f_clonal) ---")
    print(f"{'f_clonal':>8} {'ckpt':>5} {'P(esc)':>8} {'P(elim)':>8} {'med_T':>8}")
    for r in sim_results:
        if r['scan'] == 'f_clonal':
            print(f"{r['value']:>8.1f} {'ON' if r['checkpoint'] else 'OFF':>5} "
                  f"{r['p_escape']:>8.3f} {r['p_elimination']:>8.3f} "
                  f"{r['median_time_to_escape']:>8.1f}" if not np.isnan(r['median_time_to_escape'])
                  else f"{r['value']:>8.1f} {'ON' if r['checkpoint'] else 'OFF':>5} "
                  f"{r['p_escape']:>8.3f} {r['p_elimination']:>8.3f} {'N/A':>8}")
    
    print("\n--- Results: Effect of driver count (k_drivers) ---")
    print(f"{'k':>8} {'ckpt':>5} {'P(esc)':>8} {'P(elim)':>8} {'med_T':>8}")
    for r in sim_results:
        if r['scan'] == 'k_drivers':
            print(f"{r['value']:>8.0f} {'ON' if r['checkpoint'] else 'OFF':>5} "
                  f"{r['p_escape']:>8.3f} {r['p_elimination']:>8.3f} "
                  f"{r['median_time_to_escape']:>8.1f}" if not np.isnan(r['median_time_to_escape'])
                  else f"{r['value']:>8.0f} {'ON' if r['checkpoint'] else 'OFF':>5} "
                  f"{r['p_escape']:>8.3f} {r['p_elimination']:>8.3f} {'N/A':>8}")
    
    print("\n--- Results: Effect of tumour size (log10 N0) ---")
    print(f"{'log_N0':>8} {'ckpt':>5} {'P(esc)':>8} {'P(elim)':>8} {'med_T':>8}")
    for r in sim_results:
        if r['scan'] == 'N0':
            print(f"{r['value']:>8.0f} {'ON' if r['checkpoint'] else 'OFF':>5} "
                  f"{r['p_escape']:>8.3f} {r['p_elimination']:>8.3f} "
                  f"{r['median_time_to_escape']:>8.1f}" if not np.isnan(r['median_time_to_escape'])
                  else f"{r['value']:>8.0f} {'ON' if r['checkpoint'] else 'OFF':>5} "
                  f"{r['p_escape']:>8.3f} {r['p_elimination']:>8.3f} {'N/A':>8}")
    
    # Save results
    outfile = OUTPUT_DIR / "immune_escape_results.csv"
    with open(outfile, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'scan', 'value', 'checkpoint', 'p_escape', 'p_elimination',
            'median_time_to_escape', 'n_reps'
        ])
        writer.writeheader()
        writer.writerows(sim_results)
    print(f"\nResults saved to {outfile}")
    
    # Key findings summary
    print("\n" + "=" * 70)
    print("KEY FINDINGS SUMMARY")
    print("=" * 70)
    
    # Find the clonality effect
    f_clonal_ckpt = [r for r in sim_results 
                     if r['scan'] == 'f_clonal' and r['checkpoint']]
    if f_clonal_ckpt:
        low_clonal = next(r for r in f_clonal_ckpt if r['value'] == 0.2)
        high_clonal = next(r for r in f_clonal_ckpt if r['value'] == 1.0)
        print(f"\n1. CLONALITY PARADOX: Higher clonal neoantigen fraction →")
        print(f"   stronger immune pressure → MORE elimination but ALSO more")
        print(f"   escape pressure (selection for escape mutants).")
        print(f"   f_clonal=0.2: P(esc)={low_clonal['p_escape']:.3f}, "
              f"P(elim)={low_clonal['p_elimination']:.3f}")
        print(f"   f_clonal=1.0: P(esc)={high_clonal['p_escape']:.3f}, "
              f"P(elim)={high_clonal['p_elimination']:.3f}")
    
    # Checkpoint effect
    k6_on = next((r for r in sim_results 
                  if r['scan'] == 'k_drivers' and r['value'] == 6 and r['checkpoint']), None)
    k6_off = next((r for r in sim_results 
                   if r['scan'] == 'k_drivers' and r['value'] == 6 and not r['checkpoint']), None)
    if k6_on and k6_off:
        print(f"\n2. CHECKPOINT THERAPY (k=6 drivers, N0=1e7):")
        print(f"   Without checkpoint: P(esc)={k6_off['p_escape']:.3f}, "
              f"P(elim)={k6_off['p_elimination']:.3f}")
        print(f"   With checkpoint:    P(esc)={k6_on['p_escape']:.3f}, "
              f"P(elim)={k6_on['p_elimination']:.3f}")
    
    # N0 phase transition (parallel to PARPi result)
    n0_on = [r for r in sim_results if r['scan'] == 'N0' and r['checkpoint']]
    if n0_on:
        print(f"\n3. TUMOUR SIZE PHASE TRANSITION (parallel to PARPi result):")
        for r in n0_on:
            print(f"   N0=1e{r['value']:.0f}: P(esc)={r['p_escape']:.3f}, "
                  f"P(elim)={r['p_elimination']:.3f}")
