"""
data_fixer.py
=============
Standalone data cleaning script for F1_Master_Merged_Data.csv.
Run this script once after initial data collection to produce a
clean dataset ready for analysis in the main notebook.

Fixes applied:
  1. Negative Quali_Time_Delta values (sign flip during calculation)
  2. São Paulo 2024 Top_Speed_ST: mph → km/h unit conversion
  3. Impossible speed outliers (<280 or >370 km/h) → race median
  4. Missing Grid_Position → filled with 20 (last place), flag added
  5. Missing Quali_Time_Delta → filled with race maximum
  6. Missing podium_odds flag column added
  7. Hungary 2022 missing odds → manually filled from historical sources
"""

import pandas as pd
import numpy as np

# Load the raw merged dataset
df = pd.read_csv('F1_Master_Merged_Data.csv')

# ── Fix 1: Negative qualifying time deltas ─────────────────────────────────────
# Caused by a sign flip during delta calculation in telemetry_extractor.py.
# All deltas should be positive (gap to pole, in seconds).
df['Quali_Time_Delta'] = df['Quali_Time_Delta'].abs()
print("Fixed negative Quali Time Deltas using abs().")

# ── Fix 2: São Paulo 2024 speed trap — mph to km/h conversion ─────────────────
# FastF1 returned speed trap values in mph for this race instead of km/h.
# Multiply by 1.60934 to convert to the correct unit.
sp_24_mask = (df['year'] == 2024) & (df['race'] == 'São Paulo Grand Prix')
df.loc[sp_24_mask, 'Top_Speed_ST'] = df.loc[sp_24_mask, 'Top_Speed_ST'] * 1.60934
print("Converted São Paulo 2024 speeds from MPH to KM/H.")

# ── Fix 3: Impossible speed values ────────────────────────────────────────────
# F1 cars operate in the 280–370 km/h range at speed traps.
# Values outside this range are data errors; replace with the race median.
invalid_speed_mask = (df['Top_Speed_ST'] < 280) | (df['Top_Speed_ST'] > 370)
df.loc[invalid_speed_mask, 'Top_Speed_ST'] = np.nan
df['Top_Speed_ST'] = df.groupby(['year', 'race'])['Top_Speed_ST'].transform(
    lambda x: x.fillna(x.median())
)
print(f"Neutralized {invalid_speed_mask.sum()} impossible F1 speed outliers with Race Medians.")

# ── Fix 4: Missing grid position ──────────────────────────────────────────────
# Drivers who did not qualify (DNQ) have no grid position.
# Flag them with is_dnq=1, then fill with 20 (last position) so the
# feature remains usable in ML models.
df['is_dnq'] = df['Grid_Position'].isna().astype(int)
df['Grid_Position'] = df['Grid_Position'].fillna(20)

# ── Fix 5: Missing qualifying time delta ──────────────────────────────────────
# DNQ drivers have no delta to pole. Fill with the worst (maximum) delta
# observed in their race, which is a conservative but reasonable imputation.
df['Quali_Time_Delta'] = df.groupby(['year', 'race'])['Quali_Time_Delta'].transform(
    lambda x: x.fillna(x.max())
)

# ── Fix 6: Betting data availability flag ─────────────────────────────────────
# Some driver-race combinations have no odds data.
# Flag these rows so downstream analysis can filter or handle them separately.
df['has_betting_data'] = df['podium_odds'].notna().astype(int)

# ── Fix 7: Hungary 2022 missing odds ──────────────────────────────────────────
# The 2022 Hungarian Grand Prix odds were not captured by the scraper.
# Values below are sourced manually from archived F1 betting articles.
hungary_22_mask = (df['year'] == 2022) & (df['race'] == 'Hungarian Grand Prix')

df.loc[hungary_22_mask & df['driver_code'].isin(['RIC', 'ALO', 'NOR']),  'podium_odds'] = 13.0
df.loc[hungary_22_mask & df['driver_code'].isin(['MAG', 'MSC', 'TSU', 'BOT']), 'podium_odds'] = 51.0
df.loc[hungary_22_mask & (df['driver_code'] == 'ZHO'),                   'podium_odds'] = 201.0
df.loc[hungary_22_mask & df['driver_code'].isin(['STR', 'VET']),         'podium_odds'] = 601.0
df.loc[hungary_22_mask & df['driver_code'].isin(['ALB', 'LAT']),         'podium_odds'] = 901.0

# ── Save cleaned dataset ───────────────────────────────────────────────────────
df.to_csv('F1_Master_Merged_Data.csv', index=False)
print("\nSUCCESS: Dataset is perfectly sanitized and ready for Machine Learning.")
