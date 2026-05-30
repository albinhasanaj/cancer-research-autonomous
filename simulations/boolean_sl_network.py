"""
Boolean network model of the DDR / cell-cycle checkpoint pathway.

Simulates single and double knockouts under DNA damage to identify
synthetic-lethal node pairs from network topology alone.

Compares topological predictions to known SL pairs from:
  research/literature/2026-05-30_synthetic_lethality_survey.md

Network: 14 nodes representing DDR sensors, checkpoint effectors,
repair pathways, and cell-cycle controllers. Boolean update rules
derived from canonical pathway logic (not fitted to data).

Output: simulations/output/boolean_sl_pairs.csv
"""

import csv
import os
from itertools import combinations

# ── Node definitions ─────────────────────────────────────────────────────────
# Each node is a protein/pathway with binary state (1=active, 0=inactive/lost).
# "Active" means functional/expressed at normal level.
NODES = [
    "DNA_damage",  # input signal (always ON in damage scenario)
    "ATM",         # DSB sensor kinase
    "ATR",         # replication stress sensor
    "TP53",        # G1/S checkpoint transcription factor
    "CHK1",        # S/G2 checkpoint kinase (ATR→CHK1)
    "CHK2",        # checkpoint kinase (ATM→CHK2)
    "WEE1",        # G2/M gatekeeper (inhibits CDK1)
    "BRCA1",       # HR repair scaffold
    "BRCA2",       # HR repair effector (RAD51 loading)
    "PARP1",       # SSB/BER repair; trapping → fork collapse if HR absent
    "WRN",         # helicase for replication structure resolution
    "RB1",         # G1/S brake; loss → E2F-driven replication stress
    "PLK1",        # mitotic kinase; required for mitotic fidelity
    "CELL_SURV",   # output: 1 = cell survives, 0 = death
]

NODE_IDX = {n: i for i, n in enumerate(NODES)}


# ── Boolean update rules ─────────────────────────────────────────────────────
# Each rule takes the current state dict and returns the next value for a node.
# Logic reflects canonical pathway wiring (simplified, deterministic).

def update_rules(s):
    """Return next-state dict given current state dict `s`."""
    ns = {}

    # Input: DNA_damage is always ON (we simulate under damage)
    ns["DNA_damage"] = 1

    # Sensors activate if damage present (and not knocked out)
    ns["ATM"] = s["DNA_damage"] and s["ATM"]
    ns["ATR"] = s["DNA_damage"] and s["ATR"]

    # TP53 activated by ATM or CHK2 (G1/S checkpoint arm)
    ns["TP53"] = (s["ATM"] or s["CHK2"]) and s["TP53"]

    # CHK1 activated by ATR
    ns["CHK1"] = s["ATR"] and s["CHK1"]

    # CHK2 activated by ATM
    ns["CHK2"] = s["ATM"] and s["CHK2"]

    # WEE1 maintained by CHK1 (S/G2 arrest requires CHK1→WEE1)
    ns["WEE1"] = s["CHK1"] and s["WEE1"]

    # HR repair requires BRCA1 AND BRCA2
    hr_repair = s["BRCA1"] and s["BRCA2"]
    ns["BRCA1"] = s["BRCA1"]  # constitutive (unless KO)
    ns["BRCA2"] = s["BRCA2"]  # constitutive (unless KO)

    # PARP1: constitutive repair pathway (unless KO)
    ns["PARP1"] = s["PARP1"]

    # WRN: constitutive helicase (unless KO)
    ns["WRN"] = s["WRN"]

    # RB1: constitutive G1/S brake (unless KO)
    ns["RB1"] = s["RB1"]

    # PLK1: needed for mitotic fidelity; active unless KO
    ns["PLK1"] = s["PLK1"]

    # ── Cell survival logic ──────────────────────────────────────────────
    # Three requirements for survival under DNA damage:
    #   1. REPAIR: at least one repair arm functional (HR or alt-repair)
    #   2. CHECKPOINT: at least one checkpoint holds (G1 via TP53, or
    #      G2 via ATR→CHK1→WEE1) — gives time for repair
    #   3. MITOTIC FIDELITY: if RB1 lost (replication stress + mitotic
    #      gene overexpression), PLK1 needed for viable division
    # SL emerges when two redundant arms of the SAME requirement are
    # both lost.

    # Repair: two redundant arms
    can_repair_hr = hr_repair  # BRCA1 AND BRCA2
    can_repair_alt = s["PARP1"] and s["WRN"]
    repair_ok = can_repair_hr or can_repair_alt

    # Checkpoint: two redundant arms (G1 and G2)
    # ATM feeds TP53 activation; if ATM lost, TP53 cannot activate → G1 gone
    g1_checkpoint = ns["TP53"]  # requires ATM or CHK2 upstream
    g2_checkpoint = ns["CHK1"] and s["WEE1"]  # ATR→CHK1→WEE1
    checkpoint_ok = g1_checkpoint or g2_checkpoint

    # Mitotic fidelity under replication stress
    rb1_stress = not s["RB1"]
    mitotic_ok = s["PLK1"]

    # Survival requires: repair AND checkpoint AND (no RB1-stress OR PLK1)
    if not repair_ok:
        ns["CELL_SURV"] = 0  # unrepaired damage → death
    elif not checkpoint_ok:
        ns["CELL_SURV"] = 0  # no arrest → mitotic catastrophe
    elif rb1_stress and not mitotic_ok:
        ns["CELL_SURV"] = 0  # replication stress + no fidelity → death
    else:
        ns["CELL_SURV"] = 1

    return ns


