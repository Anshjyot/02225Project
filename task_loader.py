import csv

def load_csv_files(tasks_csv, arch_csv, budgets_csv):
    """
    Reads tasks, architecture (cores), and budgets from CSV files.
    Builds a hierarchical system model for simulation and analysis.
    """

    # Step 1: Parse architecture.csv (core specs + top-level scheduler)
    cores_info = {}
    with open(arch_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["core_id"]
            speed = float(row["speed_factor"])
            scheduler = row["scheduler"].strip().upper()
            cores_info[cid] = {
                "core_id": cid,
                "speed_factor": speed,
                "scheduler": scheduler,  # Top-level scheduler for components
                "components": []
            }

    # Step 2: Parse budgets.csv (components and their mapping to cores)
    comp_info = {}
    with open(budgets_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            comp_id = row["component_id"]
            scheduler = row["scheduler"].strip().upper()
            alpha = float(row["budget"])
            delay = float(row["period"])
            parent_core = row["core_id"]
            priority = int(row["priority"]) if row.get("priority") else None

            if comp_id not in comp_info:
                comp_info[comp_id] = {
                    "name": comp_id,
                    "scheduler": scheduler,
                    "bdr_init": {"alpha": alpha, "delay": delay},
                    "tasks": [],
                    "parent_core": parent_core,
                    "priority": priority  # For RM-based core scheduling
                }

    # Step 3: Parse tasks.csv (tasks inside each component)
    with open(tasks_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_name = row["task_name"]
            wcet = float(row["wcet"])
            period = float(row["period"])
            component_id = row["component_id"]
            priority = int(row["priority"]) if row.get("priority") else None
            deadline = float(row["deadline"]) if row.get("deadline") else period
            ttype = row.get("type", "hard")

            if component_id not in comp_info:
                raise ValueError(f"Component {component_id} not found in budgets.csv!")

            # Auto-assign RM priority if needed
            scheduler = comp_info[component_id]["scheduler"]
            if priority is None and scheduler in ["FPS", "RM"]:
                print(f"⚠️ Warning: Task {task_name} in component {component_id} has no priority! Auto-assigning RM priority based on period.")
                priority = period

            comp_info[component_id]["tasks"].append({
                "id": task_name,
                "wcet": wcet,
                "period": period,
                "deadline": deadline,
                "priority": priority,
                "type": ttype,
            })

    # Debug: show tasks assigned per component
    print("=== Component Task Assignment ===")
    for comp_id, comp in comp_info.items():
        task_ids = [t["id"] for t in comp["tasks"]]
        print(f"Component {comp_id} (Scheduler: {comp['scheduler']}) on Core {comp['parent_core']} has tasks: {task_ids}")

    # Step 4: Build component-core hierarchy
    for cinfo in comp_info.values():
        core_id = cinfo["parent_core"]
        if core_id not in cores_info:
            raise ValueError(f"Core {core_id} from budgets.csv not found in architecture.csv!")

        cores_info[core_id]["components"].append({
            "name": cinfo["name"],
            "scheduler": cinfo["scheduler"],
            "bdr_init": cinfo["bdr_init"],
            "priority": cinfo["priority"],
            "tasks": cinfo["tasks"]
        })

    # Step 5: Construct the full system model
    system_model = {
        "cores": list(cores_info.values())
    }

    # Step 6: Adjust WCET based on core speed
    for core in system_model["cores"]:
        speed = core["speed_factor"]
        for comp in core["components"]:
            for task in comp["tasks"]:
                task["effective_wcet"] = task["wcet"] / speed
                task["wcet"] = task["effective_wcet"]

                # Step 7: Sort components by RM priority if needed
    for core in system_model["cores"]:
        if core["scheduler"] == "RM":
            core["components"].sort(key=lambda comp: comp.get("priority", float("inf")))

    return system_model
