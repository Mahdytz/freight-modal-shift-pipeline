"""
2. Assign closest rail station to each road destination.
"""
import pandas as pd
import numpy as np
import os
import glob

BASE = r"E:\GitHub_BehtashSepahan"
INPUT = os.path.join(BASE, "input")
ORIGINS_DIR = os.path.join(BASE, "output", "assigned_stations_origins")
OUTPUT_DIR = os.path.join(BASE, "output", "assigned_station_destinations")
os.makedirs(OUTPUT_DIR, exist_ok=True)

stations_df = pd.read_csv(os.path.join(INPUT, "all_available_rail_stations_xy.csv"))
print("stations_df shape:", stations_df.shape)

csv_files = sorted(glob.glob(os.path.join(ORIGINS_DIR, "assigned_stations_origins*.csv")))
print(f"Found {len(csv_files)} origin files")

for i, path in enumerate(csv_files, start=1):
    print(f"\n{'='*60}\nProcessing {path}")
    assigned_stations_origins = pd.read_csv(path)
    print("Input rows:", len(assigned_stations_origins))

    distances = np.sqrt(
        (assigned_stations_origins["destination_x"].values[:, np.newaxis] - stations_df["X_cordinate"].values) ** 2 +
        (assigned_stations_origins["destination_y"].values[:, np.newaxis] - stations_df["Y_cordinate"].values) ** 2
    )

    closest_station_indices = np.argmin(distances, axis=1)
    closest_station_ids  = stations_df.loc[closest_station_indices, "Station_code"].values
    closest_station_name = stations_df.loc[closest_station_indices, "Station_name"].values
    closest_distances    = np.min(distances, axis=1) / 1000.0

    assigned_station_destinations = pd.DataFrame({
        "commodity_id": assigned_stations_origins["commodity_id"],
        "commodity_name": assigned_stations_origins["commodity_name"],
        "commodity_group": assigned_stations_origins["commodity_group"],
        "origin_city_name": assigned_stations_origins["origin_city_name"],
        "origin_province_name": assigned_stations_origins["origin_province_name"],
        "ORIGIN_CITY_ID": assigned_stations_origins["ORIGIN_CITY_ID"],
        "ORIGIN_PROVINCE_ID": assigned_stations_origins["ORIGIN_PROVINCE_ID"],
        "assigned_station_id_for_road_origin": assigned_stations_origins["assigned_station_id_for_road_origin"],
        "assigned_station_name_for_road_origin": assigned_stations_origins["assigned_station_name_for_road_origin"],
        "distance_from_road_origin_to_rail": assigned_stations_origins["distance_from_road_origin_to_rail"],
        "destination_city_name": assigned_stations_origins["destination_city_name"],
        "destination_province_name": assigned_stations_origins["destination_province_name"],
        "DEST_CITY_ID": assigned_stations_origins["DEST_CITY_ID"],
        "DEST_PROVINCE_ID": assigned_stations_origins["DEST_PROVINCE_ID"],
        "assigned_station_id_for_road_destination": closest_station_ids,
        "assigned_station_name_for_road_destination": closest_station_name,
        "distance_from_rail_to_road_destination": closest_distances,
        "weight": assigned_stations_origins["weight"] / 1000.0,   # keep consistent with original code
        "Initial_total_distance_road": assigned_stations_origins["Initial_total_distance_road"],
        "receive_name": assigned_stations_origins["receive_name"],
        "RECEIVE_CODE": assigned_stations_origins["RECEIVE_CODE"],
    })

    print("Before 30 km dest filter:", len(assigned_station_destinations))
    assigned_station_destinations = assigned_station_destinations[
        assigned_station_destinations["distance_from_rail_to_road_destination"] <= 30
    ]
    print("After 30 km dest filter :", len(assigned_station_destinations))

    out_path = os.path.join(OUTPUT_DIR, f"assigned_destination{i}.csv")
    assigned_station_destinations.to_csv(out_path, index=False)
    print(f"✅ Saved → {out_path}")

    print("\nSample:")
    print(assigned_station_destinations[[
        "commodity_name", "origin_city_name", "assigned_station_name_for_road_origin",
        "destination_city_name", "assigned_station_name_for_road_destination",
        "distance_from_rail_to_road_destination"
    ]].head(6).to_string())

print("\nDone with step 2.")
