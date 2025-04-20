import math
import sched

def dbf_edf(tasks, t):
    """
    DBF for a set of tasks scheduled by EDF:
      dbf(W, t) = sum over tasks of max(0, floor((t - D_i)/T_i + 1) * C_i).
    This function is used for components with EDF scheduling.
    """
    demand = 0.0
    for task in tasks:
        C = task["wcet"]
        T = task["period"]
        D = task["deadline"]
        if t >= D:
            nJobs = math.floor((t - D) / T + 1)
            if nJobs < 0:
                nJobs = 0
            demand += nJobs * C
    return demand

def dbf_fps(tasks, t):
    """
    Priority-aware DBF for tasks scheduled by FPS (with RM priority assignment).
    
    Note:
      - This function is only used for components whose scheduler is RM (or FPS).
      - For RM scheduling, tasks must have priorities. If a task is missing a priority,
        it should be auto-assigned based on its period (lower period -> higher priority).
      - The function sorts tasks in order of increasing 'priority' (or period if missing),
        then accumulates the demand level-by-level.
    """
    # Sort tasks by their priority; if a task has no priority, use its period as a fallback.
    tasks = sorted(tasks, key=lambda x: x["priority"] if x["priority"] is not None else x["period"])
    
    demand = 0.0
    for task in tasks:
        C = task["wcet"]
        T = task["period"]
        D = task["deadline"]
        if t >= D:
            nJobs = math.floor((t - D) / T + 1)
            if nJobs < 0:
                nJobs = 0
            demand += nJobs * C
        
        # If at any point the accumulated demand exceeds t,
        # the lower-priority tasks cannot be feasibly scheduled.
        if demand > t:
            break
    return demand

