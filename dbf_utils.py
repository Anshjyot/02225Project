import math

def dbf_edf(tasks, t):
    """
    DBF for a set of tasks scheduled by EDF:
       dbf(W,t) = sum of max(0, floor((t - D_i)/T_i + 1)* C_i).
    """
    demand = 0.0
    for task in tasks:
        C = task["effective_wcet"]
        T = task["period"]
        D = task["deadline"]
        if t >= D:
            nJobs = math.floor((t - D)/T + 1)
            if nJobs < 0:
                nJobs = 0
            demand += nJobs * C
    return demand

def dbf_fps(tasks, t):
    """
    Computes the total DBF under FPS with Rate Monotonic (RM) priority.
    For each task τ_i, we compute:
      dbf_i(t) = C_i + sum_{∀j ∈ hp(i)} ceil(t / T_j) * C_j
    """
    total_demand = 0.0

    for task_i in tasks:
        C_i = task_i["effective_wcet"]
        T_i = task_i["period"]
        prio_i = task_i["priority"]

        if prio_i is None:
            continue  # skip unprioritized tasks

        # Higher-priority tasks: smaller numeric value = higher priority
        hp_tasks = [t for t in tasks if t["priority"] is not None and t["priority"] < prio_i]

        interference = 0.0
        for hp in hp_tasks:
            interference += math.ceil(t / hp["period"]) * hp["effective_wcet"]

        if t >= task_i["deadline"]:
            total_demand += C_i + interference

    return total_demand
