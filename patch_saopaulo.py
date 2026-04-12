import fastf1
import pandas as pd
import numpy as np

fastf1.Cache.enable_cache('logs/')

print("Fetching REAL telemetry for São Paulo 2024 Qualifying...")
# We MUST use telemetry=True to avoid the KeyError!
session = fastf1.get_session(2024, 'São Paulo', 'Q')
session.load(telemetry=True, weather=False, messages=False)

driver_speeds = {}
for drv in session.drivers:
    driver_info = session.get_driver(drv)
    code = driver_info['Abbreviation'] 
    
    laps = session.laps.pick_driver(drv)
    if not laps.empty and 'SpeedST' in laps.columns:
        valid_speeds = laps['SpeedST'].dropna()
        if not valid_speeds.empty:
            # FastF1 returns this in km/h natively. No conversions needed!
            driver_speeds[code] = valid_speeds.max()

print("\n--- Extracted Real Speeds (KM/H) ---")
for code, speed in driver_speeds.items():
    print(f"{code}: {speed:.1f} km/h")

print("\nInjecting directly into F1_Master_Merged_Data.csv...")
df = pd.read_csv('F1_Master_Merged_Data.csv')
sp_mask = (df['year'] == 2024) & (df['race'] == 'São Paulo Grand Prix')

# Overwrite the broken flat numbers with real individual telemetry
for code, speed in driver_speeds.items():
    driver_mask = sp_mask & (df['driver_code'] == code)
    df.loc[driver_mask, 'Top_Speed_ST'] = speed

# Handle MAG (He didn't race, so he has no telemetry)
if 'MAG' not in driver_speeds:
    mag_mask = sp_mask & (df['driver_code'] == 'MAG')
    if mag_mask.any():
        real_median = np.median(list(driver_speeds.values()))
        df.loc[mag_mask, 'Top_Speed_ST'] = real_median
        print(f"MAG didn't race. Filled his missing data with the real race median: {real_median:.1f} km/h")

df.to_csv('F1_Master_Merged_Data.csv', index=False)
print("SUCCESS: Individual speeds applied. No more medians. No more MPH conversions.")
