class BDRAnalysis:
    def __init__(self, system_model):
        self.system_model = system_model

    def run_analysis(self):
        results = {}
        for core in self.system_model["cores"]:
            core_id = core["core_id"]
            results[core_id] = {}
            for comp in core["components"]:
                alpha = comp["bdr_init"]["alpha"]
                utilization = 0.0
                for task in comp["tasks"]:
                    utilization += task["effective_wcet"] / task["period"]
                results[core_id][comp["name"]] = {
                    "utilization": utilization,
                    "alpha": alpha,
                    "schedulable": utilization <= alpha
                }
        return results
