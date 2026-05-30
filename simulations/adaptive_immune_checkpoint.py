"""
Adaptive checkpoint scheduling: does competition help delay immune escape?

Item 20 from open_questions. Extends item 19 (immune escape dynamics) with
Lotka-Volterra competition under intermittent checkpoint dosing. Tests the
hypothesis that unlike PARPi MRD (item 18: N << K, competition negligible),
immune escape clones at realistic tumour burden (N ~ K) with higher fitness
cost (HLA-LOH genomic instability) may be suppressed by drug holidays that
let immune-sensitive cells compete.

Key difference from item 18 (PARPi, honest negative):
  - PARPi MRD: N0 = 1e7, K = 1e9 → N/K ≈ 0.01 (competition negligible)
  - Checkpoint therapy: N0 = 1e8–1e9 (bulk tumour, not MRD)
  - Escape cost: HLA-LOH reduces MHC-I → reduced niche-signalling, possibly
    higher fitness cost than PARPi reversion (test: cost ∈ {0.01, 0.03, 0.05})

Model: ODE Lotka-Volterra (S + E) + stochastic mutation supply.
  S: immune-sensitive, E: immune-escaped (HLA-LOH or IFNγ loss).
  Drug ON (checkpoint active):  S declines (strong immune kill), E grows.
  Drug OFF (checkpoint holiday): S grows, E grows but slower (cost).
  Competition: both share carrying capacity K.

Grounded in:
  - PMID 30278037 (Gatenby 2018): natural adaptive therapy / restrained immune
  - PMID 40998270 (2025): evolutionary double-bind + LV model
  - PMID 41136296 (2025): evolution-informed immunotherapy review

Author: autonomous research agent
Date: 2026-05-30
"""

import numpy as np
from scipy.integrate import solve_ivp
from pathlib import Path
import csv

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# Parameters
# ============================================================

K = 1e9  # carrying capacity (solid tumour)

# Baseline immune escape parameters (from item 19)
PARAMS = dict(
    b=0.1,              # birth rate /day
    d_base=0.04,        # baseline death /day
    # Immune kill (under checkpoint therapy)
    kill_checkpoint=0.12,  # /day: strong kill under anti-PD1 (from item 19: base_kill * score * boost)
    kill_natural=0.02,     # /day: natural immune pressure without checkpoint
    # Escape clone
    fitness_cost_escape=0.03,  # /day: HLA-LOH cost (higher than PARPi's 0.01)
    # Mutation
    u_escape=7e-7,      # escape rate per division (HLA-LOH 5e-7 + IFNγ 2e-7)
    # Tumour size
    N0=5e8,             # cells at therapy start (bulk, not MRD)
    E0=0.0,             # initial escape population (start from zero)
    # Thresholds
    rho_progression=1e8,  # progression = escaped clone reaches clinical mass
    t_max=1095,           # 3 years max
)


def net_growth_sensitive(params, drug_on):
    """Net growth rate of sensitive cells."""
    kill = params['kill_checkpoint'] if drug_on else params['kill_natural']
    return params['b'] - params['d_base'] - kill


def net_growth_escaped(params):
    """Net growth rate of escaped cells (immune-independent)."""
    return params['b'] - params['d_base'] - params['fitness_cost_escape']


# ============================================================
# ODE model: Lotka-Volterra competition
# ============================================================

def ode_rhs(t, y, params, schedule_fn):
    """Lotka-Volterra ODE for S (sensitive) + E (escaped).
    
    dS/dt = r_S * S * (1 - (S + E) / K) - mutation
    dE/dt = r_E * E * (1 - (S + E) / K) + mutation
    mutation = u * b * S (supply from sensitive divisions)
    """
    S, E = max(y[0], 0), max(y[1], 0)
    total = S + E
    
    drug_on = schedule_fn(t)
    r_S = net_growth_sensitive(params, drug_on)
    r_E = net_growth_escaped(params)
    
    competition = 1.0 - total / K
    
    # Mutation supply: escape arises from sensitive divisions
    mutation = params['u_escape'] * params['b'] * S
    
    dS = r_S * S * competition - mutation
    dE = r_E * E * competition + mutation
    
    return [dS, dE]


