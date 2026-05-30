"""
Spatial immunoediting: does tissue architecture change the population-filter
vs rate-limiter conclusion? (Item 23)

Extends item 21's well-mixed immunoediting model with heterogeneous immune
accessibility — each lineage has an accessibility score a_i ∈ [0,1] drawn
from a tissue-architecture distribution. Deep-crypt lineages (low a_i) face
reduced immune surveillance; surface lineages (high a_i) face full pressure.

THIS IS A NICHE-FRAILTY MODEL, not a full spatial ABM. It captures the
first-order effect of spatial refugia (heterogeneous immune pressure) without
clone migration or spatial competition.

Key design (per rubber-duck critique):
  - Matched-mean controls: compare heterogeneous vs homogeneous at same E[a]
  - Dynamic accessibility variant: clones can migrate out of refuge
  - Sensitivity sweeps over mean accessibility and crypt fraction
  - Rich readouts: a_i among successes, conditional escape rates by bin

Grounded in:
  - PMID 32929288 (Lakatos 2020): neoantigen negative selection
  - PMID 42215447: peristromal niches as spatial refugia
  - PMID 42135010: spatial ABM reproducing immune exclusion
  - Item 21 finding: well-mixed immunoediting = population filter, not rate limiter

Author: autonomous research agent
Date: 2026-05-31
"""

import numpy as np
from pathlib import Path
import csv

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def simulate_spatial_lineages(
    k: int, mu: float, p_neo: float, alpha: float, u_escape: float,
    accessibilities: np.ndarray, migration_rate: float, rng: np.random.Generator,
) -> dict:
    """
    Simulate lineages with heterogeneous immune accessibility.

    Each lineage i has accessibility a_i; effective immune rate = alpha * a_i * n_neo.
    If migration_rate > 0, a_i can jump to ~1.0 (exposed) at that rate,
    modelling clonal expansion leaving the crypt refuge.
    """
    n = len(accessibilities)
    times, neos, escaped_flags, a_vals = [], [], [], []
    eliminated = 0

    for i in range(n):
        t, n_drv, n_neo, esc = 0.0, 0, 0, False
        a_i = accessibilities[i]

        while n_drv < k:
            rate_hit = mu
            rate_elim = 0.0 if esc else alpha * a_i * n_neo
            rate_esc = 0.0 if esc else u_escape
            rate_mig = 0.0 if (esc or migration_rate <= 0 or a_i > 0.95) \
                else migration_rate
            total = rate_hit + rate_elim + rate_esc + rate_mig

            if total <= 0:
                dt = rng.exponential(1.0 / mu)
                t += dt
                n_drv += 1
                if rng.random() < p_neo:
                    n_neo += 1
                continue

            dt = rng.exponential(1.0 / total)
            t += dt
            u = rng.random() * total

            if u < rate_hit:
                n_drv += 1
                if rng.random() < p_neo:
                    n_neo += 1
            elif u < rate_hit + rate_elim:
                eliminated += 1
                break
            elif u < rate_hit + rate_elim + rate_esc:
                esc = True
            else:
                # Migration: clone leaves crypt → fully exposed
                a_i = 0.95 + 0.05 * rng.random()
        else:
            times.append(t)
            neos.append(n_neo)
            escaped_flags.append(esc)
            a_vals.append(accessibilities[i])  # original assignment

    return {
        "times": np.array(times), "n_neos": np.array(neos),
        "escaped": np.array(escaped_flags), "a_orig": np.array(a_vals),
        "n_success": len(times), "n_eliminated": eliminated, "n_total": n,
    }


def make_accessibilities(mode: str, n: int, rng: np.random.Generator,
                         mean_a: float = 0.3, f_crypt: float = 0.7) -> np.ndarray:
    """Generate accessibility array for a given architecture mode."""
    if mode == "wellmixed":
        return np.ones(n)
    elif mode == "homogeneous_low":
        return np.full(n, mean_a)
    elif mode == "graded":
        # Beta with target mean; Beta(a,b) mean = a/(a+b)
        # Fix concentration=7, solve: a = mean*conc, b = (1-mean)*conc
        conc = 7.0
        a_param = max(mean_a * conc, 0.1)
        b_param = max((1 - mean_a) * conc, 0.1)
        return rng.beta(a_param, b_param, n)
    elif mode == "bimodal":
        n_crypt = int(n * f_crypt)
        n_exposed = n - n_crypt
        crypt_vals = rng.beta(2, 8, n_crypt)   # mean ~0.2
        exposed_vals = rng.beta(8, 2, n_exposed)  # mean ~0.8
        arr = np.concatenate([crypt_vals, exposed_vals])
        rng.shuffle(arr)
        return arr
    else:
        raise ValueError(f"Unknown mode: {mode}")


