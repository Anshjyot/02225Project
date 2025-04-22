import csv

def write_solution_csv(task_stats, analysis_results, filename="solution.csv"):
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "task_name", "component_id", "task_schedulable",
            "avg_response_time", "max_response_time", "component_schedulable"
        ])

        # Map of component -> list of task schedulabilities
        comp_sched_map = {}
        task_rows = []

        for tname, stats in task_stats.items():
            cid = stats.get("component_id", "?")
            avg_resp = f"{stats.get('avg_response_time', 0.0):.2f}"
            max_resp = f"{stats.get('max_resp_time', 0.0):.2f}"
            sched = stats.get("schedulable", True)
            sched_val = "TRUE" if sched else "FALSE"

            if cid not in comp_sched_map:
                comp_sched_map[cid] = []
            comp_sched_map[cid].append(sched)

            task_rows.append([tname, cid, sched_val, avg_resp, max_resp, None])

        comp_sched_final = {
            cid: all(scheds) for cid, scheds in comp_sched_map.items()
        }

        for row in task_rows:
            row[-1] = "TRUE" if comp_sched_final.get(row[1], True) else "FALSE"
            writer.writerow(row)




