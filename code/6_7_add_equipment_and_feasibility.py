"""
6 + 7 + 8 (simplified).
- Join the required loading/unloading equipment from the edited station's facilities table
- Join station equipment availability
- Flag feasible / infeasible rows
"""
import pandas as pd
import os
import sqlite3

BASE = r"E:\GitHub_BehtashSepahan"
INPUT = os.path.join(BASE, "input")
FILTERED_DIR = os.path.join(BASE, "output", "filtered_final")
PHASE2_DIR = os.path.join(BASE, "output", "phase2")
os.makedirs(PHASE2_DIR, exist_ok=True)
os.makedirs(os.path.join(PHASE2_DIR, "feasible"), exist_ok=True)
os.makedirs(os.path.join(PHASE2_DIR, "infeasible"), exist_ok=True)

# ------------------------------------------------------------------
# 1. Build a simple "edited tajhizat" (binary flags) from the original
# ------------------------------------------------------------------
raw_taj = pd.read_excel(os.path.join(INPUT, "essential_tajhizat_commodity_load_and_unload.xlsx"))
print("Raw tajhizat shape:", raw_taj.shape)

equip_cols = [
    "Loader", "CarDumper", "MechanicalShovel", "TLO", "Crane", "LiftTruck",
    "ConveyorBelt", "SuctionDevice", "Manual_Labor", "Hatchloader",
    "DischargeBridge", "ReachStacker", "Transtainer", "Excavator"
]

# Create binary loading / unloading columns
edited = pd.DataFrame(0, index=raw_taj.index, columns=
    ["commodity_name", "commodity_group"] +
    [f"{e}_loading" for e in equip_cols] +
    [f"{e}_unloading" for e in equip_cols] +
    ["high_sided", "low_sided", "balast", "covered", "Description"]
)

edited["commodity_name"] = raw_taj["commodity_name"]
edited["commodity_group"] = raw_taj["commodity_group"]
edited["high_sided"] = raw_taj.get("high_sided", 0)
edited["low_sided"] = raw_taj.get("low_sided", 0)
edited["balast"] = raw_taj.get("balast", 0)
edited["covered"] = raw_taj.get("covered", 0)
edited["Description"] = raw_taj.get("Description", "")

loading_map = {e: f"{e}_loading" for e in equip_cols}
unloading_map = {e: f"{e}_unloading" for e in equip_cols}

for idx, row in raw_taj.iterrows():
    for col in range(1, 15):
        val = row.get(f"subdivision_of_loading{col}")
        if pd.notna(val) and val in loading_map:
            edited.at[idx, loading_map[val]] = 1
        val = row.get(f"subdivision_of_unloading{col}")
        if pd.notna(val) and val in unloading_map:
            edited.at[idx, unloading_map[val]] = 1

edited_path = os.path.join(PHASE2_DIR, "edited_tajhizat_commodity_load_and_unload.xlsx")
edited.to_excel(edited_path, index=False)
print(f"✅ Edited tajhizat saved → {edited_path}")

# ------------------------------------------------------------------
# 2. Create a tiny station-equipment table for the stations we actually use
# ------------------------------------------------------------------
# For the test we give every station full equipment so most rows become Feasible.
# You can later replace this with the real tajhizat_stations.xlsx.
stations_used = pd.read_csv(os.path.join(INPUT, "all_available_rail_stations_xy.csv"))
station_equip = stations_used[["Station_code", "Station_name"]].copy()
for e in equip_cols:
    station_equip[e] = 1          # assume all equipment present for the test

station_equip_path = os.path.join(PHASE2_DIR, "station_equipment_test.csv")
station_equip.to_csv(station_equip_path, index=False)
print(f"✅ Test station equipment → {station_equip_path}")

# ------------------------------------------------------------------
# 3. SQLite join: final data + commodity equipment + station equipment
# ------------------------------------------------------------------
db_path = os.path.join(BASE, "phase2_test.db")
if os.path.exists(db_path):
    os.remove(db_path)
conn = sqlite3.connect(db_path)

# Load tables
final_df = pd.read_csv(os.path.join(FILTERED_DIR, "filtered_whole.csv"))
final_df.to_sql("phase1_outputs", conn, if_exists="replace", index=False)

edited.to_sql("tajhizat", conn, if_exists="replace", index=False)
station_equip.to_sql("station_equipment", conn, if_exists="replace", index=False)

