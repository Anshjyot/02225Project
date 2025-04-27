# bdr_auto_generator.py
import math
from dbf_utils import dbf_edf, dbf_fps

def compute_optimal_bdr(tasks, scheduler, horizon=None):
    """
    Improved BDR calculation: find minimal alpha with fixed reasonable delta.
    """

    dbf_func = dbf_edf if scheduler.upper() == "EDF" else dbf_fps

    periods = [t["period"] for t in tasks]
    if not periods:
        return 1.0, 0.1  # fallback safe for empty task sets

    if horizon is None:
        horizon = math.ceil(sum(periods))


    delta = min(0.4 * min(periods), 50.0)
    if delta < 0.1:
        delta = 0.1

    # Step 2: Find minimum alpha
    alpha_low = 0.0
    alpha_high = 1.0
    feasible_alpha = None

    while alpha_high - alpha_low > 1e-5:
        alpha_mid = (alpha_low + alpha_high) / 2
        feasible = True
        for t in range(1, horizon + 1):
            dbf = dbf_func(tasks, t)
            sbf = alpha_mid * max(0.0, t - delta)
            if dbf > sbf + 1e-6:
                feasible = False
                break

        if feasible:
            feasible_alpha = alpha_mid
            alpha_high = alpha_mid
        else:
            alpha_low = alpha_mid

    if feasible_alpha is None:
        print("❌ Failed to compute feasible (alpha, delta) for component")
        return 1.0, 0.1  # fallback safe

    best_alpha = round(feasible_alpha, 3)
    best_delta = round(delta, 2)
    print(f"✅ BDR Interface Found: alpha={best_alpha:.3f}, delta={best_delta:.2f}")
    return best_alpha, best_delta