def run_architecture_comparison():
    """Compare architectures at matched mean accessibility."""
    rng = np.random.default_rng(42)
    k, mu, p_neo, alpha, u_escape = 6, 0.07, 0.5, 0.1, 0.005
    n_lin = 150_000

    # Baseline: no immune
    a_none = np.ones(n_lin)
    base = simulate_spatial_lineages(k, mu, 0.0, 0.0, 0.0, a_none, 0.0, rng)
    T_base = np.median(base["times"])

    modes = [
        ("wellmixed",        {"mean_a": 1.0}),
        ("homogeneous_low",  {"mean_a": 0.3}),
        ("graded",           {"mean_a": 0.3}),
        ("bimodal",          {"mean_a": 0.3, "f_crypt": 0.7}),
    ]

    print("=" * 90)
    print("ARCHITECTURE COMPARISON (matched mean where applicable)")
    print(f"k={k}, mu={mu}, alpha={alpha}, p_neo={p_neo}, N={n_lin}")
    print(f"Baseline (no immune) median T = {T_base:.1f} yr")
    print("=" * 90)
    hdr = f"{'mode':>18} {'E[a]':>6} {'P(mal)':>8} {'med_T':>7} " \
          f"{'delay':>7} {'P(esc)':>7} {'neo':>5} {'P(esc=0)':>9}"
    print(hdr)
    print("-" * 90)

    results = []
    for mode, kw in modes:
        acc = make_accessibilities(mode, n_lin, rng, **kw)
        res = simulate_spatial_lineages(
            k, mu, p_neo, alpha, u_escape, acc, 0.0, rng)
        ns = res["n_success"]
        if ns < 10:
            print(f"{mode:>18} {np.mean(acc):>6.3f}  insufficient successes")
            continue
        p_mal = ns / n_lin
        med_t = np.median(res["times"])
        delay = med_t / T_base
        p_esc = np.mean(res["escaped"])
        mn_neo = np.mean(res["n_neos"])
        p_no_esc = np.mean(~res["escaped"])

        print(f"{mode:>18} {np.mean(acc):>6.3f} {p_mal:>8.4f} {med_t:>7.1f} "
              f"{delay:>7.3f} {p_esc:>7.3f} {mn_neo:>5.2f} {p_no_esc:>9.3f}")
        results.append({
            "mode": mode, "mean_a": round(np.mean(acc), 4),
            "p_malignancy": round(p_mal, 5), "median_T": round(med_t, 2),
            "delay_factor": round(delay, 4), "p_escaped": round(p_esc, 4),
            "mean_neo": round(mn_neo, 3), "p_no_escape_success": round(p_no_esc, 4),
        })

    return results, T_base


def run_mean_accessibility_sweep():
    """Sweep mean accessibility: homogeneous vs graded at each level."""
    rng = np.random.default_rng(123)
    k, mu, p_neo, alpha, u_escape = 6, 0.07, 0.5, 0.1, 0.005
    n_lin = 100_000

    base = simulate_spatial_lineages(
        k, mu, 0.0, 0.0, 0.0, np.ones(n_lin), 0.0, rng)
    T_base = np.median(base["times"])

    mean_as = [0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]

    print("\n" + "=" * 90)
    print("MEAN ACCESSIBILITY SWEEP (homogeneous vs graded)")
    print("=" * 90)
    hdr = f"{'E[a]':>6} {'mode':>14} {'P(mal)':>8} {'delay':>7} " \
          f"{'P(esc)':>7} {'P(noesc)':>8}"
    print(hdr)
    print("-" * 60)

    results = []
    for mean_a in mean_as:
        for mode in ["homogeneous_low", "graded"]:
            acc = make_accessibilities(mode, n_lin, rng, mean_a=mean_a)
            res = simulate_spatial_lineages(
                k, mu, p_neo, alpha, u_escape, acc, 0.0, rng)
            ns = res["n_success"]
            if ns < 10:
                continue
            p_mal = ns / n_lin
            med_t = np.median(res["times"])
            delay = med_t / T_base
            p_esc = np.mean(res["escaped"])
            p_no = np.mean(~res["escaped"])
            print(f"{mean_a:>6.2f} {mode:>14} {p_mal:>8.4f} {delay:>7.3f} "
                  f"{p_esc:>7.3f} {p_no:>8.3f}")
            results.append({
                "mean_a": mean_a, "mode": mode, "p_malignancy": round(p_mal, 5),
                "delay_factor": round(delay, 4), "p_escaped": round(p_esc, 4),
                "p_no_escape": round(p_no, 4),
            })

    return results