# ── Simulation engine ────────────────────────────────────────────────────────

def make_initial_state(knockouts=None):
    """Create initial state: all nodes ON except knockouts (set to 0)."""
    state = {n: 1 for n in NODES}
    state["CELL_SURV"] = 1  # assume alive at start
    if knockouts:
        for ko in knockouts:
            state[ko] = 0
    return state


def simulate(knockouts=None, max_steps=20):
    """
    Run synchronous Boolean update until steady state or max_steps.
    Returns final CELL_SURV value.
    """
    state = make_initial_state(knockouts)
    for _ in range(max_steps):
        new_state = update_rules(state)
        if new_state == state:
            break
        state = new_state
    return state["CELL_SURV"]


# ── Knockout screen ──────────────────────────────────────────────────────────

# Nodes that can be knocked out (exclude input signal and output)
KO_CANDIDATES = [n for n in NODES if n not in ("DNA_damage", "CELL_SURV")]


def run_screen():
    """Run all single and double KO combinations; identify SL pairs."""
    # Wild-type baseline
    wt_surv = simulate(knockouts=None)
    assert wt_surv == 1, "WT must survive under damage (checkpoint + repair)"

    # Single knockouts
    single_ko_results = {}
    for node in KO_CANDIDATES:
        surv = simulate(knockouts=[node])
        single_ko_results[node] = surv

    # Double knockouts
    sl_pairs = []
    all_double = []
    for n1, n2 in combinations(KO_CANDIDATES, 2):
        surv = simulate(knockouts=[n1, n2])
        is_sl = (
            single_ko_results[n1] == 1
            and single_ko_results[n2] == 1
            and surv == 0
        )
        all_double.append((n1, n2, surv, is_sl))
        if is_sl:
            sl_pairs.append((n1, n2))

    return single_ko_results, sl_pairs, all_double


