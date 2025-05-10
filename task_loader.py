import csv
import os

def load_comm_links(filepath):
    comm_map = {}
    if not os.path.exists(filepath):
        return comm_map
    with open(filepath, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dst = row["destination_task"]
            delay = float(row["delay"])
            # only track max delay per destination task
            comm_map[dst] = max(comm_map.get(dst, 0.0), delay)
    return comm_map

def load_csv_files(tasks_csv, arch_csv, budgets_csv, use_comm_links=False):
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
                "scheduler": scheduler,
                "components": []
            }

    # Step 2: Parse budgets.csv (components and their mapping to cores or parents)
    comp_info = {}
    children_map = {}
    with open(budgets_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            comp_id = row["component_id"]
            scheduler = row["scheduler"].strip().upper()
            Q_val = float(row["budget"])
            P_val = float(row["period"])
            parent_core = row.get("core_id")
            parent_comp = row.get("parent_component") or None
            priority = int(row["priority"]) if row.get("priority") else None

            comp_info[comp_id] = {
                "name": comp_id,
                "scheduler": scheduler,
                "bdr_init": {"Q": Q_val, "P": P_val},
                "tasks": [],
                "subcomponents": [],
                "parent_core": parent_core,
                "parent_component": parent_comp,
                "priority": priority
            }

            if parent_comp:
                children_map.setdefault(parent_comp, []).append(comp_id)

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

    # Link subcomponents
    for parent, children in children_map.items():
        for cid in children:
            comp_info[parent]["subcomponents"].append(comp_info[cid])

    print("=== Component Task Assignment ===")
    for comp_id, comp in comp_info.items():
        task_ids = [t["id"] for t in comp["tasks"]]
        print(f"Component {comp_id} (Scheduler: {comp['scheduler']}) has tasks: {task_ids}")

    # Step 4: Build component-core hierarchy
    for cinfo in comp_info.values():
        if not cinfo["parent_core"]:
            continue
        core_id = cinfo["parent_core"]
        if core_id not in cores_info:
            raise ValueError(f"Core {core_id} from budgets.csv not found in architecture.csv!")

        cores_info[core_id]["components"].append({
            "name": cinfo["name"],
            "scheduler": cinfo["scheduler"],
            "bdr_init": cinfo["bdr_init"],
            "priority": cinfo["priority"],
            "tasks": cinfo["tasks"],
            "subcomponents": cinfo["subcomponents"]
        })

    # Step 5: Construct the full system model
    system_model = {
        "cores": list(cores_info.values())
    }

    # Step 6: Adjust WCET based on core speed
    for core in system_model["cores"]:
        speed = core["speed_factor"]
        def adjust_wcet(tasks):
            for task in tasks:
                task["effective_wcet"] = task["wcet"] / speed
                task["wcet"] = task["effective_wcet"]

        def adjust_all(comp):
            adjust_wcet(comp["tasks"])
            for sub in comp.get("subcomponents", []):
                adjust_all(sub)

        for comp in core["components"]:
            adjust_all(comp)

    # Step 7: Sort components by RM priority if needed
    for core in system_model["cores"]:
        if core["scheduler"] == "RM":
            core["components"].sort(key=lambda comp: comp.get("priority", float("inf")))

    comm_map = {}
    if use_comm_links:
        comm_links_path = os.path.join(os.path.dirname(tasks_csv), "comm_links.csv")
        comm_map = load_comm_links(comm_links_path)

    for core in system_model["cores"]:
        for comp in core["components"]:
            for task in comp["tasks"]:
                task["comm_jitter"] = comm_map.get(task["id"], 0.0)

    if comm_map:
        print(f"📡 Loaded communication delays for {len(comm_map)} tasks from comm_links.csv")

    return system_model
