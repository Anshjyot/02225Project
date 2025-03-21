import math

class HierarchicalSimulator:
    def __init__(self, system_model):
        self.system_model = system_model
        self.component_states = {}
        for core in self.system_model["cores"]:
            core_id = core["core_id"]
            for comp in core["components"]:
                key = (core_id, comp["name"])
                self.component_states[key] = []
                for task in comp["tasks"]:
                    task_state = {
                        "id": task["id"],
                        "period": task["period"],
                        "deadline": task["deadline"],
                        "effective_wcet": task["effective_wcet"],
                        "next_release": 0.0,
                        "job": None,
                        "scheduler": comp["scheduler"],
                        "priority": task.get("priority", None),
                        "stats": {
                            "max_resp_time": 0.0,
                            "missed_deadlines": 0
                        }
                    }
                    self.component_states[key].append(task_state)
        self.component_params = {}
        for core in self.system_model["cores"]:
            core_id = core["core_id"]
            for comp in core["components"]:
                key = (core_id, comp["name"])
                self.component_params[key] = {
                    "alpha": comp["bdr_init"]["alpha"],
                    "scheduler": comp["scheduler"]
                }

    def run_simulation(self, simulation_time=200, dt=0.1):
        t = 0.0
        while t < simulation_time:
            for comp_key, tasks in self.component_states.items():
                for task in tasks:
                    if t >= task["next_release"]:
                        if task["job"] is not None:
                            task["stats"]["missed_deadlines"] += 1
                            task["job"] = None
                        task["job"] = {
                            "release": t,
                            "remaining": task["effective_wcet"],
                            "deadline": t + task["deadline"]
                        }
                        task["next_release"] = t + task["period"]


            for comp_key, tasks in self.component_states.items():
                alpha = self.component_params[comp_key]["alpha"]
                allocated = alpha * dt
                ready_tasks = [task for task in tasks if task["job"] is not None]
                if not ready_tasks or allocated <= 0:
                    continue
                scheduler = self.component_params[comp_key]["scheduler"]
                if scheduler.upper() == "FPS":
                    ready_tasks.sort(key=lambda x: x["priority"] if x["priority"] is not None else math.inf)
                elif scheduler.upper() == "EDF":
                    ready_tasks.sort(key=lambda x: x["job"]["deadline"])
                else:
                    pass

                remaining_alloc = allocated
                for task in ready_tasks:
                    if remaining_alloc <= 0:
                        break
                    job = task["job"]
                    work = min(remaining_alloc, job["remaining"])
                    job["remaining"] -= work
                    remaining_alloc -= work
                    if job["remaining"] <= 1e-6:
                        resp_time = t + dt - job["release"]
                        if resp_time > task["stats"]["max_resp_time"]:
                            task["stats"]["max_resp_time"] = resp_time
                        task["job"] = None  # job completed
                for task in tasks:
                    job = task["job"]
                    if job is not None and t >= job["deadline"]:
                        task["stats"]["missed_deadlines"] += 1

                        task["job"] = None

            t += dt

        results = {"task_stats": {}}
        for comp_key, tasks in self.component_states.items():
            for task in tasks:
                results["task_stats"][task["id"]] = task["stats"]
        return results