# ── Known SL pairs for comparison ────────────────────────────────────────────
# Mapped to node names in this model
KNOWN_SL = [
    ("BRCA1", "PARP1", "BRCA–PARP (PMID 42092061)"),
    ("BRCA2", "PARP1", "BRCA–PARP (PMID 42092061)"),
    ("TP53", "ATR", "TP53–ATR (PMID 40759474)"),
    ("TP53", "CHK1", "TP53–CHK1 (PMID 40759474)"),
    ("TP53", "WEE1", "TP53–WEE1 (PMID 40759474)"),
    ("ATM", "ATR", "ATM–ATR (PMID 40759474)"),
    ("ATM", "CHK1", "ATM–CHK1 (PMID 40759474)"),
    ("ATM", "WEE1", "ATM–WEE1 (PMID 40759474)"),
    ("RB1", "PLK1", "RB1–PLK1 (PMID 34359636)"),
]


def compare_to_known(sl_pairs):
    """Check which known SL pairs are recovered by topology."""
    sl_set = set(sl_pairs)
    # Normalize: pairs are unordered
    sl_set_norm = set()
    for a, b in sl_set:
        sl_set_norm.add(tuple(sorted([a, b])))

    results = []
    for n1, n2, label in KNOWN_SL:
        pair = tuple(sorted([n1, n2]))
        recovered = pair in sl_set_norm
        results.append((n1, n2, label, recovered))
    return results


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    single_ko, sl_pairs, all_double = run_screen()

    print("=" * 70)
    print("BOOLEAN DDR/CELL-CYCLE NETWORK — SYNTHETIC LETHALITY SCREEN")
    print("=" * 70)

    # Single KO results
    print("\n── Single knockouts (lethal alone) ──")
    lethal_single = [n for n, s in single_ko.items() if s == 0]
    viable_single = [n for n, s in single_ko.items() if s == 1]
    if lethal_single:
        print(f"  Lethal: {', '.join(lethal_single)}")
    else:
        print("  None lethal alone (all single KOs viable)")
    print(f"  Viable: {len(viable_single)}/{len(KO_CANDIDATES)} nodes")

    # SL pairs
    print(f"\n── Synthetic-lethal pairs (from topology): {len(sl_pairs)} ──")
    for n1, n2 in sorted(sl_pairs):
        print(f"  {n1} + {n2}")

    # Comparison to known
    print("\n── Comparison to literature-known SL pairs ──")
    comparison = compare_to_known(sl_pairs)
    recovered = sum(1 for *_, r in comparison if r)
    total = len(comparison)
    print(f"  Recovered: {recovered}/{total}")
    for n1, n2, label, rec in comparison:
        status = "✓ RECOVERED" if rec else "✗ missed"
        print(f"  {status}: {label}")

    # Novel predictions (not in known set)
    known_norm = set(tuple(sorted([n1, n2])) for n1, n2, _ in KNOWN_SL)
    novel = [
        (a, b) for a, b in sl_pairs
        if tuple(sorted([a, b])) not in known_norm
    ]
    if novel:
        print(f"\n── Novel topological predictions ({len(novel)}) ──")
        for a, b in sorted(novel):
            print(f"  {a} + {b}")

    # Write output CSV
    os.makedirs("simulations/output", exist_ok=True)
    out_path = "simulations/output/boolean_sl_pairs.csv"
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["node1", "node2", "is_SL", "known_pair"])
        for n1, n2, surv, is_sl in sorted(all_double):
            pair_norm = tuple(sorted([n1, n2]))
            known = pair_norm in known_norm
            w.writerow([n1, n2, is_sl, known])

    print(f"\n  Output: {out_path}")
    print(f"  Total double-KO combinations tested: {len(all_double)}")

    # Summary statistics
    print("\n── Summary ──")
    print(f"  Nodes: {len(KO_CANDIDATES)} (knockoutable)")
    print(f"  Pairs tested: {len(all_double)}")
    print(f"  SL pairs found: {len(sl_pairs)}")
    print(f"  Known pairs recovered: {recovered}/{total} "
          f"({100*recovered/total:.0f}%)")
    print(f"  Novel predictions: {len(novel)}")


if __name__ == "__main__":
    main()
