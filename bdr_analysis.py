import math
from dbf_utils import dbf_edf, dbf_fps
from functools import reduce

class BDRAnalysis:
    def __init__(self, system_model):
        self.system_model = system_model

    def sbf_bdr(self, alpha, delta, t):
        if t <= delta:
            return 0.0
        return alpha * (t - delta)

    @staticmethod
    def lcm(a, b):
        return abs(a * b) // math.gcd(int(a), int(b))

    @staticmethod
    def lcm_of_periods(periods):
        return int(reduce(BDRAnalysis.lcm, periods))

    def run_analysis(self):
        results = {}
        for core in self.system_model["cores"]:
            c_id = core["core_id"]
            results[c_id] = {}
            for comp in core["components"]:
                cname = comp["name"]
                alpha = comp["bdr_init"]["alpha"]
                delta = comp["bdr_init"]["delay"]
                tasks = comp["tasks"]
                sched = comp["scheduler"].upper()

                if sched == "EDF":
                    dbf_func = dbf_edf
                else:
                    dbf_func = dbf_fps

                # Improved horizon logic
                periods = [t["period"] for t in tasks]
                deadlines = [t["deadline"] for t in tasks]
                lcm_periods = self.lcm_of_periods(periods)
                conservative_horizon = int(2 * max(deadlines))
                horizon = min(lcm_periods, conservative_horizon)

                schedulable = True
                for tcheck in range(horizon + 1):
                    demand = dbf_func(tasks, tcheck)
                    supply = self.sbf_bdr(alpha, delta, tcheck)
                    if demand > supply + 1e-9:
                        print(f"[DEBUG] ❌ Unschedulable: Component {cname} (Sched: {sched}) at t={tcheck}, "
                            f"demand={demand:.2f}, supply={supply:.2f}, tasks={[t['id'] for t in tasks]}")
                        schedulable = False
                        break


                results[c_id][cname] = {
                    "alpha": alpha,
                    "delay": delta,
                    "schedulable": schedulable
                }

        return results
