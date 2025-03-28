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
    Simple hierarchical approach, we sum demands of all tasks
    ignoring priority-level separation.
    A more advanced formula would do a priority-by-priority analysis.
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
            demand += nJobs*C
    return demand
