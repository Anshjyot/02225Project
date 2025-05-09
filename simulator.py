import math
from typing import Dict, List, Tuple, Any


class HierarchicalSimulator:
    """Hierarchical real‑time simulator enforcing per-core BDR interfaces with optional reclaiming."""
    def __init__(self, system_model: Dict[str, Any]):
        self.system_model = system_model
        self.task_states: Dict[Tuple[str,str], List[Dict[str,Any]]] = {}
        self.servers: Dict[Tuple[str,str], Dict[str,Any]] = {}
        self.build_state()

    def build_state(self):
        for core in self.system_model["cores"]:
            cid = core["core_id"]
            for comp in core["components"]:
                self._init_component(cid, comp, core["speed_factor"])

    def _init_component(self, cid, comp, speed):
        ckey = (cid, comp["name"])
        Q = float(comp["bdr_init"]["alpha"])
        P = float(comp["bdr_init"]["delay"])
        α = Q / P
        Δ = 2 * (P - Q)
        self.servers[ckey] = {"Q":Q, "P":P, "alpha":α, "delta":Δ,
                              "next_period_start":Δ, "budget_remaining":0.0,
                              "scheduler":comp["scheduler"].upper()}
        ts = []
        for tinfo in comp.get("tasks", []):
            ts.append({"id":tinfo["id"],"period":tinfo["period"],
                       "deadline":tinfo["deadline"],"effective_wcet":tinfo["effective_wcet"],
                       "priority":tinfo.get("priority"),"type":tinfo.get("type","hard"),
                       "next_release":0.0,"job":None,
                       "stats":{
                                "max_resp_time": 0.0,
                                "missed_deadlines": 0,
                                "total_resp_time": 0.0,
                                "num_completed_jobs": 0
                            }})
        self.task_states[ckey] = ts

        for sub in comp.get("subcomponents", []):
            self._init_component(cid, sub, speed)

    def run_simulation(self, simulation_time: float, dt: float = 0.1):
        t = 0.0
        while t < simulation_time - 1e-9:
            self._release_jobs(t)
            self._replenish_budgets(t)
            self._schedule_jobs(t, dt)
            self._check_deadlines(t)
            t += dt
        return self._collect_results()

    def _release_jobs(self, t):
        for tasks in self.task_states.values():
            for tsk in tasks:
                if t + 1e-9 >= tsk["next_release"]:
                    if tsk["job"] is not None:
                        job = tsk["job"]
                        resp = t - job["release"]
                        tsk["stats"]["max_resp_time"] = max(tsk["stats"]["max_resp_time"], resp)
                        tsk["stats"]["missed_deadlines"] += 1
                    tsk["job"] = {"release":t,"remaining":tsk["effective_wcet"],
                                  "deadline":t + tsk["deadline"]}
                    tsk["next_release"] += tsk["period"]

    def _replenish_budgets(self, t):
        for server in self.servers.values():
            if t + 1e-9 >= server["delta"]:
                while t + 1e-9 >= server["next_period_start"]:
                    server["budget_remaining"] = server["Q"]
                    server["next_period_start"] += server["P"]

    def _schedule_jobs(self, t, dt):
        for core in self.system_model["cores"]:
            cid = core["core_id"]
            active = []
            total_alpha = 0.0
            for comp in core["components"]:
                self._gather_active_components(cid, comp, t, active, total_alpha)

            if not active:
                continue

            total_alpha = sum(srv["alpha"] for _, srv, _ in active)
            scale = 1.0 / total_alpha if total_alpha > 1.0 + 1e-12 else 1.0

            for ckey, srv, ts in active:
                share = srv["alpha"] * scale * dt
                quantum = min(share, srv["budget_remaining"])
                if quantum <= 1e-12:
                    continue
                jobs = [x for x in ts if x["job"] is not None]
                if srv["scheduler"] == "EDF":
                    jobs.sort(key=lambda x: x["job"]["deadline"])
                else:
                    jobs.sort(key=lambda x: x.get("priority", float("inf")))
                rem = quantum
                for j in jobs:
                    if rem <= 1e-12:
                        break
                    slice_amt = min(rem, j["job"]["remaining"])
                    j["job"]["remaining"] -= slice_amt
                    rem -= slice_amt
                    srv["budget_remaining"] -= slice_amt
                    if j["job"]["remaining"] <= 1e-12:
                        resp = (t + dt) - j["job"]["release"]
                        j["stats"]["max_resp_time"] = max(j["stats"]["max_resp_time"], resp)
                        j["stats"]["total_resp_time"] += resp
                        j["stats"]["num_completed_jobs"] += 1
                        j["job"] = None

    def _gather_active_components(self, cid, comp, t, active, total_alpha):
        ckey = (cid, comp["name"])
        srv = self.servers[ckey]
        ts = self.task_states[ckey]
        has_job = any(x["job"] is not None for x in ts)
        if has_job and srv["budget_remaining"] > 1e-9 and t + 1e-9 >= srv["delta"]:
            active.append((ckey, srv, ts))
            total_alpha += srv["alpha"]
        for sub in comp.get("subcomponents", []):
            self._gather_active_components(cid, sub, t, active, total_alpha)

    def _check_deadlines(self, t):
        for ts in self.task_states.values():
            for j in ts:
                if j["job"] is not None and t + 1e-9 >= j["job"]["deadline"]:
                    j["stats"]["missed_deadlines"] += 1
                    resp = t - j["job"]["release"]
                    j["stats"]["max_resp_time"] = max(j["stats"]["max_resp_time"], resp)
                    j["job"] = None

    def _collect_results(self):
        out = {"task_stats":{}}
        for ts in self.task_states.values():
            for j in ts:
                out["task_stats"][j["id"]] = j["stats"]
        return out
