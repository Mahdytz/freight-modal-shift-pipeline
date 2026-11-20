"""
5. Light aggregation + optional filtering.
   For the test set we keep everything and also produce a simple
   aggregation by (commodity_id, ORIGIN_CITY_ID, DEST_CITY_ID, RECEIVE_CODE).
"""
import pandas as pd
import os

BASE = r"E:\GitHub_BehtashSepahan"
FINAL_DIR = os.path.join(BASE, "output", "final_output")
FILTERED_DIR = os.path.join(BASE, "output", "filtered_final")
os.makedirs(FILTERED_DIR, exist_ok=True)

path = os.path.join(FINAL_DIR, "final_with_whole_dist.csv")
df = pd.read_csv(path)
print("Input shape:", df.shape)
print("Columns:", df.columns.tolist())

# ------------------------------------------------------------------
# Optional filters (commented out for the small test set)
# ------------------------------------------------------------------
# df = df[df["weight"] >= 50]          # example threshold
# df = df[df["Ton_Km_Road"] > 5000]

# Sort by the ID columns the user cares about
sort_cols = [c for c in ["commodity_id", "RECEIVE_CODE", "ORIGIN_CITY_ID", "DEST_CITY_ID", "weight"] if c in df.columns]
df = df.sort_values(by=sort_cols).reset_index(drop=True)

# Save the filtered (or unfiltered) whole file
out_whole = os.path.join(FILTERED_DIR, "filtered_whole.csv")
df.to_csv(out_whole, index=False)
print(f"✅ Saved filtered_whole → {out_whole} ({len(df)} rows)")

# ------------------------------------------------------------------
# Simple aggregation example (sum weight by the key IDs)
# ------------------------------------------------------------------
agg_keys = [c for c in ["commodity_id", "commodity_name", "ORIGIN_CITY_ID", "origin_city_name_road",
                        "DEST_CITY_ID", "destination_city_name_road", "RECEIVE_CODE", "receive_name"] if c in df.columns]

agg = (df.groupby(agg_keys, as_index=False)
         .agg(
             total_weight=("weight", "sum"),
             mean_od_distance=("od_distance_whole", "mean"),
             mean_rail_distance=("Rail_Distance", "mean"),
             n_shipments=("weight", "count")
         )
         .sort_values("total_weight", ascending=False))

agg_path = os.path.join(FILTERED_DIR, "aggregated_by_ids.csv")
agg.to_csv(agg_path, index=False)
print(f"✅ Saved aggregation → {agg_path}")
print("\nTop aggregated rows:")
print(agg.head(10).to_string())

print("\nDone with step 5.")
