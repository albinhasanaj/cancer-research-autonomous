"""
Evolutionary dynamics of resistance to PARP-inhibitor therapy via BRCA reversion.

Stochastic birth-death model (Gillespie SSA) of a tumour under PARPi selection
where resistant cells arise via BRCA-reversion mutations that restore HR.

Framework: Iwasa, Michor & Nowak (2006) Proc R Soc B 273:1137-1144.
Parameterised for PARP-inhibitor + BRCA-reversion using clinical constraints.

Parameters (literature-grounded ranges):
  - N0: tumour cells at treatment start (1e8 – 1e10; ~1cm – 10cm tumour)
  - u:  reversion mutation rate per division (~1e-9 – 1e-7; frameshift reversion)
  - b_S, d_S: sensitive cell birth/death under PARPi
  - b_R, d_R: resistant cell birth/death (fitness restored)
  - Detection threshold rho: resistant clone size for clinical progression

Outputs:
  - Time-to-resistance distributions across parameter regimes
  - Analytic vs simulation comparison
  - Sensitivity to N0, u, drug kill rate
  - Comparison to clinical PFS (~12-24 months)

Author: autonomous research agent
Date: 2026-05-30
"""

import numpy as np
from pathlib import Path
import csv

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# --- Parameters ---

# Baseline: ovarian BRCA-mut under PARPi maintenance
PARAMS_BASELINE = dict(
    N0=1e9,           # cells at start of maintenance (~1-2cm residual)
    u=1e-8,           # reversion rate per division (conservative; frameshift)
    b_S=0.1,          # sensitive birth rate /day (~doubling time ~10d)
    d_S=0.14,         # sensitive death rate /day (net decline under PARPi)
    b_R=0.1,          # resistant birth rate /day (HR restored)
    d_R=0.05,         # resistant death rate /day (normal turnover)
    rho=1e6,          # detection threshold (clinically apparent progression)
)


def net_growth_S(p):
    """Net growth rate of sensitive population."""
    return p['b_S'] - p['d_S']


def net_growth_R(p):
    """Net growth rate of resistant population."""
    return p['b_R'] - p['d_R']


# --- Analytic approximation (Iwasa et al. 2006) ---

def analytic_time_to_resistance(p):
    """
    Approximate median time to resistance (days).

    Two phases:
    1) Waiting time for first surviving resistant mutant (t_wait)
    2) Expansion time of resistant clone to detection (t_grow)

    The effective mutation supply rate accounts for the probability that
    a new resistant mutant survives stochastic extinction = 1 - d_R/b_R.
    """
    r_S = net_growth_S(p)  # negative under drug
    r_R = net_growth_R(p)  # positive (resistant grows)

    # Probability a new resistant cell survives drift
    if p['b_R'] > p['d_R']:
        p_survive = 1.0 - p['d_R'] / p['b_R']
    else:
        p_survive = 0.0
        return float('inf')

    # Effective mutation supply: u * b_S * N(t) * p_survive
    # N(t) = N0 * exp(r_S * t) for sensitive pop (declining if r_S < 0)
    # Cumulative supply up to t: integral of u * b_S * N0 * exp(r_S*s) * p_survive ds

    # Median waiting time: solve integral = ln(2)
    # If r_S < 0: integral = u*b_S*N0*p_survive * (1 - exp(r_S*t)) / (-r_S)
    # Set = ln(2) and solve for t

    supply_rate_0 = p['u'] * p['b_S'] * p['N0'] * p_survive

    if r_S < 0:
        # Sensitive pop declining
        max_supply = supply_rate_0 / (-r_S)  # total cumulative supply (t→∞)
        if max_supply < np.log(2):
            # Not enough supply — resistance unlikely before tumour dies
            return float('inf')
        # Solve: supply_rate_0/(-r_S) * (1 - exp(r_S*t)) = ln(2)
        t_wait = np.log(1.0 - np.log(2) * (-r_S) / supply_rate_0) / r_S
    elif r_S == 0:
        t_wait = np.log(2) / supply_rate_0
    else:
        # Sensitive pop growing (shouldn't happen under effective drug)
        t_wait = np.log(1.0 + np.log(2) * r_S / supply_rate_0) / r_S

    # Expansion time: resistant clone from 1 cell to rho
    t_grow = np.log(p['rho']) / r_R

    return t_wait + t_grow


