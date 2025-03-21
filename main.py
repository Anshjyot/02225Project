import sys
from task_loader import load_system_model
from simulator import HierarchicalSimulator
from analysis import BDRAnalysis

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <config_file.json>")
        sys.exit(1)

    config_file = sys.argv[1]
    system_model = load_system_model(config_file)

    # Run simulation
    simulator = HierarchicalSimulator(system_model)
    sim_results = simulator.run_simulation(simulation_time=200, dt=0.1)
    print("\n=== SIMULATION RESULTS ===")
    for task_id, stats in sim_results["task_stats"].items():
        print(f"Task {task_id} -> max_resp_time = {stats['max_resp_time']:.2f}, missed_deadlines = {stats['missed_deadlines']}")

    # Run analysis
    analysis_tool = BDRAnalysis(system_model)
    analysis_results = analysis_tool.run_analysis()
    print("\n=== ANALYSIS RESULTS ===")
    for core_id, comp_res in analysis_results.items():
        print(f"[Core {core_id} Analysis]:")
        for comp_name, res in comp_res.items():
            status = "Schedulable" if res["schedulable"] else "Unschedulable"
            print(f"  Component {comp_name}: {status} (utilization: {res['utilization']:.2f}, alpha: {res['alpha']:.2f})")

    print("\n--- COMPARISON OF SIMULATION VS. ANALYSIS COMPLETE ---")

if __name__ == "__main__":
    main()
