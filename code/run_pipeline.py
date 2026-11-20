#!/usr/bin/env python3
"""
Main menu / orchestrator for the multimodal (road→rail) OD pipeline.
Runs steps 0 → 6/7 sequentially, clears memory after each step,
prints clear progress + error location, and optionally opens the final Excel.
"""
import os
import sys
import traceback
import gc
import time
import subprocess
from pathlib import Path

# ------------------------------------------------------------------
# PATHS – main directories (as requested)
# ------------------------------------------------------------------
BASE = Path(r"E:\GitHub_BehtashSepahan")
CODES_DIR = BASE / "code"
INPUT_DIR = BASE / "input"
OUTPUT_DIR = BASE / "output"

# Sandbox / test environment (uncomment if running inside the current test setup):
# BASE = Path("/home/workdir/artifacts/pipeline_test")
# CODES_DIR = BASE / "codes"
# INPUT_DIR = BASE / "input"
# OUTPUT_DIR = BASE / "output"

STEPS = [
    ("0_merge_xy.py",                     "Step 0: Merge road OD with XY coordinates"),
    ("1_assign_origins.py",               "Step 1: Assign closest rail station to origins (≤30 km)"),
    ("2_assign_destinations.py",          "Step 2: Assign closest rail station to destinations (≤30 km)"),
    ("3_merge_rail_distances.py",         "Step 3: Merge rail-to-rail distances (SQLite)"),
    ("4_calculate_total_distance.py",     "Step 4: Calculate total multimodal distance & merge finals"),
    ("5_aggregate_and_filter.py",         "Step 5: Aggregate / light filter"),
    ("6_7_add_equipment_and_feasibility.py", "Step 6+7: Equipment requirements + Feasibility flag"),
]

FINAL_CSV = OUTPUT_DIR / "phase2" / "feasible" / "feasible_output.csv"
FINAL_XLSX = OUTPUT_DIR / "phase2" / "feasible" / "feasible_output.xlsx"


def clear_memory():
    """Force garbage collection to free RAM between steps."""
    gc.collect()
    time.sleep(0.3)


def run_step(script_name: str, description: str) -> bool:
    """Execute one pipeline script. Returns True on success."""
    script_path = CODES_DIR / script_name
    print("\n" + "=" * 70)
    print(f"▶  {description}")
    print(f"   File: {script_path}")
    print("=" * 70)

    if not script_path.exists():
        print(f"❌ ERROR: Script not found → {script_path}")
        return False

    try:
        # Run in a clean subprocess so memory is released when it finishes
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(BASE),
            capture_output=False,          # show stdout/stderr live
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print(f"\n❌ Step failed with exit code {result.returncode}")
            return False
        print(f"\n✅ {description} finished successfully.")
        return True
    except Exception as e:
        print(f"\n❌ EXCEPTION while running {script_name}:")
        traceback.print_exc()
        return False
    finally:
        clear_memory()


def convert_final_to_excel():
    """Optional: save a nice Excel version of the final feasible file."""
    try:
        import pandas as pd
        if FINAL_CSV.exists():
            df = pd.read_csv(FINAL_CSV)
            df.to_excel(FINAL_XLSX, index=False)
            print(f"✅ Excel version written → {FINAL_XLSX}")
            return True
    except Exception as e:
        print(f"⚠ Could not create Excel: {e}")
    return False


def open_final_file():
    """Try to open the final output with the default application."""
    target = FINAL_XLSX if FINAL_XLSX.exists() else FINAL_CSV
    if not target.exists():
        print("⚠ Final file not found, nothing to open.")
        return
    print(f"\n📂 Opening: {target}")
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(target))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(target)], check=False)
        else:
            # Linux – try xdg-open
            subprocess.run(["xdg-open", str(target)], check=False)
    except Exception as e:
        print(f"Could not auto-open file: {e}")
        print(f"Please open it manually: {target}")


def print_menu():
    print("\n" + "═" * 60)
    print("  MULTIMODAL ROAD→RAIL OD PIPELINE  –  MENU")
    print("═" * 60)
    print("  1. Run full pipeline (steps 0 → 6/7)")
    print("  2. Run full pipeline + open final output")
    print("  3. Open final output only")
    print("  4. Exit")
    print("═" * 60)


def main():
    # Ensure directories exist
    for d in [CODES_DIR, INPUT_DIR, OUTPUT_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    while True:
        print_menu()
        choice = input("Select option [1-4]: ").strip()

        if choice == "1" or choice == "2":
            print("\n🚀 Starting full pipeline…")
            success = True
            for script, desc in STEPS:
                if not run_step(script, desc):
                    print(f"\n🛑 Pipeline stopped because of error in {script}")
                    success = False
                    break
            if success:
                print("\n" + "🎉" * 10)
                print("ALL STEPS COMPLETED SUCCESSFULLY")
                print("🎉" * 10)
                convert_final_to_excel()
                if choice == "2":
                    open_final_file()
            else:
                print("\nPipeline finished with errors. Check the log above.")
            input("\nPress Enter to return to menu…")

        elif choice == "3":
            convert_final_to_excel()
            open_final_file()
            input("\nPress Enter to return to menu…")

        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3 or 4.")


if __name__ == "__main__":
    main()