# --- Stochastic simulation (tau-leaping for large populations) ---

def simulate_resistance_tauleap(p, dt=1.0, max_days=3650, rng=None):
    """
    Tau-leaping simulation of resistance emergence.

    Returns time (days) when resistant clone reaches rho, or max_days if not.
    Uses tau-leaping (dt=1 day) since populations are large.
    """
    if rng is None:
        rng = np.random.default_rng()

    S = p['N0']
    R = 0.0
    t = 0.0

    while t < max_days:
        if S < 1 and R < p['rho']:
            # Tumour extinct before resistance
            return max_days

        # Sensitive cell events (Poisson approximation for large N)
        if S > 0:
            births_S = rng.poisson(p['b_S'] * S * dt) if S > 0 else 0
            deaths_S = rng.poisson(p['d_S'] * S * dt) if S > 0 else 0
            # Mutations: each birth has probability u of producing resistant
            mutations = rng.binomial(births_S, p['u']) if births_S > 0 else 0
        else:
            births_S = deaths_S = mutations = 0

        # Resistant cell events
        if R > 0:
            births_R = rng.poisson(p['b_R'] * R * dt)
            deaths_R = rng.poisson(p['d_R'] * R * dt)
        else:
            births_R = deaths_R = 0

        # Update populations
        S = max(0, S + births_S - deaths_S - mutations)
        R = max(0, R + births_R - deaths_R + mutations)

        t += dt

        # Check detection
        if R >= p['rho']:
            return t

    return max_days


def run_parameter_scan(n_reps=500):
    """
    Scan over key parameters and compute time-to-resistance distributions.
    Compare to analytic prediction and clinical PFS data.
    """
    rng = np.random.default_rng(42)

    # Parameter variations
    scan_configs = [
        # (label, param_overrides)
        ("baseline", {}),
        ("large_tumour_N0=1e10", {"N0": 1e10}),
        ("small_tumour_N0=1e8", {"N0": 1e8}),
        ("high_mutation_u=1e-7", {"u": 1e-7}),
        ("low_mutation_u=1e-9", {"u": 1e-9}),
        ("strong_drug_dS=0.18", {"d_S": 0.18}),
        ("weak_drug_dS=0.11", {"d_S": 0.11}),
    ]

    results = []

    for label, overrides in scan_configs:
        params = {**PARAMS_BASELINE, **overrides}
        t_analytic = analytic_time_to_resistance(params)

        # Run stochastic simulations
        times = []
        for _ in range(n_reps):
            t_res = simulate_resistance_tauleap(params, rng=rng)
            times.append(t_res)

        times = np.array(times)
        # Exclude censored (= max_days)
        observed = times[times < 3650]
        frac_resistant = len(observed) / n_reps

        if len(observed) > 0:
            median_sim = np.median(observed)
            q25 = np.percentile(observed, 25)
            q75 = np.percentile(observed, 75)
        else:
            median_sim = q25 = q75 = float('nan')

        results.append({
            "label": label,
            "N0": params['N0'],
            "u": params['u'],
            "net_kill_rate": params['d_S'] - params['b_S'],
            "t_analytic_days": round(t_analytic, 1),
            "t_analytic_months": round(t_analytic / 30.44, 1),
            "median_sim_days": round(median_sim, 1),
            "median_sim_months": round(median_sim / 30.44, 1),
            "q25_months": round(q25 / 30.44, 1),
            "q75_months": round(q75 / 30.44, 1),
            "frac_resistant_10yr": round(frac_resistant, 3),
            "n_reps": n_reps,
        })

        print(f"  {label}: analytic={t_analytic/30.44:.1f}mo, "
              f"sim_median={median_sim/30.44:.1f}mo, "
              f"frac_resist={frac_resistant:.3f}")

    return results


