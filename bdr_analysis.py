import math
from dbf_utils import dbf_edf, dbf_fps

class BDRAnalysis:
    def __init__(self, system_model):
        self.system_model = system_model

    def sbf_bdr(self, alpha, delta, t):
        # Equation (6) from the "Hierarchical Scheduling" chapter (Bounded Delay Resource).
        if t <= delta:
            return 0.0
        return alpha*(t - delta)

    def run_analysis(self):
        """
        For each core -> for each component:
          1) gather tasks
          2) pick dbf( ) based on scheduler
          3) define horizon = sum(periods) (a naive bound)
          4) check for all t from 0..horizon if dbf(W,t) <= sbf_bdr(alpha,delta,t)
          5) if it always holds, schedulable => True
        """
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


                sum_periods = sum(t["period"] for t in tasks)
                horizon = math.ceil(sum_periods)

                schedulable = True
                for tcheck in range(horizon + 1):
                    demand = dbf_func(tasks, tcheck)
                    supply = self.sbf_bdr(alpha, delta, tcheck)
                    if demand > supply + 1e-6:  # more slack
                        print(f"[DEBUG] ❌ Unschedulable at t={tcheck}: demand={demand:.2f} > supply={supply:.2f}")
                        schedulable = False
                        break

                results[c_id][cname] = {
                    "alpha": alpha,
                    "delay": delta,
                    "schedulable": schedulable
                }

        return results