def simulate_schedule(params, schedule_fn, dt_check=1.0):
    """Run ODE and return time-to-progression (TTP) and final state."""
    y0 = [params['N0'], params['E0']]
    t_span = (0, params['t_max'])
    t_eval = np.arange(0, params['t_max'] + dt_check, dt_check)
    
    sol = solve_ivp(
        ode_rhs, t_span, y0,
        args=(params, schedule_fn),
        t_eval=t_eval, method='RK45',
        max_step=1.0, rtol=1e-6, atol=1e-3
    )
    
    if not sol.success:
        return params['t_max'], sol.y[0][-1], sol.y[1][-1]
    
    # Find time-to-progression: E >= rho_progression
    for i, (s, e) in enumerate(zip(sol.y[0], sol.y[1])):
        if e >= params['rho_progression']:
            return sol.t[i], s, e
    
    return params['t_max'], sol.y[0][-1], sol.y[1][-1]


# ============================================================
# Schedule functions
# ============================================================

def make_continuous_schedule():
    """Checkpoint always on."""
    return lambda t: True


def make_no_treatment_schedule():
    """No checkpoint therapy."""
    return lambda t: False


def make_periodic_schedule(on_days, off_days):
    """Periodic on/off schedule."""
    cycle = on_days + off_days
    def schedule(t):
        return (t % cycle) < on_days
    return schedule


def make_adaptive_schedule(params, threshold_low=0.3, threshold_high=0.7):
    """Adaptive: stop when tumour shrinks below threshold_low * N0,
    resume when it grows back to threshold_high * N0.
    
    This requires ODE integration with event detection, so we implement
    as a state machine embedded in the schedule.
    """
    # For adaptive, we use a different simulation approach below
    pass


def simulate_adaptive(params, threshold_low_frac=0.3, threshold_high_frac=0.7):
    """Simulate adaptive therapy: drug ON until tumour < low, OFF until > high.
    
    Uses step-wise integration with state tracking.
    """
    N0 = params['N0']
    low = threshold_low_frac * N0
    high = threshold_high_frac * N0
    
    S = float(N0)
    E = float(params['E0'])
    t = 0.0
    dt = 0.5
    drug_on = True  # start with drug on
    
    while t < params['t_max']:
        total = S + E
        
        # Adaptive switching logic
        if drug_on and total < low:
            drug_on = False
        elif not drug_on and total > high:
            drug_on = True
        
        # Check progression
        if E >= params['rho_progression']:
            return t, S, E
        
        # Lotka-Volterra step (Euler — sufficient for comparison)
        r_S = net_growth_sensitive(params, drug_on)
        r_E = net_growth_escaped(params)
        competition = 1.0 - total / K
        mutation = params['u_escape'] * params['b'] * S
        
        dS = (r_S * S * competition - mutation) * dt
        dE = (r_E * E * competition + mutation) * dt
        
        S = max(0, S + dS)
        E = max(0, E + dE)
        t += dt
    
    return params['t_max'], S, E


# ============================================================
# Main analysis
# ============================================================

def run_schedule_comparison(params):
    """Compare continuous vs periodic vs adaptive schedules."""
    results = []
    
    # Continuous (always on)
    ttp, s_f, e_f = simulate_schedule(params, make_continuous_schedule())
    results.append(dict(schedule='continuous', on_frac=1.0, ttp=ttp,
                        final_S=s_f, final_E=e_f))
    
    # No treatment
    ttp, s_f, e_f = simulate_schedule(params, make_no_treatment_schedule())
    results.append(dict(schedule='no_treatment', on_frac=0.0, ttp=ttp,
                        final_S=s_f, final_E=e_f))
    
    # Periodic schedules
    for on_days, off_days in [(28, 7), (21, 7), (14, 7), (14, 14),
                               (7, 7), (7, 14), (7, 21), (5, 5),
                               (21, 14), (28, 14), (14, 21)]:
        on_frac = on_days / (on_days + off_days)
        schedule = make_periodic_schedule(on_days, off_days)
        ttp, s_f, e_f = simulate_schedule(params, schedule)
        results.append(dict(
            schedule=f'{on_days}on/{off_days}off', on_frac=on_frac,
            ttp=ttp, final_S=s_f, final_E=e_f
        ))
    
    # Adaptive schedules with different thresholds
    for lo, hi in [(0.2, 0.6), (0.3, 0.7), (0.4, 0.8), (0.5, 0.9)]:
        ttp, s_f, e_f = simulate_adaptive(params, lo, hi)
        results.append(dict(
            schedule=f'adaptive_{lo:.1f}_{hi:.1f}', on_frac=np.nan,
            ttp=ttp, final_S=s_f, final_E=e_f
        ))
    
    return results


