#  Identifying Value Bets in Formula 1
### DSA 210 – Introduction to Data Science | Spring 2026

---

##  Project Overview

This project builds a machine learning system to predict F1 podium finishers and identify **Expected Value (EV)** betting opportunities. By comparing model derived probabilities — built from qualifying telemetry against bookmaker market odds, the project detects cases where the market systematically undervalues a driver's chances.

**Core hypothesis:** Prerace car telemetry data (grid position, qualifying time delta, top speed) contains measurable signals that the betting market fails to fully price in.

---

##  Repository Structure

| File | Description |
|---|---|
| `F1_EV_Analysis_Final.ipynb` | **Main analysis notebook** — complete pipeline from data to predictions |
| `F1_Master_Merged_Data.csv` | Merged dataset: telemetry + odds (2022–2024, 1340 rows) |
| `F1_2025_Grid_Quali_Speed_Data.csv` | 2025 qualifying telemetry from FastF1 |
| `F1_2025_Odds.numbers` | 2025 bookmaker odds (manually collected) |
| `odds_scraper.py` | Selenium scraper for F1 betting articles |
| `telemetry_extractor.py` | FastF1 data extraction script |
| `data_fixer.py` | Data cleaning and validation script |
| `DSA_210 Project Proposal.pdf` | Original project proposal |
| `index.html` | Project webpage (hosted via GitHub Pages) |
| `DSA210_Final_Report_Hakan_Taskin.docx` | Final written report |
| `AI_USAGE.md` | AI assistance disclosure |
| `requirements.txt` | Python dependencies |

---

##  How to Reproduce

```bash
pip install -r requirements.txt
jupyter notebook F1_EV_Analysis_Final.ipynb
```

Make sure `F1_Master_Merged_Data.csv`, `F1_2025_Grid_Quali_Speed_Data.csv`, and `F1_2025_Odds.numbers` are in the same directory as the notebook.

---

##  Data Sources

### 1. Race Results (Podium Labels)
- **Source:** [Jolpica API](https://api.jolpi.ca/) 
- **Method:** Fetched via `requests` — actual finishing positions for 2022–2024
- **Coverage:** 2022–2024 seasons (2022: 22 races, 2023: 22 races, 2024: 21 races)

### 2. Betting Odds
- **Source:** Official Formula 1 Betting Articles (published before each race weekend)
- **Method:** Web scraping with `BeautifulSoup` and `Selenium` (`odds_scraper.py`)
- **Coverage:** 2022–2025 seasons
- **Manual Enrichment:** Missing or corrupted values verified and corrected by hand

### 3. Car Telemetry
- **Source:** [`FastF1`](https://theoehrly.github.io/Fast-F1/) Python library
- **Sessions used:** Qualifying
- **Key features:** Grid position, gap to pole (seconds), speed trap top speed (km/h)
- **Coverage:** 2022–2025 seasons

---

##  Methodology

### Probability Calibration — Power Method
Raw bookmaker odds contain a built in margin (overround). To extract fair value probabilities:

$$P_{raw} = \frac{1}{\text{Decimal Odds}} \qquad \text{Find } k: \sum (P_{raw})^k = 1 \qquad P_{calibrated} = (P_{raw})^k$$

### Machine Learning Models

| Model | Role |
|---|---|
| Logistic Regression | Baseline — linear, interpretable |
| Random Forest | Non-linear — feature interactions, importance |
| Ensemble | Average of LR + RF predictions |

- **Train:** 2022–2023 seasons
- **Test:** 2024 season (true out of sample)
- **5-fold CV AUC:** LR 0.891 ± 0.028 · RF 0.886 ± 0.031

### Expected Value Simulation

$$\text{EV} = (P_{\text{model}} \times \text{Decimal Odds}) - 1$$

A bet is flagged as a **value bet** when EV > 0.05. Drivers with podium odds above 50 are excluded from EV calculation as these represent bookmaker field odds rather than individually priced probabilities. Precision on the 2024 test set: **27.48%** vs **15% true baseline** (3 podiums per 20 driver field) — **1.8× better than random**.

---

##  Hypothesis Testing

All features were tested for normality (Shapiro-Wilk) — results showed non normal distributions, so **Mann-Whitney U tests** were used throughout.

### H1 — Does Grid Position Predict Win Probability?
> **H₀:** No difference in calibrated win probability between Top 3 qualifiers and the rest  
> **Result:** ✅ **Rejected** — Top-3 qualifiers have significantly higher win probability  
> **Mann-Whitney U | p = 7.96e-23**

### H2 — Does Straight-Line Top Speed Predict Podium Outcome?
> **H₀:** No difference in top speed between podium and non podium drivers  
> **Result:** ❌ **Failed to Reject** — The ~1 km/h difference is not statistically significant  
> **Mann-Whitney U | p = 0.47**

### H3 — Does Qualifying Time Delta Predict Podium Outcome?
> **H₀:** No difference in time delta between podium and non podium drivers  
> **Result:** ✅ **Rejected** — Podium drivers are significantly closer to pole position  
> **Mann-Whitney U | p = 1.76e-66**

---

##  Key Results

| Metric | Value |
|---|---|
| Model AUC (2024 out of sample) | **0.9031** |
| PR-AUC (imbalanced metric) | **0.4785** |
| 2024 value bet precision | **27.48%** vs 15% baseline = **1.8× better** |
| 2025 value bets flagged | **127** across 24 races |
| Dominant feature (RF importance) | Grid Position (48%) |

---

##  Known Limitations

- **EV threshold:** 0.05 is a design choice, not statistically derived.
- **Odds scraper fragility:** Scraper depends on F1 betting article page structure — layout changes require manual intervention.
- **Missing 2024 rounds:** 3 rounds from the 2024 season were unavailable via the Jolpica API and were excluded from training.

---

##  Links

- [Project Webpage](https://hakanotaskin.github.io/DSA210-Project/)
- [Final Report](DSA210_Final_Report_Hakan_Taskin.docx)
- [AI Usage Disclosure](AI_USAGE.md)
