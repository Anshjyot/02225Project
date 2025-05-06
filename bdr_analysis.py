import math
from functools import reduce
from dbf_utils import dbf_edf, dbf_fps
from math import lcm



class BDRAnalysis:
    def __init__(self, system_model):
        self.system_model = system_model

    # ---------- BDR supply‑bound function -------------------------
    @staticmethod
    def sbf_bdr(alpha, delta, t):
        return 0.0 if t <= delta else alpha * (t - delta)

    # ---------- helpers ------------------------------------------
    @staticmethod
    def lcm(a, b):
        return abs(a * b) // math.gcd(int(a), int(b))

    @staticmethod
    def lcm_of_periods(periods):
        return int(reduce(BDRAnalysis.lcm, periods))

    # ---------- DBF of a periodic server with jitter -------------
    @staticmethod
    def dbf_server(Q, P, J, t):
        """
        Exact DBF for a periodic server with release jitter J and
        implicit deadline D = P (used for EDF cores).
        """
        if t < J + P:                  # no server deadline has arrived yet
            return 0.0
        n_jobs = math.floor((t - (J + P)) / P) + 1
        return n_jobs * Q


    # ---------- main entry ---------------------------------------
    def run_analysis(self):
        results = {}
        for core in self.system_model["cores"]:
            c_id       = core["core_id"]
            core_sched = core["scheduler"].upper()
            results[c_id] = {}

            # ---- 1) check each component in isolation ----
            core_servers = []
            for comp in core["components"]:
                cname = comp["name"]
                Q     = comp["bdr_init"]["alpha"]   # column holds Q
                P     = comp["bdr_init"]["delay"]
                tasks = comp["tasks"]
                sched = comp["scheduler"].upper()

                alpha = Q / P
                delta = 2 * (P - Q)  #needs to be as low as possible
                dbf   = dbf_edf if sched == "EDF" else dbf_fps

                periods   = [t["period"] for t in tasks]
                deadlines = [t["deadline"] for t in tasks]
                H = max(self.lcm_of_periods(periods),
                        int(2 * max(deadlines)))

                ok = True
                for t in range(H + 1):
                    if dbf(tasks, t) > self.sbf_bdr(alpha, delta, t) + 1e-9:
                        ok = False
                        break

                results[c_id][cname] = {
                    "alpha": alpha,
                    "delay": delta,
                    "schedulable": ok
                }

                core_servers.append({
                    "Q": Q, "P": P, "J": delta,
                    "priority": comp.get("priority"),
                    "name": cname,
                    "ok_inside": ok
                })

            # if any component already failed, skip core‑level test
            if not all(s["ok_inside"] for s in core_servers):
                continue
            
            # ------------ DEBUG dump: one line per core ------------
            print(f"[DBG] Core {c_id:>5}  sched={core_sched:3}  "
                  f"Σα = {sum(s['Q']/s['P'] for s in core_servers):4.3f}   "
                  f"servers = "
                  + ", ".join(f"{s['name']}[Q={s['Q']},P={s['P']},J={s['J']}]"
                              for s in core_servers))
            # --------------------------------------------------------

            # ---- 2) check set of servers on the core ----
            if core_sched == "EDF":
                periods = [int(s["P"]) for s in core_servers]
                H_core  = lcm(*periods)          # first hyper‑period of the servers
                for t in range(H_core + 1):
                    demand = sum(self.dbf_server(s["Q"], s["P"], s["J"], t)
                                 for s in core_servers)
                    if demand > t + 1e-9:
                        for s in core_servers:
                            results[c_id][s["name"]]["schedulable"] = False
                        break

            else:  # RM / FPS at core level
                hp_sorted = sorted(core_servers,
                                   key=lambda s: s["priority"])
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
                                results[c_id][ss["name"]]["schedulable"] = False
                            break
                        R = I + s["Q"]
                    else:
                        continue
                    break   # exit on first failure
        return results
