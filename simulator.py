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
                    "delay": comp["bdr_init"]["delay"],
                    "scheduler": comp["scheduler"].upper()
                }

                tasks_state = []
                for tinfo in comp["tasks"]:
                    tasks_state.append({
                        "id": tinfo["id"],
                        "period": tinfo["period"],
                        "deadline": tinfo["deadline"],
                        "effective_wcet": tinfo["effective_wcet"],
                        "priority": tinfo.get("priority", None),
                        "type": tinfo.get("type", "hard"),

                        "next_release": 0.0,
                        "job": None,
                        "stats": {
                            "max_resp_time": 0.0,
                            "missed_deadlines": 0
                        }
                    })
                self.comp_states[ckey] = tasks_state

    def run_simulation(self, simulation_time, dt):
        t = 0.0
        while t < simulation_time:
            # 1. Job release phase
            for ckey, tasks in self.comp_states.items():
                for tsk in tasks:
                    if t >= tsk["next_release"]:
                        if tsk["job"] is not None:
                            job = tsk["job"]
                            rtime = t - job["release"]
                            tsk["stats"]["max_resp_time"] = max(tsk["stats"]["max_resp_time"], rtime)
                            tsk["stats"]["missed_deadlines"] += 1
                            ##print(f"[DEBUG] ❌ Missed job release for task {tsk['id']} at time {t:.2f} "
                             ##   f"(release: {job['release']:.2f}, deadline: {job['deadline']:.2f}, remaining: {job['remaining']:.2f})")
                            tsk["job"] = None
                        tsk["job"] = {
                            "release": t,
                            "remaining": tsk["effective_wcet"],
                            "deadline": t + tsk["deadline"]
                        }
                        tsk["next_release"] = t + tsk["period"]

            # 2. Core-level: Fair component CPU allocation based on alpha/delay
            for core in self.system_model["cores"]:
                core_id = core["core_id"]

                runnable_components = []
                for comp in core["components"]:
                    ckey = (core_id, comp["name"])
                    tasks = self.comp_states[ckey]
                    if any(t["job"] is not None for t in tasks):
                        runnable_components.append((comp, ckey, tasks))

                if not runnable_components:
                    continue

                total_alloc = 0.0
                comp_allocations = []
                for comp, ckey, tasks in runnable_components:
                    alpha = comp["bdr_init"]["alpha"]
                    delay = comp["bdr_init"]["delay"]
                    alloc = (alpha / delay) * dt
                    total_alloc += alloc
                    comp_allocations.append((alloc, comp, ckey, tasks))

                # Normalize if total_alloc > dt (shouldn't normally happen)
                if total_alloc > dt:
                    factor = dt / total_alloc
                    comp_allocations = [(alloc * factor, comp, ckey, tasks) for alloc, comp, ckey, tasks in comp_allocations]

                for alloc, comp, ckey, tasks in comp_allocations:
                    sched = comp["scheduler"].upper()
                    ready_tasks = [t for t in tasks if t["job"] is not None]
                    if not ready_tasks or alloc <= 0:
                        continue

                    if sched == "EDF":
                        ready_tasks.sort(key=lambda x: x["job"]["deadline"])
                    elif sched in ["RM", "FPS"]:
                        ready_tasks.sort(key=lambda x: x["priority"] if x["priority"] is not None else float("inf"))

                    remaining = alloc
                    for tsk in ready_tasks:
                        if remaining <= 1e-9:
                            break
                        job = tsk["job"]
                        amount = min(remaining, job["remaining"])
                        job["remaining"] -= amount
                        remaining -= amount
                        if job["remaining"] <= 1e-9:
                            rtime = (t + dt) - job["release"]
                            #print(f"[DEBUG] ✅ Task {tsk['id']} completed at t={t+dt:.2f}, response time: {rtime:.2f}")
                            tsk["stats"]["max_resp_time"] = max(tsk["stats"]["max_resp_time"], rtime)
                            tsk["job"] = None

            # 3. Deadline checks
            for ckey, tasks in self.comp_states.items():
                for tsk in tasks:
                    job = tsk["job"]
                    if job is not None and t >= job["deadline"]:
                        tsk["stats"]["missed_deadlines"] += 1
                        rtime = t - job["release"]
                        tsk["stats"]["max_resp_time"] = max(tsk["stats"]["max_resp_time"], rtime)
                        print(f"[DEBUG] ❌ Deadline MISS for {tsk['id']} at time {t:.2f} "
                            f"(release: {job['release']:.2f}, deadline: {job['deadline']:.2f}, response time: {rtime:.2f})")

                        tsk["job"] = None

            t += dt

        # 4. Final statistics
        final_stats = {"task_stats": {}}
        for ckey, tasks in self.comp_states.items():
            for tsk in tasks:
                final_stats["task_stats"][tsk["id"]] = tsk["stats"]
        return final_stats