def run_fitness_cost_sensitivity(params):
    """How does escape fitness cost affect the adaptive therapy benefit?"""
    results = []
    
    for cost in [0.005, 0.01, 0.02, 0.03, 0.05, 0.08]:
        p = dict(params)
        p['fitness_cost_escape'] = cost
        
        # Continuous
        ttp_cont, _, _ = simulate_schedule(p, make_continuous_schedule())
        # Best periodic (14on/14off as candidate)
        ttp_periodic, _, _ = simulate_schedule(p, make_periodic_schedule(14, 14))
        # Adaptive
        ttp_adapt, _, _ = simulate_adaptive(p, 0.3, 0.7)
        
        benefit_periodic = (ttp_periodic - ttp_cont) / ttp_cont * 100
        benefit_adaptive = (ttp_adapt - ttp_cont) / ttp_cont * 100
        
        results.append(dict(
            fitness_cost=cost,
            ttp_continuous=ttp_cont,
            ttp_periodic_14_14=ttp_periodic,
            ttp_adaptive=ttp_adapt,
            benefit_periodic_pct=benefit_periodic,
            benefit_adaptive_pct=benefit_adaptive,
        ))
    
    return results


def run_tumour_burden_sensitivity(params):
    """How does N0/K ratio affect competition benefit?
    This is the KEY test: PARPi failed because N/K << 1.
    """
    results = []
    
    for log_n0 in [6, 7, 8, 8.5, 9]:
        p = dict(params)
        p['N0'] = 10**log_n0
        nk_ratio = p['N0'] / K
        
        ttp_cont, _, _ = simulate_schedule(p, make_continuous_schedule())
        ttp_periodic, _, _ = simulate_schedule(p, make_periodic_schedule(14, 14))
        ttp_adapt, _, _ = simulate_adaptive(p, 0.3, 0.7)
        
        benefit_periodic = (ttp_periodic - ttp_cont) / ttp_cont * 100 if ttp_cont > 0 else 0
        benefit_adaptive = (ttp_adapt - ttp_cont) / ttp_cont * 100 if ttp_cont > 0 else 0
        
        results.append(dict(
            log_N0=log_n0, NK_ratio=nk_ratio,
            ttp_continuous=ttp_cont,
            ttp_periodic=ttp_periodic,
            ttp_adaptive=ttp_adapt,
            benefit_periodic_pct=benefit_periodic,
            benefit_adaptive_pct=benefit_adaptive,
        ))
    
    return results


