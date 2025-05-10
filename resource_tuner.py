"""
resource_tuner.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Optional extension: tighten (Q,P) of every component so that
its BDR delay Δ = 2·(P − Q) is as small as possible *without*
making anything unschedulable.

– Works for both EDF and RM inner schedulers
– Never decreases α = Q/P, so DBF ≤ SBF on the component itself
  can only improve
– Re-checks the full core after each tentative change, so a core
  that was schedulable stays schedulable
"""

from copy import deepcopy
import math

from bdr_analysis import BDRAnalysis


# ---------------------------------------------------------------------------
# Helper: iterate over strictly smaller candidate periods
# ---------------------------------------------------------------------------

def _candidate_periods(P0: int):
    """
    Yields periods < P0 in descending aggressiveness order:
        P0//2, P0//3, P0//4, …, 1
    No repetitions.
    """
    seen = set()
    k = 2
    while True:
        P = P0 // k
        if P < 1:
            return
        if P not in seen:
            seen.add(P)
            yield P
        k += 1


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def tune_system(system_model):
    """
    In-place optimisation of every component’s (Q,P).

    Call this *immediately after* load_csv_files() and *before*
    you run either greedy_core_assigner or the simulator.
    """

    analyser = BDRAnalysis(system_model)

    # ──────────────────────────────────────────────────────────────────────
    # loop over cores → components
    # ──────────────────────────────────────────────────────────────────────
    for core in system_model["cores"]:
        cid = core["core_id"]
        speed = core["speed_factor"]

        # collect a flat list of every component on this core
        def _collect(comp, lst):
            lst.append(comp)
            for sub in comp.get("subcomponents", []):
                _collect(sub, lst)

        comps = []
        for c in core["components"]:
            _collect(c, comps)

        # ----------------------------------------------------------------
        # try to tighten each component independently
        # ----------------------------------------------------------------
        for comp in comps:
            print(f"🔍 Tuning component: {comp['name']}")

            # current (Q,P,α,Δ) and quick bounds
            Q0 = comp["bdr_init"]["Q"]
            P0 = comp["bdr_init"]["P"]
            alpha = Q0 / P0
            deadlines = [t["deadline"] for t in comp["tasks"]]
            P_min = 1  # <---- FORCE TUNING TO HAPPEN (can be reset later)

            best_Q, best_P = Q0, P0  # keep a fallback

            for P in _candidate_periods(P0):
                if P < P_min:
                    continue
                Q = alpha * P
                print(f"    🔧 Trying candidate: P={P}, Q={Q:.2f}")

                # ── try this candidate
                comp["bdr_init"]["Q"] = Q
                comp["bdr_init"]["P"] = P

                # (A) intra-component schedulability
                comp_ok, *_ = analyser.analyze_component(comp, speed)
                if not comp_ok["bdr"]["schedulable"]:
                    print(f"    ❌ Failed component check.")
                    continue

                # (B) full-core check – reuse existing analyser logic
                full_res = analyser.run_analysis()
                all_good = True
                for res in full_res[cid].values():
                    if not res["bdr"]["schedulable"]:
                        all_good = False
                        print(f"    ❌ Failed core check.")
                        break

                if all_good:
                    best_Q, best_P = Q, P
                    print(f"    ✅ Passed! Keeping P={P}, Q={Q:.2f}")
                else:
                    break  # stop testing if core cannot accept more

            # ── commit best found values
            if (best_P, best_Q) != (P0, Q0):
                print(f"   • {comp['name']}: P {P0:.0f}→{best_P:.0f}, "
                      f"Δ {2 * (P0 - Q0):.1f}→{2 * (best_P - best_Q):.1f}")
            comp["bdr_init"]["Q"] = best_Q
            comp["bdr_init"]["P"] = best_P
