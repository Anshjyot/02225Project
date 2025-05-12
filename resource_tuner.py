from bdr_analysis import BDRAnalysis

def _candidate_periods(P0: int):
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

def tune_system(system_model):

    analyser = BDRAnalysis(system_model)
    for core in system_model["cores"]:
        cid = core["core_id"]
        speed = core["speed_factor"]

        def _collect(comp, lst):
            lst.append(comp)
            for sub in comp.get("subcomponents", []):
                _collect(sub, lst)

        comps = []
        for c in core["components"]:
            _collect(c, comps)

        for comp in comps:
            print(f" Tuning component: {comp['name']}")

            Q0 = comp["bdr_init"]["Q"]
            P0 = comp["bdr_init"]["P"]
            alpha = Q0 / P0
            deadlines = [t["deadline"] for t in comp["tasks"]]
            P_min = 1

            best_Q, best_P = Q0, P0

            for P in _candidate_periods(P0):
                if P < P_min:
                    continue
                Q = alpha * P
                print(f"    Trying candidate: P={P}, Q={Q:.2f}")

                comp["bdr_init"]["Q"] = Q
                comp["bdr_init"]["P"] = P

                comp_ok, *_ = analyser.analyze_component(comp, speed)
                if not comp_ok["bdr"]["schedulable"]:
                    print(f"    Failed component check.")
                    continue

                full_res = analyser.run_analysis()
                all_good = True
                for res in full_res[cid].values():
                    if not res["bdr"]["schedulable"]:
                        all_good = False
                        print(f"    Failed core check.")
                        break

                if all_good:
                    best_Q, best_P = Q, P
                    print(f"    Passed! Keeping P={P}, Q={Q:.2f}")
                else:
                    break

            if (best_P, best_Q) != (P0, Q0):
                print(f"   • {comp['name']}: P {P0:.0f}→{best_P:.0f}, "
                      f"Δ {2 * (P0 - Q0):.1f}→{2 * (best_P - best_Q):.1f}")
            comp["bdr_init"]["Q"] = best_Q
            comp["bdr_init"]["P"] = best_P
