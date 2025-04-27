
import csv

def load_csv_files(tasks_csv, arch_csv, budgets_csv):
    cores_info = {}
    with open(arch_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["core_id"]
            speed = float(row["speed_factor"])
            sched = row["scheduler"]
            cores_info[cid] = {
                "core_id": cid,
                "speed_factor": speed,
                "scheduler": sched,
                "components": []
            }

    comp_info = {}
    with open(budgets_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            comp_id = row["component_id"]
            scheduler = row["scheduler"]
            alpha = float(row["budget"])
            delay = float(row["period"])
            core_id = row["core_id"]

            comp_info[comp_id] = {
                "name": comp_id,
                "scheduler": scheduler,
                "bdr_init": {
                    "alpha": alpha,
                    "delay": delay
                },
                "tasks": [],
                "parent_core": core_id
            }

    with open(tasks_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tname = row["task_name"]
            wcet = float(row["wcet"])
            period = float(row["period"])
            cid = row["component_id"]
            prio = int(row["priority"]) if row.get("priority") else None

            task = {
                "id": tname,
                "wcet": wcet,
                "period": period,
                "deadline": period,
                "priority": prio,
                "type": "hard",  # default
                "scheduler": comp_info[cid]["scheduler"],
                "component_id": cid
            }
            comp_info[cid]["tasks"].append(task)

    for comp in comp_info.values():
        core_id = comp.pop("parent_core")
        cores_info[core_id]["components"].append(comp)

    model = {"cores": list(cores_info.values())}

    for core in model["cores"]:
        sf = core["speed_factor"]
        for comp in core["components"]:
            for task in comp["tasks"]:
                task["effective_wcet"] = task["wcet"] / sf

    return model
