import pandas as pd
import fastf1
import numpy as np
import os

# 1. Enable caching
if not os.path.exists('fastf1_cache'):
    os.makedirs('fastf1_cache')
fastf1.Cache.enable_cache('fastf1_cache')

# 2. Load your flawless financial data
print("Loading financial data...")
df = pd.read_csv('F1_Master_Merged_Data.csv')

# Create empty columns for our new physical features
df['Grid_Position'] = np.nan
df['Quali_Time_Delta'] = np.nan
df['Top_Speed_ST'] = np.nan

# 3. Get a unique list of races to download
races_to_fetch = df[['year', 'race']].drop_duplicates()
total_races = len(races_to_fetch)
print(f"Found {total_races} races to process. Beginning extraction...\n")

# 4. The Extraction Loop
for index, row in races_to_fetch.iterrows():
    year = row['year']
    race_name = row['race']
    print(f"Fetching: {year} {race_name} ({index + 1}/{total_races})")
    
    try:
        session = fastf1.get_session(year, race_name, 'Q')
        session.load(telemetry=True, weather=False, messages=False)
        results = session.results
        
        pole_time = results.iloc[0]['Q3'] if pd.notnull(results.iloc[0]['Q3']) else (results.iloc[0]['Q2'] if pd.notnull(results.iloc[0]['Q2']) else results.iloc[0]['Q1'])
        
        for driver_code in results['Abbreviation']:
            mask = (df['year'] == year) & (df['race'] == race_name) & (df['driver_code'] == driver_code)
            
            if mask.any():
                driver_data = results[results['Abbreviation'] == driver_code].iloc[0]
                df.loc[mask, 'Grid_Position'] = driver_data['Position']
                
                best_time = driver_data['Q3'] if pd.notnull(driver_data['Q3']) else (driver_data['Q2'] if pd.notnull(driver_data['Q2']) else driver_data['Q1'])
                if pd.notnull(best_time) and pd.notnull(pole_time):
                    delta = (best_time - pole_time).total_seconds()
                    df.loc[mask, 'Quali_Time_Delta'] = delta
                
                try:
                    fastest_lap = session.laps.pick_driver(driver_code).pick_fastest()
                    if pd.notnull(fastest_lap['SpeedST']):
                        df.loc[mask, 'Top_Speed_ST'] = fastest_lap['SpeedST']
                except Exception:
                    pass
                    
    except Exception as e:
        print(f"  [!] Could not load telemetry for {year} {race_name}. Error: {e}")

# 5. Save the final merged dataset
output_filename = 'F1_Master_Merged_Data.csv'
df.to_csv(output_filename, index=False)
print(f"\nSUCCESS! Data extraction complete. Saved as {output_filename}")
