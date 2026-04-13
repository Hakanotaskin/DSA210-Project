import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import scipy.stats as stats


print("Loading Merged Data...")
df = pd.read_csv('F1_Master_Merged_Data.csv')


print("\n--- Generating EDA Plots ---")

plt.figure(figsize=(10, 8))

numeric_cols = ['race_win_prob', 'podium_prob', 'Grid_Position', 'Quali_Time_Delta', 'Top_Speed_ST']
sns.heatmap(df[numeric_cols].corr(), annot=True, cmap='coolwarm', fmt=".2f")
plt.title("Correlation: Car Physics vs. True Probabilities")
plt.tight_layout()
plt.savefig('Correlation_Heatmap.png')
print("Saved Correlation_Heatmap.png")

plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='Grid_Position', y='race_win_prob', alpha=0.6, color='blue')
plt.title("How Grid Position Dictates Financial Probability")
plt.xlabel("Qualifying Grid Position (1 = Pole)")
plt.ylabel("True Win Probability")
plt.gca().invert_xaxis() # Invert so Pole is on the right
plt.grid(True, linestyle='--', alpha=0.7)
plt.savefig('Grid_vs_Probability.png')
print("Saved Grid_vs_Probability.png")


print("\n--- Running Statistical Hypothesis Tests ---")


print("\nTEST 1: Does qualifying in the Top 3 statistically matter?")
top_3 = df[df['Grid_Position'] <= 3]['race_win_prob'].dropna()
midfield = df[(df['Grid_Position'] >= 4) & (df['Grid_Position'] <= 10)]['race_win_prob'].dropna()

t_stat, p_value = stats.ttest_ind(top_3, midfield, equal_var=False)

print(f"T-Statistic: {t_stat:.2f}")
print(f"P-Value: {p_value:.5e}")
if p_value < 0.05:
    print("Conclusion: Reject H0. Qualifying in the Top 3 gives a statistically massive advantage in win probability.")
else:
    print("Conclusion: Fail to reject H0.")

print("\nTEST 2: Does straight-line speed dictate podium probability?")

df['Speed_Rank'] = df.groupby(['year', 'race'])['Top_Speed_ST'].rank(ascending=False)

fast_straight = df[df['Speed_Rank'] <= 5]['podium_prob'].dropna()
slow_straight = df[df['Speed_Rank'] > 5]['podium_prob'].dropna()

u_stat, p_value_u = stats.mannwhitneyu(fast_straight, slow_straight, alternative='greater')

print(f"Mann-Whitney U-Stat: {u_stat:.2f}")
print(f"P-Value: {p_value_u:.5e}")
if p_value_u < 0.05:
    print("Conclusion: Reject H0. Top speed is a statistically significant indicator of podium probability.")
else:
    print("Conclusion: Fail to reject H0. Top speed alone does not guarantee a podium.")
    
print("\nAnalysis Complete! Check your folder for the new PNG graphs.")
