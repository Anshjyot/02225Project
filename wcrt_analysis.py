import math

def estimate_wcrt(tasks):
    wcrt_stats = {}
    for task in tasks:
        C = task["effective_wcet"]
        T = task["period"]
        D = task["deadline"]
        task_id = task["id"]
        wcrt = C

        if task.get("scheduler", "EDF").upper() == "RM":
            hp_tasks = [t for t in tasks if t["priority"] is not None and t["priority"] < task["priority"]]

            R_prev = C
            for _ in range(100):
                interference = sum(
                    math.ceil(R_prev / t["period"]) * t["effective_wcet"] for t in hp_tasks
                )
                R_next = C + interference
                if abs(R_next - R_prev) < 1e-3:
                    break
                R_prev = R_next
            wcrt = R_next

        elif task.get("scheduler", "EDF").upper() == "EDF":
            # Formal WCRT computation for EDF (Baruah's bound)
            D_i = task["deadline"]
            C_i = task["effective_wcet"]

            # Consider only tasks with deadline <= D_i (interfering)
            interfering_tasks = [
                t for t in tasks if t["deadline"] <= D_i
            ]

            t_val = C_i
            while t_val <= D_i * 2:  # Reasonable upper bound
                total_demand = sum(
                    math.ceil(t_val / t["period"]) * t["effective_wcet"]
                    for t in interfering_tasks
                )
                if total_demand <= t_val:
                    break
                t_val += 0.1  # step size for convergence (fine-grained)
            wcrt = round(t_val, 2)

        wcrt_stats[task_id] = round(wcrt, 2)

    return wcrt_stats
