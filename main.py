import os
from task_loader import load_csv_files
from simulator import HierarchicalSimulator
from bdr_analysis import BDRAnalysis
from solution_writer import write_solution_csv

def main():
    ################################################################
    # 1) test case folder here:
    ################################################################
    TEST_CASE_FOLDER = "test_cases/1-tiny-test-case" #BDR false
    #TEST_CASE_FOLDER = "test_cases/2-small-test-case" # correcvt, true
    #TEST_CASE_FOLDER = "test_cases/3-medium-test-case"
    #TEST_CASE_FOLDER = "test_cases/4-large-test-case" #sim false, one missed
    #TEST_CASE_FOLDER = "test_cases/5-huge-test-case"
    #TEST_CASE_FOLDER = "test_cases/6-gigantic-test-case"
    #TEST_CASE_FOLDER = "test_cases/7-unschedulable-test-case"
    #TEST_CASE_FOLDER = "test_cases/8-unschedulable-test-case"
    #TEST_CASE_FOLDER = "test_cases/9-unschedulable-test-case" #true to all
    #TEST_CASE_FOLDER = "test_cases/10-unschedulable-test-case"


    OUTPUT_CSV = "solution.csv"


    tasks_csv = os.path.join(TEST_CASE_FOLDER, "tasks.csv")
    arch_csv = os.path.join(TEST_CASE_FOLDER, "architecture.csv")
    budgets_csv = os.path.join(TEST_CASE_FOLDER, "budgets.csv")


    for fpath in (tasks_csv, arch_csv, budgets_csv):
        if not os.path.exists(fpath):
            print(f"❌ Missing file: {fpath}")
            return

    print(f"📂 Running test case from: {TEST_CASE_FOLDER}")

    # 2) Load system model from CSV
    system_model = load_csv_files(tasks_csv, arch_csv, budgets_csv, use_comm_links=False)

    # 3) Run hierarchical simulator
    simulator = HierarchicalSimulator(system_model)
    sim_results = simulator.run_simulation(simulation_time=1800.0, dt=0.1)

    print("\n=== SIMULATION RESULTS =´´==")
    for task_id, stats in sim_results["task_stats"].items():
        print(f"Task {task_id} -> max_resp_time = {stats['max_resp_time']:.2f},"
             f" missed_deadlines = {stats['missed_deadlines']}")#

    # 4) BDR-based analysis
    analyzer = BDRAnalysis(system_model)
    analysis_res = analyzer.run_analysis()

    print("\n=== ANALYSIS RESULTS: BDR MODEL ===")
    for core, comps in analysis_res.items():
        print(f"[Core {core}]")
        for cname, result in comps.items():
            bdr = result["bdr"]
            print(
                f"   Component {cname} → α={bdr['alpha']:.3f}, Δ={bdr['delay']:.2f}, schedulable={bdr['schedulable']}")
            for tid, R in bdr["wcrt"].items():
                print(f"      • Task {tid:<15}  WCRT = {R:.2f}")

    print("\n=== ANALYSIS RESULTS: PRM MODEL ===")
    for core, comps in analysis_res.items():
        print(f"[Core {core}]")
        for cname, result in comps.items():
            prm = result["prm"]
            print(f"   Component {cname} → Q={prm['Q']:.2f}, P={prm['P']:.2f}, schedulable={prm['schedulable']}")
            for tid, R in prm["wcrt"].items():
                print(f"      • Task {tid:<15}  WCRT = {R:.2f}")

    # Build task to component map
    task_to_comp = {}
    for core in system_model["cores"]:
        for comp in core["components"]:
            for task in comp["tasks"]:
                task_to_comp[task["id"]] = (core["core_id"], comp["name"])

    # 5) Write solution out
    if OUTPUT_CSV:
        write_solution_csv(sim_results["task_stats"], analysis_res, task_to_comp, filename=OUTPUT_CSV)
        print(f"\n✅ Results written to: {OUTPUT_CSV}")

    print("\n🏁 Simulation + analysis complete.")

if __name__ == "__main__":
    main()
