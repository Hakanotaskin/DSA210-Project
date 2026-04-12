import pandas as pd

# 1. Load the broken dataset
df = pd.read_csv('F1_Master_Merged_Data.csv')

# 2. Identify the corrupted Hungarian GP 2022 rows
hungary_mask = (df['year'] == 2022) & (df['race'] == 'Hungarian Grand Prix')

# 3. Keep everything EXCEPT those rows
df_clean = df[~hungary_mask]

# 4. Save it back
df_clean.to_csv('F1_Master_Merged_Data.csv', index=False)
print(f"Removed {hungary_mask.sum()} corrupted rows. Your dataset is now safe.")

