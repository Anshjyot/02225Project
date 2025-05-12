# 02225 DRTS Project – Group 29

This project implements a full analysis and simulation toolchain for hierarchical scheduling of ADAS systems on multicore platforms. It supports Bounded Delay Resource (BDR) modeling, Periodic Resource Model (PRM) validation, Worst-Case Response Time (WCRT) analysis, simulation, core assignment optimization, and delay tuning. 

---

## 📦 Project Contents

| File/Folder               | Description                                                      |
|---------------------------|------------------------------------------------------------------|
| `main.py`                 | Main entry point. Controls execution of analysis and simulation. |
| `bdr_analysis.py`         | Compositional BDR and PRM schedulability analysis tool.          |
| `simulator.py`            | Discrete-time hierarchical real-time system simulator.           |
| `wcrt_analysis.py`        | Exact WCRT computation for EDF and RM.                           |
| `task_loader.py`          | Loads system model (tasks, architecture, budgets) from CSV.      |
| `greedy_core_assigner.py` | Heuristic core assignment algorithm.                             |
| `resource_tuner.py`       | Delay reduction by optimizing (Q, P) values.                     |
| `solution_writer.py`      | Exports simulation and analysis results to CSV.                  |
| `test_cases/`             | Folder containing all official and custom test case folders.     |
| `README.md`               | This file.                                                       |
| `solution.csv`            | Output files are stored in here.                                 |

---

## 🐍 Requirements

- **Python version:** `3.12.7` (recommended for best compatibility)
- **Dependencies:** None (only standard Python libraries are used)

You can install a matching version of Python via:

```bash
pyenv install 3.12.7
pyenv local 3.12.7
```

---

## 🚀 How to Run the Tool

Navigate to the root folder and run:

```bash
python main.py
```

The tool will:
- Load a test case from the specified folder
- Optionally run WCRT analysis, delay tuning, and core reassignment
- Output results in CSV format

### ✏️ Configure Execution in `main.py`

Edit the following block to choose the test case and optional features:

```python
# Example configuration
TEST_CASE_FOLDER = "test_cases/3-medium-test-case"
USE_TUNER = False;
USE_CORE_ASSIGNER = False;
system_model = load_csv_files(tasks_csv, arch_csv, budgets_csv, use_comm_links=True)
```

You can change `TEST_CASE_FOLDER` to any of the following:

- `test_cases/1-tiny-test-case`
- `test_cases/2-small-test-case`
- `test_cases/3-medium-test-case`
- `test_cases/4-large-test-case`
- `test_cases/5-huge-test-case`
- `test_cases/6-gigantic-test-case`
- `test_cases/7-unschedulable-test-case`
- `test_cases/8-unschedulable-test-case`
- `test_cases/9-unschedulable-test-case`
- `test_cases/10-unschedulable-test-case`

And custom ones:
- `test_cases/custom_cases/1-custom-test-case`
- `test_cases/custom_cases/2-custom-test-case`

## 📂 Input File Format

Each test case folder should contain the following files:

- `tasks.csv`: Task parameters (wcet, period, priority, component)
- `architecture.csv`: Core properties (speed, scheduler)
- `budgets.csv`: Component resource parameters (Q, P), scheduling policy, and core mapping
- `comm_links.csv` *(optional)*: Communication delays between tasks (used in `1-tiny-test-case` & `1-custom-test-case`)

---

## 📤 Output

Simulation and analysis results are printed to the terminal and optionally saved to a CSV (`solution.csv`).

Output fields include:

- Task-level schedulability
- Average and max response time (simulation)
- WCRT (analysis)
- Component schedulability flags

---


## 👨‍🔬 Authors

Group 29 (DTU 02225 Distributed Real-Time Systems Project):
- Anshjyot Singh (s215806)
- Anthony Raphael Stylinars (s215519)
- Nipun Fernando (s215518)
- Vandad Kolahi Azar (s205073)

---

## 📚 References

- Buttazzo, G. (2024). *Hard Real-Time Computing Systems: Predictable Scheduling Algorithms and Applications*. Springer. [Available via DTU Library]
- Kopetz, H., & Steiner, W. (2022). *Real-Time Systems: Design Principles for Distributed Embedded Applications*. Springer. [Available via DTU Library]
- Lipari, G., & Bini, E. (2022). *Hierarchical Scheduling*. In *Handbook of Real-Time Computing*. [PDF provided in course materials]
- Devi, U. C., & Anderson, J. H. (2014). *General and Efficient Response Time Analysis for EDF Scheduling*. In *DATE 2014*
- Mok, A. K., Feng, Y., & Chen, D. (2003). *A Periodic Resource Model for Compositional Real-Time Guarantees*. In *RTSS 2003*
- Joseph, M., & Pandya, P. K. (1986). Finding Response Times in a Real-Time System. The Computer Journal, 29(5), 390–395.
- *TSN for Dummies*. [PDF provided in Week 4 course materials]
- Course slides and project PDFs, available on the DTU 02225 course page
- Handbook of Real-Time Computing, Chapter on Hierarchical Scheduling
- Lecture notes from 02225 (Paul Pop, DTU)
- GitHub: [https://github.com/Plyncesilva/DRTS_Project-Test-Cases)
