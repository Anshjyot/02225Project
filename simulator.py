# simulator.py
import math

class HierarchicalSimulator:
    def __init__(self, system_model):
        self.system_model = system_model
        self.comp_states = {}
        self.comp_params = {}

        for core in system_model["cores"]:
            core_id = core["core_id"]
            for comp in core["components"]:
                ckey = (core_id, comp["name"])
                self.comp_params[ckey] = {
                    "alpha": comp["bdr_init"]["alpha"],
                    "scheduler": comp["scheduler"]
                }

                tasks_state = []
                for tinfo in comp["tasks"]:
                    tasks_state.append({
                        "id": tinfo["id"],
                        "period": tinfo["period"],
                        "deadline": tinfo["deadline"],
                        "effective_wcet": tinfo["effective_wcet"],
                        "priority": tinfo.get("priority", None),
                        "scheduler": comp["scheduler"],
                        "type": tinfo.get("type", "hard"),
                        "component_id": tinfo.get("component_id", "Unknown"),

                        "next_release": 0.0,
                        "job": None,
                        "stats": {
                            "max_resp_time": 0.0,
                            "missed_deadlines": 0,
                            "resp_times": []
                        }
                    })
                self.comp_states[ckey] = tasks_state

    def run_simulation(self, simulation_time=200.0, dt=0.1):
        t = 0.0
        while t < simulation_time:
            for ckey, tasks in self.comp_states.items():
                for tsk in tasks:
                    if t >= tsk["next_release"]:
                        if tsk["job"] is not None:
                            tsk["stats"]["missed_deadlines"] += 1
                            tsk["job"] = None
                        tsk["job"] = {
                            "release": t,
                            "remaining": tsk["effective_wcet"],
                            "deadline": t + tsk["deadline"]
                        }
                        tsk["next_release"] = t + tsk["period"]

            for ckey, tasks in self.comp_states.items():
                alpha = self.comp_params[ckey]["alpha"]
                allocated = alpha * dt
                ready_tasks = [tsk for tsk in tasks if tsk["job"] is not None]
                if allocated <= 0 or not ready_tasks:
                    continue

                sched = self.comp_params[ckey]["scheduler"].upper()
                if sched == "EDF":
                    ready_tasks.sort(key=lambda x: x["job"]["deadline"])
                elif sched in ["FPS", "RM"]:
                    ready_tasks.sort(key=lambda x: x["priority"] if x["priority"] is not None else math.inf)

                remain = allocated
                for tsk in ready_tasks:
                    if remain <= 1e-9:
                        break
                    job = tsk["job"]
                    amount = min(remain, job["remaining"])
                    job["remaining"] -= amount
                    remain -= amount
                    if job["remaining"] <= 1e-9:
                        resp = (t + dt) - job["release"]
                        tsk["stats"]["max_resp_time"] = max(resp, tsk["stats"]["max_resp_time"])
                        tsk["stats"]["resp_times"].append(resp)
                        tsk["job"] = None

            for ckey, tasks in self.comp_states.items():
                for tsk in tasks:
                    job = tsk["job"]
                    if job is not None and t >= job["deadline"]:
                        tsk["stats"]["missed_deadlines"] += 1
                        tsk["job"] = None

            t += dt

        final_stats = {"task_stats": {}}
        for ckey, tasks in self.comp_states.items():
            for tsk in tasks:
                stats = tsk["stats"]
                rt_list = stats.get("resp_times", [])
                avg = sum(rt_list) / len(rt_list) if rt_list else 0.0
                is_sched = stats["missed_deadlines"] == 0
                final_stats["task_stats"][tsk["id"]] = {
                    "max_resp_time": stats["max_resp_time"],
                    "avg_response_time": avg,
                    "missed_deadlines": stats["missed_deadlines"],
                    "schedulable": is_sched,
                    "component_id": tsk["component_id"]
                }
        return final_stats
