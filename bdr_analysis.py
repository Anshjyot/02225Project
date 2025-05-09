import math
from functools import reduce
from math import lcm

from dbf_utils import dbf_edf, dbf_fps
from wcrt_analysis import compute_wcrt, compute_wcrt_edf, compute_wcrt_rm


class BDRAnalysis:
    def __init__(self, system_model):
        self.system_model = system_model

    @staticmethod
    def half_half_to_qp(alpha: float, delta: float):
        if not (0 < alpha < 1):
            raise ValueError("Half-Half only valid for 0 < α < 1.")
        P = delta / (1 - alpha)
        Q = (alpha * P) / 2
        return Q, P

    @staticmethod
    def sbf_bdr(alpha, delta, t):
        return 0.0 if t <= delta else alpha * (t - delta)

    @staticmethod
    def sbf_prm(Q, P, t):
        return max(0.0, math.floor(t / P) * Q)

    @staticmethod
    def lcm(a, b):
        return abs(a * b) // math.gcd(int(a), int(b))

    @staticmethod
    def lcm_of_periods(periods):
        return int(reduce(BDRAnalysis.lcm, periods))

    @staticmethod
    def dbf_server(Q, P, J, t):
        if t < J + P:
            return 0.0
        n_jobs = math.floor((t - (J + P)) / P) + 1
        return n_jobs * Q

    def analyze_component(self, comp, speed_factor):
        tasks = comp["tasks"]
        sched = comp["scheduler"].upper()
        Q = comp["bdr_init"]["alpha"]
        P = comp["bdr_init"]["delay"]
        alpha = Q / P
        delta = 2 * (P - Q)
        dbf = dbf_edf if sched == "EDF" else dbf_fps

        periods = [t["period"] for t in tasks]
        deadlines = [t["deadline"] for t in tasks]
        H = max(self.lcm_of_periods(periods), int(2 * max(deadlines)))

        # BDR analysis
        bdr_ok = True
        for t in range(H + 1):
            if dbf(tasks, t) > self.sbf_bdr(alpha, delta, t) + 1e-9:
                bdr_ok = False
                break
        bdr_wcrt = compute_wcrt(tasks, sched, alpha, delta)

        # PRM analysis
        prm_ok = True
        for t in range(H + 1):
            if dbf(tasks, t) > self.sbf_prm(Q, P, t) + 1e-9:
                prm_ok = False
                break
        if sched == "EDF":
            prm_wcrt = compute_wcrt_edf(tasks, alpha, 0.0)  # delta = 0 for PRM (no delay model)
        else:
            prm_wcrt = compute_wcrt_rm(tasks, 0.0)  # no jitter for PRM

        result = {
            "bdr": {
                "alpha": alpha,
                "delay": delta,
                "schedulable": bdr_ok,
                "wcrt": bdr_wcrt
            },
            "prm": {
                "Q": Q,
                "P": P,
                "schedulable": prm_ok,
                "wcrt": prm_wcrt
            }
        }

        return result, Q, P, delta, bdr_ok and prm_ok

    def run_analysis(self):
        results = {}
        for core in self.system_model["cores"]:
            c_id = core["core_id"]
            core_sched = core["scheduler"].upper()
            results[c_id] = {}

            core_servers = []

            for comp in core["components"]:
                def recurse(comp):
                    cname = comp["name"]
                    res, Q, P, delta, ok = self.analyze_component(comp, core["speed_factor"])
                    results[c_id][cname] = res

                    core_servers.append({
                        "Q": Q, "P": P, "J": delta,
                        "priority": comp.get("priority"),
                        "name": cname,
                        "ok_inside": ok
                    })

                    for sub in comp.get("subcomponents", []):
                        recurse(sub)

                recurse(comp)

            if not all(s["ok_inside"] for s in core_servers):
                continue

            if core_sched == "EDF":
                periods = [int(s["P"]) for s in core_servers]
                H_core = lcm(*periods)
                for t in range(H_core + 1):
                    demand = sum(self.dbf_server(s["Q"], s["P"], s["J"], t) for s in core_servers)
                    if demand > t + 1e-9:
                        for s in core_servers:
                            results[c_id][s["name"]]["bdr"]["schedulable"] = False
                            results[c_id][s["name"]]["prm"]["schedulable"] = False
                        break
            else:
                hp_sorted = sorted(core_servers, key=lambda s: s["priority"])
                for i, s in enumerate(hp_sorted):
                    R = s["Q"]
                    while True:
                        I = sum(
                            math.ceil((R + hp["J"]) / hp["P"]) * hp["Q"]
                            for hp in hp_sorted[:i]
                        )
                        if I + s["Q"] == R:
                            break
                        if I + s["Q"] > s["P"]:
                            for ss in core_servers:
                                results[c_id][ss["name"]]["bdr"]["schedulable"] = False
                                results[c_id][ss["name"]]["prm"]["schedulable"] = False
                            break
                        R = I + s["Q"]
                    else:
                        continue
                    break

        return results
