import math
from typing import List, Dict

def compute_wcrt_rm(tasks: List[Dict], delta: float) -> Dict[str, float]:
    results = {}
    sorted_tasks = sorted(tasks, key=lambda x: x["priority"])
    for i, task in enumerate(sorted_tasks):
        Ci = task["wcet"]
        Di = task["deadline"]
        J = task.get("comm_jitter", 0.0)
        Ri = Ci + delta + J
        while True:
            interference = sum(
                math.ceil(Ri / hp["period"]) * hp["wcet"]
                for hp in sorted_tasks[:i]
            )
            R_next = Ci + delta + J + interference
            if abs(R_next - Ri) < 1e-6:
                break
            if R_next > Di:
                R_next = float("inf")
                break
            Ri = R_next
        results[task["id"]] = R_next
    return results

def dbf_edf(tasks: List[Dict], t: float) -> float:
    demand = 0.0
    for task in tasks:
        C, T, D = task["wcet"], task["period"], task["deadline"]
        if t >= D:
            n_jobs = math.floor((t - D) / T + 1)
            demand += max(0, n_jobs) * C
    return demand

def compute_wcrt_edf(tasks: List[Dict], alpha: float, delta: float) -> Dict[str, float]:
    results = {}
    sorted_tasks = sorted(tasks, key=lambda x: x["deadline"])
    for i, task in enumerate(sorted_tasks):
        Di = task["deadline"]
        J = task.get("comm_jitter", 0.0)
        max_t = max(t["deadline"] for t in sorted_tasks[:i + 1]) * 2
        R = float("inf")
        for t in range(int(Di + J), int(max_t) + 1):
            demand = dbf_edf(sorted_tasks[:i + 1], t - J)
            supply = max(0.0, alpha * (t - delta))
            if demand <= supply + 1e-9:
                R = t
                break
        results[task["id"]] = R
    return results

def compute_wcrt(tasks: List[Dict], scheduler: str, alpha: float, delta: float) -> Dict[str, float]:
    sched = scheduler.upper()
    if sched in {"FPS", "RM"}:
        return compute_wcrt_rm(tasks, delta)
    elif sched == "EDF":
        return compute_wcrt_edf(tasks, alpha, delta)

    else:
        raise ValueError(f"Unknown scheduler: {scheduler}")
