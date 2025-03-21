import json

def load_system_model(config_file):
    with open(config_file, 'r') as f:
        data = json.load(f)
    for core in data.get("cores", []):
        speed = core.get("speed_factor", 1.0)
        for comp in core.get("components", []):
            for task in comp.get("tasks", []):
                original_wcet = task["wcet"]
                task["effective_wcet"] = original_wcet / speed
    return data
