import pandas as pd
import numpy as np

# Load the dataset
df = pd.read_csv('F1_Master_Merged_Data.csv')

# 1. Target São Paulo 2024
sp_mask = (df['year'] == 2024) & (df['race'] == 'São Paulo Grand Prix')

# 2. Identify the MPH values (anything under 300 is definitely MPH)
mph_mask = sp_mask & (df['Top_Speed_ST'] < 300)

# Apply your exact conversion logic ONLY to the MPH values
df.loc[mph_mask, 'Top_Speed_ST'] = df.loc[mph_mask, 'Top_Speed_ST'] * 1.60934
print(f"Converted {mph_mask.sum()} MPH values to KM/H for São Paulo 2024.")

# 3. Clean up the MAG placeholder (or any other anomalies)
# If a speed is still exactly the old placeholder or physically impossible (>370), neutralize it
invalid_mask = sp_mask & ((df['Top_Speed_ST'] == 352.44546) | (df['Top_Speed_ST'] > 370))
df.loc[invalid_mask, 'Top_Speed_ST'] = np.nan

# Fill the neutralized value with the NEW, accurate race median
new_median = df.loc[sp_mask, 'Top_Speed_ST'].median()
df.loc[sp_mask, 'Top_Speed_ST'] = df.loc[sp_mask, 'Top_Speed_ST'].fillna(new_median)
print(f"Fixed {invalid_mask.sum()} placeholder(s) with the new race median: {new_median:.1f} km/h.")

# Save it back
df.to_csv('F1_Master_Merged_Data.csv', index=False)
print("SUCCESS: São Paulo speeds are now realistic F1 KM/H values.")