query = """
WITH equipment_check AS (
    SELECT
        p.*,
        t.commodity_group AS taj_group,
        t.Loader_loading, t.CarDumper_loading, t.MechanicalShovel_loading,
        t.TLO_loading, t.Crane_loading, t.LiftTruck_loading,
        t.ConveyorBelt_loading, t.SuctionDevice_loading, t.Manual_Labor_loading,
        t.Hatchloader_loading, t.DischargeBridge_loading, t.ReachStacker_loading,
        t.Transtainer_loading, t.Excavator_loading,
        t.Loader_unloading, t.CarDumper_unloading, t.MechanicalShovel_unloading,
        t.TLO_unloading, t.Crane_unloading, t.LiftTruck_unloading,
        t.ConveyorBelt_unloading, t.SuctionDevice_unloading, t.Manual_Labor_unloading,
        t.Hatchloader_unloading, t.DischargeBridge_unloading, t.ReachStacker_unloading,
        t.Transtainer_unloading, t.Excavator_unloading,
        t.high_sided, t.low_sided, t.balast, t.covered, t.Description,

        so.Loader AS origin_loader, so.CarDumper AS origin_cardumper,
        so.MechanicalShovel AS origin_mechanicalshovel, so.TLO AS origin_tlo,
        so.Crane AS origin_crane, so.LiftTruck AS origin_lifttruck,
        so.ConveyorBelt AS origin_conveyorbelt, so.SuctionDevice AS origin_suctiondevice,
        so.Manual_Labor AS origin_manual_labor, so.Hatchloader AS origin_hatchloader,
        so.DischargeBridge AS origin_dischargebridge, so.ReachStacker AS origin_reachstacker,
        so.Transtainer AS origin_transtainer, so.Excavator AS origin_excavator,

        sd.Loader AS dest_loader, sd.CarDumper AS dest_cardumper,
        sd.MechanicalShovel AS dest_mechanicalshovel, sd.TLO AS dest_tlo,
        sd.Crane AS dest_crane, sd.LiftTruck AS dest_lifttruck,
        sd.ConveyorBelt AS dest_conveyorbelt, sd.SuctionDevice AS dest_suctiondevice,
        sd.Manual_Labor AS dest_manual_labor, sd.Hatchloader AS dest_hatchloader,
        sd.DischargeBridge AS dest_dischargebridge, sd.ReachStacker AS dest_reachstacker,
        sd.Transtainer AS dest_transtainer, sd.Excavator AS dest_excavator
    FROM phase1_outputs p
    LEFT JOIN tajhizat t
      ON LOWER(TRIM(p.commodity_name)) = LOWER(TRIM(t.commodity_name))
    LEFT JOIN station_equipment so
      ON p.assigned_station_name_for_road_origin = so.Station_name
    LEFT JOIN station_equipment sd
      ON p.assigned_station_name_for_road_destination = sd.Station_name
)
SELECT *,
    CASE WHEN (
        (Loader_loading = 0 OR (Loader_loading = 1 AND origin_loader = 1)) AND
        (CarDumper_loading = 0 OR (CarDumper_loading = 1 AND origin_cardumper = 1)) AND
        (MechanicalShovel_loading = 0 OR (MechanicalShovel_loading = 1 AND origin_mechanicalshovel = 1)) AND
        (TLO_loading = 0 OR (TLO_loading = 1 AND origin_tlo = 1)) AND
        (Crane_loading = 0 OR (Crane_loading = 1 AND origin_crane = 1)) AND
        (LiftTruck_loading = 0 OR (LiftTruck_loading = 1 AND origin_lifttruck = 1)) AND
        (ConveyorBelt_loading = 0 OR (ConveyorBelt_loading = 1 AND origin_conveyorbelt = 1)) AND
        (SuctionDevice_loading = 0 OR (SuctionDevice_loading = 1 AND origin_suctiondevice = 1)) AND
        (Manual_Labor_loading = 0 OR (Manual_Labor_loading = 1 AND origin_manual_labor = 1)) AND
        (Hatchloader_loading = 0 OR (Hatchloader_loading = 1 AND origin_hatchloader = 1)) AND
        (DischargeBridge_loading = 0 OR (DischargeBridge_loading = 1 AND origin_dischargebridge = 1)) AND
        (ReachStacker_loading = 0 OR (ReachStacker_loading = 1 AND origin_reachstacker = 1)) AND
        (Transtainer_loading = 0 OR (Transtainer_loading = 1 AND origin_transtainer = 1)) AND
        (Excavator_loading = 0 OR (Excavator_loading = 1 AND origin_excavator = 1)) AND

        (Loader_unloading = 0 OR (Loader_unloading = 1 AND dest_loader = 1)) AND
        (CarDumper_unloading = 0 OR (CarDumper_unloading = 1 AND dest_cardumper = 1)) AND
        (MechanicalShovel_unloading = 0 OR (MechanicalShovel_unloading = 1 AND dest_mechanicalshovel = 1)) AND
        (TLO_unloading = 0 OR (TLO_unloading = 1 AND dest_tlo = 1)) AND
        (Crane_unloading = 0 OR (Crane_unloading = 1 AND dest_crane = 1)) AND
        (LiftTruck_unloading = 0 OR (LiftTruck_unloading = 1 AND dest_lifttruck = 1)) AND
        (ConveyorBelt_unloading = 0 OR (ConveyorBelt_unloading = 1 AND dest_conveyorbelt = 1)) AND
        (SuctionDevice_unloading = 0 OR (SuctionDevice_unloading = 1 AND dest_suctiondevice = 1)) AND
        (Manual_Labor_unloading = 0 OR (Manual_Labor_unloading = 1 AND dest_manual_labor = 1)) AND
        (Hatchloader_unloading = 0 OR (Hatchloader_unloading = 1 AND dest_hatchloader = 1)) AND
        (DischargeBridge_unloading = 0 OR (DischargeBridge_unloading = 1 AND dest_dischargebridge = 1)) AND
        (ReachStacker_unloading = 0 OR (ReachStacker_unloading = 1 AND dest_reachstacker = 1)) AND
        (Transtainer_unloading = 0 OR (Transtainer_unloading = 1 AND dest_transtainer = 1)) AND
        (Excavator_unloading = 0 OR (Excavator_unloading = 1 AND dest_excavator = 1))
    ) THEN 'Feasible' ELSE 'Infeasible' END AS Feasibility
FROM equipment_check
"""

results = pd.read_sql_query(query, conn)
print("Feasibility check shape:", results.shape)
print(results["Feasibility"].value_counts())

feasible = results[results["Feasibility"] == "Feasible"]
infeasible = results[results["Feasibility"] == "Infeasible"]

feasible.to_csv(os.path.join(PHASE2_DIR, "feasible", "feasible_output.csv"), index=False)
infeasible.to_csv(os.path.join(PHASE2_DIR, "infeasible", "infeasible_output.csv"), index=False)

print(f"✅ Feasible   → {len(feasible)} rows")
print(f"✅ Infeasible → {len(infeasible)} rows")

conn.close()
print("\nDone with equipment + feasibility steps.")
