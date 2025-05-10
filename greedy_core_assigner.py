from typing import Dict, Any


def assign_components_to_cores(system_model: Dict[str, Any]) -> Dict[str, str]:
    """
    Assigns components to cores using a greedy heuristic based on BDR alpha and core speed.
    Updates system_model in-place by modifying component['parent_core'].

    Returns:
        Dict mapping component names to assigned core IDs (for logging/debugging).
    """
    components = []
    core_speeds = {}
    for core in system_model["cores"]:
        core_id = core["core_id"]
        core_speeds[core_id] = core["speed_factor"]
        for comp in core["components"]:
            alpha = comp["bdr_init"]["Q"] / comp["bdr_init"]["P"]
            components.append({
                "name": comp["name"],
                "alpha": alpha,
                "original": comp
            })

    core_loads = {core_id: 0.0 for core_id in core_speeds}
    assignments = {}

    # Sort components by descending alpha
    components.sort(key=lambda c: -c["alpha"])

    for comp in components:
        best_core = None
        min_load = float("inf")
        for core_id, speed in core_speeds.items():
            eff_alpha = comp["alpha"] / speed
            if core_loads[core_id] + eff_alpha <= 1.0 + 1e-9:
                if core_loads[core_id] + eff_alpha < min_load:
                    best_core = core_id
                    min_load = core_loads[core_id] + eff_alpha

        if best_core is None:
            best_core = min(core_loads, key=core_loads.get)

        core_loads[best_core] += comp["alpha"] / core_speeds[best_core]
        assignments[comp["name"]] = best_core
        comp["original"]["parent_core"] = best_core

    return assignments
