import math

def dbf_edf(tasks, t):
    demand = 0.0
    for task in tasks:
        C, T, D = task["wcet"], task["period"], task["deadline"]
        if t >= D:
            n_jobs = math.floor((t - D) / T + 1)
            demand += max(0, n_jobs) * C
    return demand

def dbf_fps(tasks, t):
    return dbf_edf(tasks, t)
