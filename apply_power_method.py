import pandas as pd
import numpy as np
from scipy.optimize import minimize

print("Loading F1_Master_Odds_Final.csv...")
df = pd.read_csv('F1_Master_Odds_Final.csv')


df['raw_win'] = df['race_win_odds'].apply(lambda x: 1/x if x > 0 else 0)
df['raw_podium'] = df['podium_odds'].apply(lambda x: 1/x if x > 0 else 0)


def find_optimal_k(implied_probs, target_sum):
    probs = implied_probs[implied_probs > 0] 
    if len(probs) == 0: return 1.0
    
    def objective(k):
        return (np.sum(probs ** k) - target_sum) ** 2
        

    res = minimize(objective, 1.0, bounds=[(0.5, 3.0)])
    return res.x[0]

print("Calculating True Probabilities for all races...")
processed_races = []


for (year, race), group in df.groupby(['year', 'race']):
    race_df = group.copy()

    win_k = find_optimal_k(race_df['raw_win'], 1.0)
    race_df['true_win_prob'] = race_df['raw_win'].apply(lambda x: (x ** win_k) if x > 0 else 0)
    

    podium_k = find_optimal_k(race_df['raw_podium'], 3.0)
    race_df['true_podium_prob'] = race_df['raw_podium'].apply(lambda x: (x ** podium_k) if x > 0 else 0)
    
    processed_races.append(race_df)


final_df = pd.concat(processed_races)


final_df = final_df.drop(columns=['raw_win', 'raw_podium'])
final_df['true_win_prob'] = final_df['true_win_prob'].round(4)
final_df['true_podium_prob'] = final_df['true_podium_prob'].round(4)


final_df['race_win_prob'] = final_df['true_win_prob']
final_df['podium_prob'] = final_df['true_podium_prob']
final_df = final_df.drop(columns=['true_win_prob', 'true_podium_prob'])


output_file = 'F1_Master_Odds_ML_Ready.csv'
final_df.to_csv(output_file, index=False)

print("\n--- DATASET COMPLETE ---")
print(f"Removed bookmaker margins from {len(df['race'].unique())} unique races.")
print(f"Saved pristine financial data as: {output_file}")
