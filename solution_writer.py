import csv

def write_solution_csv(task_stats, analysis_results, task_to_comp, filename="solution.csv"):
    """
    Writes a CSV file with detailed simulation + analysis results.

    Columns:
    task_name, component_id, task_schedulable, avg_response_time,
    max_response_time, wcrt, violates_deadline, component_schedulable
    """
    # Build component-level schedulability map from analysis
    comp_schedulable = {}
    wcrt_lookup = {}
    for core in analysis_results:
        for comp, data in analysis_results[core].items():
            comp_schedulable[(core, comp)] = data["bdr"]["schedulable"]  # or "prm", if preferred
            for tid, wcrt in data["bdr"]["wcrt"].items():  # or data["prm"]["wcrt"] if you prefer that
                wcrt_lookup[tid] = wcrt

    # Accumulate all tasks grouped by component to compute per-component schedulability (simulator-based)
    comp_task_ids = {}
    for task_id, (core_id, comp_id) in task_to_comp.items():
        key = (core_id, comp_id)
        comp_task_ids.setdefault(key, []).append(task_id)

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "task_name",
            "component_id",
            "task_schedulable",
            "avg_response_time",
            "max_response_time",
            "wcrt",
            "violates_deadline",
            "component_schedulable"
        ])
        for task_id, stats in task_stats.items():
            core_id, comp_id = task_to_comp[task_id]
            avg_resp = (
                stats["total_resp_time"] / stats["num_completed_jobs"]
                if stats["num_completed_jobs"] > 0 else 0.0
            )
            task_sched = 1 if stats["missed_deadlines"] == 0 else 0
            key = (core_id, comp_id)
            all_comp_tasks = comp_task_ids.get(key, [])
            comp_sched_sim = all(
                task_stats[tid]["missed_deadlines"] == 0 for tid in all_comp_tasks
            )
            wcrt = wcrt_lookup.get(task_id, -1)
            violates = 1 if wcrt > stats.get("deadline", float("inf")) else 0
            writer.writerow([
                task_id,
                comp_id,
                task_sched,
                f"{avg_resp:.2f}",
                f"{stats['max_resp_time']:.2f}",
                f"{wcrt:.2f}",
                violates,
                1 if comp_sched_sim else 0
            ])