if __name__ == "__main__":
    print("=" * 70)
    print("ADAPTIVE CHECKPOINT SCHEDULING: DOES COMPETITION HELP?")
    print("=" * 70)
    
    # Show baseline parameters
    r_S_on = net_growth_sensitive(PARAMS, True)
    r_S_off = net_growth_sensitive(PARAMS, False)
    r_E = net_growth_escaped(PARAMS)
    print(f"\n--- Baseline parameters ---")
    print(f"  N0 = {PARAMS['N0']:.1e}, K = {K:.1e}, N0/K = {PARAMS['N0']/K:.2f}")
    print(f"  r_S (drug ON):  {r_S_on:.4f}/day (net decline under checkpoint)")
    print(f"  r_S (drug OFF): {r_S_off:.4f}/day (net growth, natural immune only)")
    print(f"  r_E (escaped):  {r_E:.4f}/day (immune-independent)")
    print(f"  Fitness cost of escape: {PARAMS['fitness_cost_escape']}/day")
    print(f"  Competition term at N0: 1 - N0/K = {1 - PARAMS['N0']/K:.3f}")
    print(f"  Escape mutation rate: {PARAMS['u_escape']:.1e}/division")
    
    # Key comparison to PARPi (item 18)
    print(f"\n--- Comparison to PARPi MRD (item 18, where adaptive FAILED) ---")
    print(f"  PARPi: N0/K = 0.01, fitness cost = 0.01, competition term = 0.99")
    print(f"  Here:  N0/K = {PARAMS['N0']/K:.2f}, fitness cost = {PARAMS['fitness_cost_escape']}, "
          f"competition term = {1 - PARAMS['N0']/K:.3f}")
    
    # Run schedule comparison
    print("\n--- Schedule comparison (baseline) ---")
    sched_results = run_schedule_comparison(PARAMS)
    print(f"{'Schedule':<22} {'on_frac':>8} {'TTP(d)':>8} {'final_E':>10}")
    continuous_ttp = next(r['ttp'] for r in sched_results if r['schedule'] == 'continuous')
    for r in sorted(sched_results, key=lambda x: -x['ttp']):
        benefit = (r['ttp'] - continuous_ttp) / continuous_ttp * 100 if continuous_ttp > 0 else 0
        print(f"  {r['schedule']:<20} {r['on_frac']:>8.2f} {r['ttp']:>8.1f} "
              f"{r['final_E']:>10.2e} ({benefit:+.1f}%)")
    
    # Fitness cost sensitivity
    print("\n--- Fitness cost sensitivity ---")
    cost_results = run_fitness_cost_sensitivity(PARAMS)
    print(f"{'cost':>6} {'TTP_cont':>9} {'TTP_per':>9} {'TTP_adpt':>9} "
          f"{'%ben_per':>9} {'%ben_adp':>9}")
    for r in cost_results:
        print(f"  {r['fitness_cost']:>5.3f} {r['ttp_continuous']:>9.1f} "
              f"{r['ttp_periodic_14_14']:>9.1f} {r['ttp_adaptive']:>9.1f} "
              f"{r['benefit_periodic_pct']:>+9.1f} {r['benefit_adaptive_pct']:>+9.1f}")
    
    # Tumour burden sensitivity (THE KEY TEST)
    print("\n--- Tumour burden sensitivity (N0/K ratio) — KEY TEST ---")
    burden_results = run_tumour_burden_sensitivity(PARAMS)
    print(f"{'log_N0':>7} {'N0/K':>7} {'TTP_cont':>9} {'TTP_per':>9} {'TTP_adpt':>9} "
          f"{'%ben_per':>9} {'%ben_adp':>9}")
    for r in burden_results:
        print(f"  {r['log_N0']:>5.1f} {r['NK_ratio']:>7.3f} {r['ttp_continuous']:>9.1f} "
              f"{r['ttp_periodic']:>9.1f} {r['ttp_adaptive']:>9.1f} "
              f"{r['benefit_periodic_pct']:>+9.1f} {r['benefit_adaptive_pct']:>+9.1f}")
    
    # Save results
    outfile = OUTPUT_DIR / "adaptive_immune_checkpoint.csv"
    with open(outfile, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'schedule', 'on_frac', 'ttp', 'final_S', 'final_E'
        ])
        writer.writeheader()
        writer.writerows(sched_results)
    print(f"\nSchedule results saved to {outfile}")
    
    # Key findings
    print("\n" + "=" * 70)
    print("KEY FINDINGS")
    print("=" * 70)
    
    best_sched = max(sched_results, key=lambda x: x['ttp'])
    worst_sched = min(sched_results, key=lambda x: x['ttp'])
    best_benefit = (best_sched['ttp'] - continuous_ttp) / continuous_ttp * 100
    
    print(f"\n1. Best schedule: {best_sched['schedule']} "
          f"(TTP={best_sched['ttp']:.0f}d, {best_benefit:+.1f}% vs continuous)")
    print(f"   Continuous TTP: {continuous_ttp:.0f}d")
    
    # Interpret competition effect
    high_burden = next((r for r in burden_results if r['log_N0'] == 9), None)
    low_burden = next((r for r in burden_results if r['log_N0'] == 6), None)
    if high_burden and low_burden:
        print(f"\n2. COMPETITION EFFECT (N0/K dependence):")
        print(f"   N0=1e6 (N/K=0.001): periodic benefit = {low_burden['benefit_periodic_pct']:+.1f}%")
        print(f"   N0=1e9 (N/K=1.0):   periodic benefit = {high_burden['benefit_periodic_pct']:+.1f}%")
        if abs(high_burden['benefit_periodic_pct']) > abs(low_burden['benefit_periodic_pct']) + 5:
            print("   → COMPETITION MATTERS: benefit increases with N0/K ratio")
        else:
            print("   → COMPETITION STILL NEGLIGIBLE even at high N0/K")
    
    # Fitness cost effect
    low_cost = next((r for r in cost_results if r['fitness_cost'] == 0.01), None)
    high_cost = next((r for r in cost_results if r['fitness_cost'] == 0.05), None)
    if low_cost and high_cost:
        print(f"\n3. FITNESS COST EFFECT:")
        print(f"   cost=0.01: adaptive benefit = {low_cost['benefit_adaptive_pct']:+.1f}%")
        print(f"   cost=0.05: adaptive benefit = {high_cost['benefit_adaptive_pct']:+.1f}%")
