
import os
from task_loader import load_csv_files
from simulator import HierarchicalSimulator
from bdr_analysis import BDRAnalysis
from bdr_auto_generator import compute_optimal_bdr
from wcrt_analysis import estimate_wcrt
from solution_writer import write_solution_csv
from half_half_mapper import bdr_to_prm
import math
from functools import reduce

AUTO_COMPUTE_BDR = True
DO_WCRT_ANALYSIS = True

def lcm(a, b):
    return abs(a * b) // math.gcd(a, b)

def lcm_list(numbers):
    return reduce(lcm, numbers, 1)

def determine_simulation_time(system_model):
    core_horizons = []
    for core in system_model["cores"]:
        periods = []
        for comp in core["components"]:
            for task in comp["tasks"]:
                periods.append(int(task["period"]))
        if periods:
            core_horizon = 2 * lcm_list(periods)
            core_horizons.append(core_horizon)
    return max(core_horizons) if core_horizons else 800  # fallback


def main():
    # TEST_CASE_FOLDER = "test_cases/custom-test_cases/camera_heavy"
    #TEST_CASE_FOLDER = "test_cases/1-tiny-test-case"
    #TEST_CASE_FOLDER = "test_cases/2-small-test-case"
    #TEST_CASE_FOLDER = "test_cases/3-medium-test-case"
    #TEST_CASE_FOLDER = "test_cases/4-large-test-case"
    TEST_CASE_FOLDER = "test_cases/5-huge-test-case"
    # TEST_CASE_FOLDER = "test_cases/6-gigantic-test-case"
    # TEST_CASE_FOLDER = "test_cases/7-unschedulable-test-case"
    # TEST_CASE_FOLDER = "test_cases/8-unschedulable-test-case"
    # TEST_CASE_FOLDER = "test_cases/9-unschedulable-test-case"
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
    system_model = load_csv_files(tasks_csv, arch_csv, budgets_csv)

    if AUTO_COMPUTE_BDR:
        print("🔄 Auto-computing BDR interface for all components...")
        for core in system_model["cores"]:
            for comp in core["components"]:
                tasks = comp["tasks"]
                scheduler = comp["scheduler"]
                alpha, delta = compute_optimal_bdr(tasks, scheduler)
                comp["bdr_init"] = {"alpha": alpha, "delay": delta}

                C_supply, T_supply = bdr_to_prm(alpha, delta)
                if T_supply > 0:
                    print(f"🔁 Half-Half (BDR→PRM) for {comp['name']}: C={C_supply}, T={T_supply}")
                else:
                    print(f"⚠️  Half-Half mapping skipped for {comp['name']} (delta too small)")

    simulator = HierarchicalSimulator(system_model)
    sim_time = determine_simulation_time(system_model)
    sim_results = simulator.run_simulation(simulation_time=sim_time, dt=0.1)

    if DO_WCRT_ANALYSIS:
        print("🧠 Estimating WCRT for all tasks...")
        for core in system_model["cores"]:
            for comp in core["components"]:
                wcrt_map = estimate_wcrt(comp["tasks"])
                for task in comp["tasks"]:
                    tid = task["id"]
                    if tid in sim_results["task_stats"]:
                        sim_results["task_stats"][tid]["wcrt_est"] = wcrt_map[tid]

    print("\n=== SIMULATION RESULTS ===")
    for tid, stats in sim_results["task_stats"].items():
        wcrt_est = stats.get("wcrt_est", "N/A")
        print(
            f"Task {tid}: max={stats['max_resp_time']:.2f}, avg={stats['avg_response_time']:.2f}, miss={stats['missed_deadlines']}, schedulable={stats['schedulable']}, WCRT_est={wcrt_est}")

    analyzer = BDRAnalysis(system_model)
    analysis = analyzer.run_analysis()

    print("\n=== BDR ANALYSIS RESULTS ===")
    for cid, comps in analysis.items():
        print(f"[Core {cid}]")
        for cname, val in comps.items():
            print(f"  Comp {cname}: alpha={val['alpha']:.3f}, delta={val['delay']:.2f}, schedulable={val['schedulable']}")

    write_solution_csv(sim_results["task_stats"], analysis, filename=OUTPUT_CSV)
    print(f"\n✅ Solution written to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()