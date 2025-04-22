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
            # TODO: Very simple EDF estimate, could be improved with formal response time bound
            wcrt = D  # Assume worst-case deadline bound for now

        wcrt_stats[task_id] = round(wcrt, 2)

    return wcrt_stats
