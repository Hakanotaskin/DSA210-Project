import pandas as pd
import numpy as np

# Load the fresh data
df = pd.read_csv('F1_Master_Merged_Data.csv')

# --- FIX 1: The Negative Time Deltas ---
# Using .abs() immediately converts any negative gaps to positive
df['Quali_Time_Delta'] = df['Quali_Time_Delta'].abs()
print("Fixed negative Quali Time Deltas using abs().")

# --- FIX 2: São Paulo 2024 MPH to KM/H ---
sp_24_mask = (df['year'] == 2024) & (df['race'] == 'São Paulo Grand Prix')
# Convert the whole race to km/h
df.loc[sp_24_mask, 'Top_Speed_ST'] = df.loc[sp_24_mask, 'Top_Speed_ST'] * 1.60934
print("Converted São Paulo 2024 speeds from MPH to KM/H.")

# --- FIX 3: The Outlier Catch-All (Ocon & Norris) ---
# After conversion, NOR might be 434 km/h. OCO is stuck at 268 km/h. 
# Anything < 280 or > 370 is physically impossible. We replace them with the Race Median.
invalid_speed_mask = (df['Top_Speed_ST'] < 280) | (df['Top_Speed_ST'] > 370)
df.loc[invalid_speed_mask, 'Top_Speed_ST'] = np.nan
df['Top_Speed_ST'] = df.groupby(['year', 'race'])['Top_Speed_ST'].transform(lambda x: x.fillna(x.median()))
print(f"Neutralized {invalid_speed_mask.sum()} impossible F1 speed outliers with Race Medians.")

# --- FIX 4 & 5: The DNQ and Odds Handlers (From Yesterday) ---
df['is_dnq'] = df['Grid_Position'].isna().astype(int)
df['Grid_Position'] = df['Grid_Position'].fillna(20)
df['Quali_Time_Delta'] = df.groupby(['year', 'race'])['Quali_Time_Delta'].transform(lambda x: x.fillna(x.max()))
df['has_betting_data'] = df['podium_odds'].notna().astype(int)

# --- THE HUNGARIAN GP ODDS PATCH ---
hungary_22_mask = (df['year'] == 2022) & (df['race'] == 'Hungarian Grand Prix')
df.loc[hungary_22_mask & df['driver_code'].isin(['RIC', 'ALO', 'NOR']), 'podium_odds'] = 13.0
df.loc[hungary_22_mask & df['driver_code'].isin(['MAG', 'MSC', 'TSU', 'BOT']), 'podium_odds'] = 51.0
df.loc[hungary_22_mask & (df['driver_code'] == 'ZHO'), 'podium_odds'] = 201.0
df.loc[hungary_22_mask & df['driver_code'].isin(['STR', 'VET']), 'podium_odds'] = 601.0
df.loc[hungary_22_mask & df['driver_code'].isin(['ALB', 'LAT']), 'podium_odds'] = 901.0

# Save it
df.to_csv('F1_Master_Merged_Data.csv', index=False)
print("\nSUCCESS: Dataset is perfectly sanitized and ready for Machine Learning.")