def run_preexisting_resistance_analysis():
    """
    Compute probability that resistance is PREEXISTING at treatment start
    (Luria-Delbrück / Iwasa formula) as f(N0, u).
    """
    print("\n--- Preexisting resistance probability ---")
    results = []

    for log_N0 in [7, 8, 9, 10, 11]:
        for log_u in [-9, -8, -7, -6]:
            N0 = 10**log_N0
            u = 10**log_u
            # P(preexist) ≈ 1 - exp(-u*N0) for large tumours grown from 1 cell
            # More precisely: expected number of resistant cells at size N
            # = u*N0 (for neutral growth; larger if resistant has fitness advantage)
            p_preexist = 1.0 - np.exp(-u * N0)
            results.append({
                "log10_N0": log_N0,
                "log10_u": log_u,
                "P_preexisting": round(p_preexist, 4),
            })

    # Print table
    print(f"{'log10(N0)':<12} {'log10(u)':<10} {'P(preexist)':<12}")
    for r in results:
        print(f"{r['log10_N0']:<12} {r['log10_u']:<10} {r['P_preexisting']:<12}")

    return results


def run_maintenance_calibration(n_reps=500):
    """
    Clinically-calibrated maintenance scenario.

    Post-surgery + platinum → minimal residual disease (N0 ~ 1e5–1e7).
    PARPi maintenance. Clinical median PFS: ~24 months (SOLO-1 BRCA-mut)
    to ~56 months (5-year update). Identify parameter regime matching this.
    """
    print("\n--- Maintenance calibration (MRD setting) ---")
    print("  Clinical target: median PFS ~24-36 months")

    # Maintenance scenarios: smaller N0, possibly slower resistant growth
    maint_configs = [
        ("MRD_N0=1e5_u=1e-8", {"N0": 1e5, "u": 1e-8}),
        ("MRD_N0=1e6_u=1e-8", {"N0": 1e6, "u": 1e-8}),
        ("MRD_N0=1e7_u=1e-8", {"N0": 1e7, "u": 1e-8}),
        ("MRD_N0=1e6_u=1e-9", {"N0": 1e6, "u": 1e-9}),
        ("MRD_N0=1e6_slow_R", {"N0": 1e6, "u": 1e-8,
                                "b_R": 0.07, "d_R": 0.05}),  # net 0.02/d
        ("MRD_N0=1e6_very_slow_R", {"N0": 1e6, "u": 1e-8,
                                     "b_R": 0.06, "d_R": 0.05}),  # net 0.01/d
    ]

    rng = np.random.default_rng(123)
    results = []

    for label, overrides in maint_configs:
        params = {**PARAMS_BASELINE, **overrides}
        t_analytic = analytic_time_to_resistance(params)

        times = []
        for _ in range(n_reps):
            t_res = simulate_resistance_tauleap(params, rng=rng)
            times.append(t_res)

        times = np.array(times)
        observed = times[times < 3650]
        frac_resistant = len(observed) / n_reps

        if len(observed) > 0:
            median_sim = np.median(observed)
            q25 = np.percentile(observed, 25)
            q75 = np.percentile(observed, 75)
        else:
            median_sim = q25 = q75 = float('nan')

        results.append({
            "label": label,
            "N0": params['N0'],
            "u": params['u'],
            "net_R_growth": params['b_R'] - params['d_R'],
            "t_analytic_months": round(t_analytic / 30.44, 1),
            "median_sim_months": round(median_sim / 30.44, 1),
            "q25_months": round(q25 / 30.44, 1),
            "q75_months": round(q75 / 30.44, 1),
            "frac_resistant_10yr": round(frac_resistant, 3),
        })

        print(f"  {label}: analytic={t_analytic/30.44:.1f}mo, "
              f"sim_median={median_sim/30.44:.1f}mo, "
              f"frac_resist={frac_resistant:.3f}")

    return results