def run_migration_test():
    """Test dynamic accessibility: clones migrate out of crypt."""
    rng = np.random.default_rng(789)
    k, mu, p_neo, alpha, u_escape = 6, 0.07, 0.5, 0.1, 0.005
    n_lin = 100_000

    base = simulate_spatial_lineages(
        k, mu, 0.0, 0.0, 0.0, np.ones(n_lin), 0.0, rng)
    T_base = np.median(base["times"])

    mig_rates = [0.0, 0.001, 0.005, 0.01, 0.02, 0.05]

    print("\n" + "=" * 90)
    print("MIGRATION TEST (graded E[a]=0.3, clones migrate to exposed)")
    print("=" * 90)
    hdr = f"{'mig_rate':>10} {'P(mal)':>8} {'delay':>7} {'P(esc)':>7} {'P(noesc)':>8}"
    print(hdr)
    print("-" * 50)

    results = []
    for mr in mig_rates:
        acc = make_accessibilities("graded", n_lin, rng, mean_a=0.3)
        res = simulate_spatial_lineages(
            k, mu, p_neo, alpha, u_escape, acc, mr, rng)
        ns = res["n_success"]
        if ns < 10:
            continue
        p_mal = ns / n_lin
        med_t = np.median(res["times"])
        delay = med_t / T_base
        p_esc = np.mean(res["escaped"])
        p_no = np.mean(~res["escaped"])
        print(f"{mr:>10.3f} {p_mal:>8.4f} {delay:>7.3f} {p_esc:>7.3f} {p_no:>8.3f}")
        results.append({
            "migration_rate": mr, "p_malignancy": round(p_mal, 5),
            "delay_factor": round(delay, 4), "p_escaped": round(p_esc, 4),
            "p_no_escape": round(p_no, 4),
        })

    return results


def run_accessibility_bin_analysis():
    """Analyse outcomes by accessibility bin (which niches produce tumours?)."""
    rng = np.random.default_rng(321)
    k, mu, p_neo, alpha, u_escape = 6, 0.07, 0.5, 0.1, 0.005
    n_lin = 200_000

    acc = make_accessibilities("graded", n_lin, rng, mean_a=0.3)
    res = simulate_spatial_lineages(
        k, mu, p_neo, alpha, u_escape, acc, 0.0, rng)

    bins = [(0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.5), (0.5, 0.7), (0.7, 1.0)]

    print("\n" + "=" * 90)
    print("ACCESSIBILITY BIN ANALYSIS (graded E[a]=0.3)")
    print("=" * 90)
    hdr = f"{'bin':>10} {'N_total':>8} {'N_succ':>7} {'P(mal)':>8} " \
          f"{'med_T':>7} {'P(esc)':>7} {'neo':>5}"
    print(hdr)
    print("-" * 65)

    results = []
    for lo, hi in bins:
        mask_all = (acc >= lo) & (acc < hi)
        mask_succ = (res["a_orig"] >= lo) & (res["a_orig"] < hi)
        n_tot = int(mask_all.sum())
        n_succ = int(mask_succ.sum())
        if n_tot < 10 or n_succ < 5:
            continue
        p_mal = n_succ / n_tot
        med_t = np.median(res["times"][mask_succ])
        p_esc = np.mean(res["escaped"][mask_succ])
        mn_neo = np.mean(res["n_neos"][mask_succ])
        print(f"[{lo:.1f},{hi:.1f}){'':<3} {n_tot:>8} {n_succ:>7} {p_mal:>8.4f} "
              f"{med_t:>7.1f} {p_esc:>7.3f} {mn_neo:>5.2f}")
        results.append({
            "bin_lo": lo, "bin_hi": hi, "n_total": n_tot, "n_success": n_succ,
            "p_malignancy": round(p_mal, 5), "median_T": round(med_t, 2),
            "p_escaped": round(p_esc, 4), "mean_neo": round(mn_neo, 3),
        })

    return results


def save_all(arch, sweep, mig, bins):
    """Save results to CSV files."""
    for name, data in [
        ("spatial_architecture_comparison", arch),
        ("spatial_mean_sweep", sweep),
        ("spatial_migration_test", mig),
        ("spatial_bin_analysis", bins),
    ]:
        if not data:
            continue
        path = OUTPUT_DIR / f"{name}.csv"
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=data[0].keys())
            w.writeheader()
            w.writerows(data)
        print(f"Saved: {path}")


if __name__ == "__main__":
    print("=" * 90)
    print("SPATIAL IMMUNOEDITING: TISSUE ARCHITECTURE AND IMMUNE REFUGIA")
    print("Item 23 — does spatial structure change filter vs rate-limiter?")
    print("=" * 90)

    arch, T_base = run_architecture_comparison()
    sweep = run_mean_accessibility_sweep()
    mig = run_migration_test()
    bins = run_accessibility_bin_analysis()
    save_all(arch, sweep, mig, bins)

    print("\n" + "=" * 90)
    print("DONE — see output CSVs for full results")
    print("=" * 90)
