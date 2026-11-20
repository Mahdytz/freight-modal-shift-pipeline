"""
3. Merge assigned origin/destination stations with rail-to-rail distances.
Uses SQLite as in the original code.
"""
import pandas as pd
import os
import sqlite3
import glob

BASE = r"E:\GitHub_BehtashSepahan"
INPUT = os.path.join(BASE, "input")
DEST_DIR = os.path.join(BASE, "output", "assigned_station_destinations")
OUTPUT_DIR = os.path.join(BASE, "output", "assigned_whole")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------------------------------------------------------------
# SQLite connection
# ------------------------------------------------------------------
db_path = os.path.join(BASE, "assigned_1401_test.db")
if os.path.exists(db_path):
    os.remove(db_path)
conn = sqlite3.connect(db_path)
print(f"SQLite DB → {db_path}")

# ------------------------------------------------------------------
# Load rail distance matrix
# ------------------------------------------------------------------
rail_distance_file = os.path.join(INPUT, "rail_distance_alafipour_od_xy.xlsx")
distance_of_stations = pd.read_excel(rail_distance_file)
print("Rail distance shape:", distance_of_stations.shape)
print("Columns:", distance_of_stations.columns.tolist())

# Keep only the columns we need and clean names
distance_of_stations = distance_of_stations[
    ["origin_name", "destination_name", "Rail_Distance"]
].copy()
distance_of_stations.to_sql("distance_of_stations", conn, if_exists="replace", index=False)
print("Loaded distance_of_stations into SQLite")

# ------------------------------------------------------------------
# Process each assigned_destination file
# ------------------------------------------------------------------
csv_files = sorted(glob.glob(os.path.join(DEST_DIR, "assigned_destination*.csv")))
print(f"Found {len(csv_files)} destination files")

j = 1
for i, path in enumerate(csv_files, start=1):
    print(f"\n{'='*60}\nProcessing {path}")
    assigned = pd.read_csv(path)
    print("Rows:", len(assigned))

    table_name = f"assigned_station_destinations{j}"
    assigned.to_sql(table_name, conn, if_exists="replace", index=False)

    query = f"""
    SELECT
        a.commodity_id,
        a.commodity_name,
        a.commodity_group,
        a.origin_city_name,
        a.origin_province_name,
        a.ORIGIN_CITY_ID,
        a.ORIGIN_PROVINCE_ID,
        a.assigned_station_id_for_road_origin,
        a.assigned_station_name_for_road_origin,
        a.distance_from_road_origin_to_rail,
        a.destination_city_name,
        a.destination_province_name,
        a.DEST_CITY_ID,
        a.DEST_PROVINCE_ID,
        a.assigned_station_id_for_road_destination,
        a.assigned_station_name_for_road_destination,
        a.distance_from_rail_to_road_destination,
        a.weight,
        a.Initial_total_distance_road,
        a.receive_name,
        a.RECEIVE_CODE,
        d.Rail_Distance
    FROM {table_name} AS a
    LEFT JOIN distance_of_stations AS d
      ON a.assigned_station_name_for_road_origin = d.origin_name
     AND a.assigned_station_name_for_road_destination = d.destination_name
    """
    merged_df = pd.read_sql(query, conn)
    print("After join:", len(merged_df))
    print("Rail_Distance nulls:", merged_df["Rail_Distance"].isna().sum())

    # Save intermediate
    out_path = os.path.join(OUTPUT_DIR, f"assigned_station_whole{j}.csv")
    merged_df.to_csv(out_path, index=False)
    print(f"✅ Saved → {out_path}")

    print("\nSample:")
    print(merged_df[[
        "commodity_name", "assigned_station_name_for_road_origin",
        "assigned_station_name_for_road_destination", "Rail_Distance",
        "distance_from_road_origin_to_rail", "distance_from_rail_to_road_destination"
    ]].head(6).to_string())

    j += 1

conn.close()
print("\nDone with step 3.")
