from dbf_utils import dbf_edf, dbf_fps
import math

def compute_optimal_bdr(tasks, scheduler, horizon=None, step=0.1):
    if scheduler.upper() == "EDF":
        dbf_func = dbf_edf
    else:
        dbf_func = dbf_fps

    all_periods = [t["period"] for t in tasks]
    if not horizon:
        horizon = math.ceil(sum(all_periods))

    best_alpha = 1.0
    best_delta = 0.0

    for delta in [i * step for i in range(int(horizon / step) + 1)]:
        alpha_low = 0.0
        alpha_high = 1.0
        feasible_alpha = None

        while alpha_high - alpha_low > 1e-4:
            alpha_mid = (alpha_low + alpha_high) / 2.0
            feasible = True

            for t in range(1, int(horizon) + 1):
                dbf = dbf_func(tasks, t)
                sbf = alpha_mid * max(0.0, t - delta)
                if dbf > sbf + 1e-9:
                    feasible = False
                    break

            if feasible:
                feasible_alpha = alpha_mid
                alpha_high = alpha_mid
            else:
                alpha_low = alpha_mid

        if feasible_alpha is not None and feasible_alpha < best_alpha:
            best_alpha = feasible_alpha
            best_delta = delta

    return best_alpha, best_delta