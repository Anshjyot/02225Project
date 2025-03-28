import csv

def load_csv_files(tasks_csv, arch_csv, budgets_csv):
    """
    Reads tasks, architecture (cores), budgets from CSV,
    returns a system_model dict with structure:
      {
         "cores": [
            {
              "core_id": "Core_1",
              "speed_factor": 1.0,
              "components": [
                {
                  "name": "CompA",
                  "scheduler": "EDF" or "FPS",
                  "bdr_init": { "alpha": float, "delay": float },
                  "tasks": [
                    { "id": "Task1", "wcet": 3.0, "period": 20.0, "deadline": 20.0, ...},
                    ...
                  ]
                }, ...
              ]
            }, ...
         ]
      }
    """


    cores_info = {}
    with open(arch_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["core_id"]
            speed = float(row["speed_factor"])
            cores_info[cid] = {
                "core_id": cid,
                "speed_factor": speed,
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
            parent_core = row["core_id"]

            comp_info[comp_id] = {
                "name": comp_id,
                "scheduler": scheduler,
                "bdr_init": {
                    "alpha": alpha,
                    "delay": delay
                },
                "tasks": [],
                "parent_core": parent_core
            }


    with open(tasks_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_name = row["task_name"]
            wcet = float(row["wcet"])
            period = float(row["period"])
            component_id = row["component_id"]
            sched = row["scheduler"]

            priority = None
            if row.get("priority", ""):
                priority = int(row["priority"])

            deadline = row.get("deadline", "")
            if deadline:
                deadline = float(deadline)
            else:
                deadline = period
            ttype = row.get("type", "hard")

            if component_id not in comp_info:
                raise ValueError(f"Component {component_id} not found in budgets file!")
            comp_info[component_id]["tasks"].append({
                "id": task_name,
                "wcet": wcet,
                "period": period,
                "deadline": deadline,
                "priority": priority,
                "type": ttype,
                "scheduler": sched,
            })


    for cinfo in comp_info.values():
        the_core_id = cinfo["parent_core"]
        if the_core_id not in cores_info:
            raise ValueError(f"Core {the_core_id} not in architecture.csv!")
        cores_info[the_core_id]["components"].append({
            "name": cinfo["name"],
            "scheduler": cinfo["scheduler"],
            "bdr_init": cinfo["bdr_init"],
            "tasks": cinfo["tasks"]
        })


    system_model = {
        "cores": list(cores_info.values())
    }


    for core in system_model["cores"]:
        speed = core["speed_factor"]
        for comp in core["components"]:
            for task in comp["tasks"]:
                orig = task["wcet"]
                task["effective_wcet"] = orig / speed

    return system_model
