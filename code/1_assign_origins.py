"""
1. Assign closest rail station to each road origin.
"""
import pandas as pd
import numpy as np
import os

BASE = r"E:\GitHub_BehtashSepahan"
INPUT = os.path.join(BASE, "input")
OUTPUT_DIR = os.path.join(BASE, "output", "assigned_stations_origins")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------------------------------------------------------------
# Load data
# ------------------------------------------------------------------
od_xy_merged = pd.read_csv(os.path.join(BASE, "output", "1401", "road_od_with_xy.csv"))
print("od_xy_merged shape:", od_xy_merged.shape)

stations_df = pd.read_csv(os.path.join(INPUT, "all_available_rail_stations_xy.csv"))
print("stations_df shape:", stations_df.shape)
print(stations_df.head(3))

# ------------------------------------------------------------------
# Because the test set is tiny we process everything in one chunk
# ------------------------------------------------------------------
i = 0
number_of_rows = 500000
n_chunks = int(np.ceil(len(od_xy_merged) / number_of_rows))
print(f"n_chunks = {n_chunks}")

while i <= n_chunks:
    start = i * number_of_rows
    end = (i + 1) * number_of_rows
    od_xy_merged_splitted = od_xy_merged.iloc[start:end].copy()
    if len(od_xy_merged_splitted) == 0:
        break

    print(f"\n--- Chunk {i+1}: rows {start} → {start+len(od_xy_merged_splitted)-1} ---")

    # Euclidean distance matrix (rows = ODs, cols = stations)
    distances = np.sqrt(
        (od_xy_merged_splitted["origin_x"].values[:, np.newaxis] - stations_df["X_cordinate"].values) ** 2 +
        (od_xy_merged_splitted["origin_y"].values[:, np.newaxis] - stations_df["Y_cordinate"].values) ** 2
    )

    closest_station_indices = np.argmin(distances, axis=1)
    closest_station_ids   = stations_df.loc[closest_station_indices, "Station_code"].values
    closest_station_name  = stations_df.loc[closest_station_indices, "Station_name"].values
    closest_distances     = np.min(distances, axis=1) / 1000.0   # convert to km

    assigned_station_origins = pd.DataFrame({
        "commodity_id": od_xy_merged_splitted["KALA_ID"].values,
        "commodity_name": od_xy_merged_splitted["KALA_NAME"].values,
        "commodity_group": od_xy_merged_splitted["GOROOH_KALA_NAME"].values,
        "origin_city_name": od_xy_merged_splitted["MABDA_SHAHR_NAME"].values,
        "origin_province_name": od_xy_merged_splitted["MABDA_OSTAN_NAME"].values,
        "ORIGIN_CITY_ID": od_xy_merged_splitted["ORIGIN_CITY_ID"].values,
        "ORIGIN_PROVINCE_ID": od_xy_merged_splitted["ORIGIN_PROVINCE_ID"].values,
        "assigned_station_id_for_road_origin": closest_station_ids,
        "assigned_station_name_for_road_origin": closest_station_name,
        "distance_from_road_origin_to_rail": closest_distances,
        "destination_city_name": od_xy_merged_splitted["MAGHSAD_SHAHR_NAME"].values,
        "destination_province_name": od_xy_merged_splitted["MAGHSAD_OSTAN_NAME"].values,
        "DEST_CITY_ID": od_xy_merged_splitted["DEST_CITY_ID"].values,
        "DEST_PROVINCE_ID": od_xy_merged_splitted["DEST_PROVINCE_ID"].values,
        "destination_x": od_xy_merged_splitted["destination_x"].values,
        "destination_y": od_xy_merged_splitted["destination_y"].values,
        "weight": od_xy_merged_splitted["VAZN"].values,
        "receive_name": od_xy_merged_splitted["RECEIVENAME"].values,
        "RECEIVE_CODE": od_xy_merged_splitted["RECEIVE_CODE"].values,
        "Initial_total_distance_road": od_xy_merged_splitted["MASAFAT"].values,
    })

    print("Before 30 km filter:", len(assigned_station_origins))
    assigned_stations_origins = assigned_station_origins[
        assigned_station_origins["distance_from_road_origin_to_rail"] <= 30
    ].copy()
    print("After 30 km filter :", len(assigned_stations_origins))

    # Drop same-city ODs
    assigned_stations_origins = assigned_stations_origins[
        assigned_stations_origins["origin_city_name"] != assigned_stations_origins["destination_city_name"]
    ]
    print("After same-city drop:", len(assigned_stations_origins))

    out_path = os.path.join(OUTPUT_DIR, f"assigned_stations_origins{i+1}.csv")
    assigned_stations_origins.to_csv(out_path, index=False)
    print(f"✅ Saved → {out_path}")

    # Diagnostics
    print("\nDistance stats (km):")
    print(assigned_stations_origins["distance_from_road_origin_to_rail"].describe())
    print("\nSample:")
    print(assigned_stations_origins[[
        "commodity_name", "origin_city_name", "assigned_station_name_for_road_origin",
        "distance_from_road_origin_to_rail", "destination_city_name"
    ]].head(8).to_string())

    i += 1

print("\nDone with step 1.")
