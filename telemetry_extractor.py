"""
telemetry_extractor.py
======================
Extracts qualifying session telemetry from the FastF1 API for all races
in the master dataset (2022-2024 seasons).

For each race, the script fetches:
  - Grid_Position:     Final qualifying grid position (1 = pole)
  - Quali_Time_Delta:  Driver's best lap time minus pole time (seconds)
  - Top_Speed_ST:      Speed trap top speed from the driver's fastest lap (km/h)

The results are written directly back to F1_Master_Merged_Data.csv,
overwriting any existing telemetry columns.

Requirements:
  pip install fastf1 pandas numpy

Usage:
  python telemetry_extractor.py
  (First run will download and cache session data — may take a while)
"""

import pandas as pd
import fastf1
import numpy as np
import os

# ── FastF1 local cache setup ───────────────────────────────────────────────────
# Caching avoids re-downloading session data on subsequent runs.
# The cache folder is created automatically if it does not exist.
if not os.path.exists('fastf1_cache'):
    os.makedirs('fastf1_cache')
fastf1.Cache.enable_cache('fastf1_cache')

# ── Load existing dataset ──────────────────────────────────────────────────────
# The CSV is used to determine which race-driver combinations need telemetry.
# The telemetry columns are reset to NaN before extraction to ensure clean data.
print("Loading dataset...")
df = pd.read_csv('F1_Master_Merged_Data.csv')

# Reset telemetry columns — fresh extraction overwrites any previous values
df['Grid_Position']    = np.nan
df['Quali_Time_Delta'] = np.nan
df['Top_Speed_ST']     = np.nan

# ── Identify unique race-year combinations to process ─────────────────────────
races_to_fetch = df[['year', 'race']].drop_duplicates()
total_races = len(races_to_fetch)
print(f"Found {total_races} races to process. Beginning extraction...\n")

# ── Main extraction loop ───────────────────────────────────────────────────────
for index, row in races_to_fetch.iterrows():
    year      = row['year']
    race_name = row['race']
    print(f"Fetching: {year} {race_name} ({index + 1}/{total_races})")

    try:
        # Load qualifying session data from FastF1
        # telemetry=True is required to access SpeedST (speed trap values)
        # weather and messages are disabled to reduce download size
        session = fastf1.get_session(year, race_name, 'Q')
        session.load(telemetry=True, weather=False, messages=False)
        results = session.results

        # Determine pole time: use Q3 → Q2 → Q1 in order of availability
        # (some circuits use different qualifying formats)
        pole_time = (
            results.iloc[0]['Q3'] if pd.notnull(results.iloc[0]['Q3'])
            else results.iloc[0]['Q2'] if pd.notnull(results.iloc[0]['Q2'])
            else results.iloc[0]['Q1']
        )

        # ── Per-driver extraction ──────────────────────────────────────────────
        for driver_code in results['Abbreviation']:
            mask = (
                (df['year']        == year) &
                (df['race']        == race_name) &
                (df['driver_code'] == driver_code)
            )

            if not mask.any():
                continue  # driver not in our dataset — skip

            driver_data = results[results['Abbreviation'] == driver_code].iloc[0]

            # Grid position from qualifying results
            df.loc[mask, 'Grid_Position'] = driver_data['Position']

            # Qualifying time delta to pole (in seconds)
            # Use best available session time: Q3 → Q2 → Q1
            best_time = (
                driver_data['Q3'] if pd.notnull(driver_data['Q3'])
                else driver_data['Q2'] if pd.notnull(driver_data['Q2'])
                else driver_data['Q1']
            )
            if pd.notnull(best_time) and pd.notnull(pole_time):
                delta = (best_time - pole_time).total_seconds()
                df.loc[mask, 'Quali_Time_Delta'] = delta

            # Speed trap top speed from the driver's fastest qualifying lap
            # Wrapped in try/except — some drivers have no recorded laps (DNQ)
            try:
                fastest_lap = session.laps.pick_driver(driver_code).pick_fastest()
                if pd.notnull(fastest_lap['SpeedST']):
                    df.loc[mask, 'Top_Speed_ST'] = fastest_lap['SpeedST']
            except Exception:
                pass  # no telemetry available for this driver — leave as NaN

    except Exception as e:
        # Log the error and continue — one failed race should not stop the run
        print(f"  [!] Could not load telemetry for {year} {race_name}. Error: {e}")

# ── Save updated dataset ───────────────────────────────────────────────────────
output_filename = 'F1_Master_Merged_Data.csv'
df.to_csv(output_filename, index=False)
print(f"\nSUCCESS! Data extraction complete. Saved as {output_filename}")
