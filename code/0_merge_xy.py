"""
0. Merge road OD data with XY coordinates.
Adapted for the light test dataset.
"""
import pandas as pd
import os

# ------------------------------------------------------------------
# Paths (all relative to pipeline_test)
# ------------------------------------------------------------------
BASE = r"E:\GitHub_BehtashSepahan"
# BASE = "/home/workdir/artifacts/pipeline_test"  # sandbox / test environment
INPUT = os.path.join(BASE, "input")
OUTPUT = os.path.join(BASE, "output", "1401")
os.makedirs(OUTPUT, exist_ok=True)

# ------------------------------------------------------------------
# 1. Load tajhizat (to filter only known commodities)
# ------------------------------------------------------------------
tajhizat = pd.read_excel(os.path.join(INPUT, "essential_tajhizat_commodity_load_and_unload.xlsx"))
print("tajhizat shape:", tajhizat.shape)
print("Sample commodity names from tajhizat:", tajhizat["commodity_name"].head(10).tolist())

# ------------------------------------------------------------------
# 2. Load the light test data
# ------------------------------------------------------------------
file_path = os.path.join(INPUT, "test_data_1401_light.csv")
columns_to_read = [
    "KALA_ID", "KALA_NAME", "GOROOH_KALA_NAME",
    "MABDA_OSTAN_NAME", "MABDA_SHAHR_NAME",
    "MAGHSAD_OSTAN_NAME", "MAGHSAD_SHAHR_NAME",
    "VAZN", "MASAFAT", "RECEIVENAME",
    # keep the ID columns we added
    "ORIGIN_PROVINCE_ID", "ORIGIN_CITY_ID",
    "DEST_PROVINCE_ID", "DEST_CITY_ID",
    "RECEIVE_CODE"
]

org_road_df = pd.read_csv(file_path, usecols=columns_to_read)
print("\nRaw test data shape:", org_road_df.shape)
print(org_road_df.head(3))

# ------------------------------------------------------------------
# 3. Filter to commodities that exist in tajhizat
# ------------------------------------------------------------------
matches = org_road_df["KALA_NAME"].isin(tajhizat["commodity_name"])
filtered_road_data = org_road_df[matches].copy()
print(f"\nAfter filtering by tajhizat commodity_name: {len(filtered_road_data)} rows "
      f"(dropped {len(org_road_df) - len(filtered_road_data)} unknown commodities)")

# ------------------------------------------------------------------
# 4. Load XY coordinates (our minimal test version)
# ------------------------------------------------------------------
road_od_just_xy_df = pd.read_excel(os.path.join(INPUT, "od_xy_test.xlsx"))
print("\nod_xy_test shape:", road_od_just_xy_df.shape)

# ------------------------------------------------------------------
# 5. Merge origin coordinates
# ------------------------------------------------------------------
merged_with_origin = pd.merge(
    filtered_road_data,
    road_od_just_xy_df,
    left_on=["MABDA_SHAHR_NAME"],
    right_on=["name"],
    how="left"
)
merged_with_origin = merged_with_origin.rename(columns={"X": "origin_x", "Y": "origin_y"})
merged_with_origin = merged_with_origin.drop(columns=["name"])

# ------------------------------------------------------------------
# 6. Merge destination coordinates
# ------------------------------------------------------------------
od_xy_merged = pd.merge(
    merged_with_origin,
    road_od_just_xy_df,
    left_on=["MAGHSAD_SHAHR_NAME"],
    right_on=["name"],
    how="left"
)
od_xy_merged = od_xy_merged.rename(columns={"X": "destination_x", "Y": "destination_y"})
od_xy_merged = od_xy_merged.drop(columns=["name"])

# ------------------------------------------------------------------
# 7. Diagnostics
# ------------------------------------------------------------------
print("\nFinal od_xy_merged shape:", od_xy_merged.shape)
print("Columns:", od_xy_merged.columns.tolist())
print("\nNAN counts:")
for col in ["origin_x", "origin_y", "destination_x", "destination_y"]:
    print(f"  {col}: {od_xy_merged[col].isna().sum()}")

print("\nSample rows:")
print(od_xy_merged[["KALA_ID", "KALA_NAME", "MABDA_SHAHR_NAME", "origin_x",
                    "MAGHSAD_SHAHR_NAME", "destination_x", "VAZN"]].head(8).to_string())

# ------------------------------------------------------------------
# 8. Save
# ------------------------------------------------------------------
out_path = os.path.join(OUTPUT, "road_od_with_xy.csv")
od_xy_merged.to_csv(out_path, index=False)
print(f"\n✅ Saved → {out_path}")
print("Done with step 0.")