def main():
    print("=" * 60)
    print("PARP-inhibitor resistance dynamics via BRCA reversion")
    print("Stochastic birth-death + Iwasa/Michor/Nowak analytic")
    print("=" * 60)

    # 1. Analytic baseline
    t_base = analytic_time_to_resistance(PARAMS_BASELINE)
    print(f"\nBaseline analytic T_resist (bulk tumour N0=1e9): {t_base:.0f} days "
          f"({t_base/30.44:.1f} months)")
    print(f"  Clinical PFS reference: 24-56 months (SOLO-1, PRIMA; BRCA-mut)")

    # 2. Parameter scan with stochastic simulation
    print("\n--- Parameter scan (tau-leaping, N_reps=500) ---")
    scan_results = run_parameter_scan(n_reps=500)

    # 3. Clinically-calibrated maintenance scenario
    maint_results = run_maintenance_calibration(n_reps=500)

    # 4. Preexisting resistance
    preexist_results = run_preexisting_resistance_analysis()

    # 5. Save results
    out_path = OUTPUT_DIR / "parp_resistance_scan.csv"
    with open(out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=scan_results[0].keys())
        writer.writeheader()
        writer.writerows(scan_results)
    print(f"\nScan results saved to {out_path}")

    out_maint = OUTPUT_DIR / "parp_resistance_maintenance.csv"
    with open(out_maint, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=maint_results[0].keys())
        writer.writeheader()
        writer.writerows(maint_results)
    print(f"Maintenance results saved to {out_maint}")

    out_path2 = OUTPUT_DIR / "parp_resistance_preexisting.csv"
    with open(out_path2, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=preexist_results[0].keys())
        writer.writeheader()
        writer.writerows(preexist_results)
    print(f"Preexisting prob saved to {out_path2}")

    # 6. Summary & interpretation
    print("\n" + "=" * 60)
    print("SUMMARY & INTERPRETATION")
    print("=" * 60)
    baseline = scan_results[0]
    print(f"\n1. BULK TUMOUR (N0=1e9, pre-treatment setting):")
    print(f"   Analytic median: {baseline['t_analytic_months']} months")
    print(f"   Simulation median: {baseline['median_sim_months']} months")
    print(f"   P(preexisting resistance): ~1.0 (u*N0 >> 1)")
    print(f"   → Resistance essentially GUARANTEED before treatment starts")
    print(f"   → 'Time to resistance' = expansion time only (~9 months)")

    print(f"\n2. MAINTENANCE SETTING (post-surgery MRD):")
    for r in maint_results:
        if "1e6_u=1e-8\"" not in r['label']:
            continue
    # Print the maintenance results summary
    print(f"   At N0=1e6, u=1e-8: P(preexist)=0.01 → resistance must ARISE")
    print(f"   Time dominated by waiting for first surviving mutant + expansion")

    print(f"\n3. KEY FINDING — WHY CLINICAL PFS IS LONGER THAN NAIVE PREDICTION:")
    print(f"   The Iwasa model with N0=1e9 (bulk tumour) predicts ~9 months,")
    print(f"   but PARPi maintenance starts after surgery+chemo → MRD (N0~1e5-1e7).")
    print(f"   With N0=1e6: P(preexisting)~0.01; resistance must arise de novo")
    print(f"   under drug pressure from a DECLINING sensitive population,")
    print(f"   which drastically limits mutation supply.")
    print(f"   → Surgical debulking + chemo is the rate-limiting step for PFS.")

    print(f"\n4. PARAMETER SENSITIVITY:")
    print(f"   - N0 dominates (sets preexisting vs de novo regime boundary)")
    print(f"   - u secondary (but u*N0 is the key product)")
    print(f"   - Drug kill rate: stronger kill → faster S decline → LESS supply")
    print(f"     (paradox: more effective drug can delay resistance if MRD)")
    print(f"   - Resistant growth rate: determines expansion phase duration")


if __name__ == "__main__":
    main()
