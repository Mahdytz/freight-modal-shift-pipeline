"""
4. Calculate total OD distance (road origin→rail + rail→rail + rail→road destination)
   and create final_output files.
"""
import pandas as pd
import glob
import os

BASE = r"E:\GitHub_BehtashSepahan"
WHOLE_DIR = os.path.join(BASE, "output", "assigned_whole")
FINAL_DIR = os.path.join(BASE, "output", "final_output")
os.makedirs(FINAL_DIR, exist_ok=True)

csv_files = sorted(glob.glob(os.path.join(WHOLE_DIR, "assigned_station_whole*.csv")))
print(f"Found {len(csv_files)} whole files")

i = 1
for path in csv_files:
    print(f"\n{'='*70}\nProcessing {path}")
    assigned_stations = pd.read_csv(path)
    print("Input rows:", len(assigned_stations))

    # Total multimodal distance
    summation = (
        assigned_stations["distance_from_road_origin_to_rail"] +
        assigned_stations["distance_from_rail_to_road_destination"] +
        assigned_stations["Rail_Distance"]
    ).round(3)

    final_output = pd.DataFrame({
        "commodity_id": assigned_stations["commodity_id"],
        "commodity_name": assigned_stations["commodity_name"],
        "commodity_group": assigned_stations.get("commodity_group", None),
        "receive_name": assigned_stations["receive_name"],
        "RECEIVE_CODE": assigned_stations.get("RECEIVE_CODE", None),
        "origin_city_name_road": assigned_stations["origin_city_name"],
        "origin_province_name_road": assigned_stations["origin_province_name"],
        "ORIGIN_CITY_ID": assigned_stations.get("ORIGIN_CITY_ID", None),
        "ORIGIN_PROVINCE_ID": assigned_stations.get("ORIGIN_PROVINCE_ID", None),
        "assigned_station_id_for_road_origin": assigned_stations["assigned_station_id_for_road_origin"],
        "assigned_station_name_for_road_origin": assigned_stations["assigned_station_name_for_road_origin"],
        "distance_from_road_origin_to_rail": assigned_stations["distance_from_road_origin_to_rail"],
        "destination_city_name_road": assigned_stations["destination_city_name"],
        "destination_province_name": assigned_stations["destination_province_name"],
        "DEST_CITY_ID": assigned_stations.get("DEST_CITY_ID", None),
        "DEST_PROVINCE_ID": assigned_stations.get("DEST_PROVINCE_ID", None),
        "assigned_station_id_for_road_destination": assigned_stations["assigned_station_id_for_road_destination"],
        "assigned_station_name_for_road_destination": assigned_stations["assigned_station_name_for_road_destination"],
        "distance_from_rail_to_road_destination": assigned_stations["distance_from_rail_to_road_destination"],
        "weight": assigned_stations["weight"],
        "Initial_total_distance_road": assigned_stations["Initial_total_distance_road"],
        "Rail_Distance": assigned_stations["Rail_Distance"],
        "od_distance_whole": summation,
        "Ton_Km_Road": assigned_stations["weight"] * assigned_stations["Initial_total_distance_road"],
    })

    # Drop same-city ODs (safety)
    final_output = final_output[
        final_output["origin_city_name_road"] != final_output["destination_city_name_road"]
    ]

    out_path = os.path.join(FINAL_DIR, f"final{i}.csv")
    final_output.to_csv(out_path, index=False)
    print(f"✅ Saved {len(final_output)} rows → {out_path}")

    print("\nSample of final_output:")
    print(final_output[[
        "commodity_name", "origin_city_name_road", "assigned_station_name_for_road_origin",
        "destination_city_name_road", "assigned_station_name_for_road_destination",
        "Rail_Distance", "od_distance_whole", "weight"
    ]].head(8).to_string())

    i += 1

# ------------------------------------------------------------------
# Merge all final*.csv into one file
# ------------------------------------------------------------------
print("\n" + "="*70)
print("Merging all final*.csv into one file...")
all_finals = sorted(glob.glob(os.path.join(FINAL_DIR, "final*.csv")))
dfs = [pd.read_csv(f) for f in all_finals]
final_df = pd.concat(dfs, ignore_index=True)

merged_path = os.path.join(FINAL_DIR, "final_with_whole_dist.csv")
final_df.to_csv(merged_path, index=False)
print(f"✅ Final aggregated file → {merged_path}")
print(f"Total rows: {len(final_df)}")
print("\nDone with step 4.")
