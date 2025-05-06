import math

def tune_prm_from_bdr(alpha, tasks, scheduler, horizon=None, granularity=0.1):
    """
    Given BDR (alpha, delta) and a task set, compute a conservative PRM interface (C, T)
    such that the PRM supply S(t) = floor(t/T) * C >= BDR_SBF(t) for all t in [0, horizon]
    """

    # Extract delta from alpha using EDF or RM approximation
    periods = [t["period"] for t in tasks]
    delta = min(periods) / 2  # for example, half the shortest period
    if horizon is None:
        horizon = 2 * max(periods)

    best_C, best_T = 0.0, 0.0
    min_error = float("inf")

    T_values = [round(i * granularity, 6) for i in range(1, int(float(horizon) / granularity))]

    for T in T_values:
        if T <= 0:
            continue
        C = 0.0
        for step in range(int(float(horizon) / granularity)):
            t = round(step * granularity, 6)
            sbf_bdr = max(0, alpha * (t - delta))
            supply = math.floor(t / T) * C
            if supply < sbf_bdr - 1e-6:
                needed = (sbf_bdr / max(1, math.floor(t / T))) if math.floor(t / T) > 0 else 0
                C = max(C, needed)

        # Re-validate with final C
        valid = True
        for step in range(int(float(horizon) / granularity)):
            t = round(step * granularity, 6)
            sbf_bdr = max(0, alpha * (t - delta))
            supply = math.floor(t / T) * C
            if supply < sbf_bdr - 1e-6:
                valid = False
                break

        if valid:
            error = C * (horizon / T) - alpha * (horizon - delta)
            if error < min_error:
                best_C, best_T = C, T
                min_error = error

    return alpha, delta, best_C, best_T
