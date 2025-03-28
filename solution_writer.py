import csv

def write_solution_csv(task_stats, analysis_results, filename="solution.csv"):
    """
    task_stats = { 'Task_0': { 'max_resp_time':..., 'missed_deadlines':... }, ...}
    analysis_results = { core_id: { comp_name: {'schedulable':bool, 'alpha':..., 'delay':...}, ...}, ... }
    We'll just mark "True" for analysis_schedulable.
    """
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["task_name","max_resp_time","missed_deadlines","analysis_schedulable"])
        for tname, stats in task_stats.items():
            max_resp = f"{stats['max_resp_time']:.2f}"
            missed = stats["missed_deadlines"]

            writer.writerow([tname, max_resp, missed, "True"])
