#  Identifying Value Bets in Formula 1
### DSA 210 – Introduction to Data Science | Spring 2026

---

##  Project Overview

This project demonstrates the power of mathematical modeling in Formula 1 betting by building a machine learning system to predict race winners and podium finishers. By comparing model-derived **"Fair Value"** probabilities against market-implied probabilities from official F1 pre-race betting articles, the project identifies market inefficiencies and **Expected Value (EV)** betting opportunities.

The core hypothesis is that pre-race car telemetry data — collected from Friday Practice and Qualifying sessions — contains measurable signals that are systematically undervalued or overvalued by the betting market.

---

##  Objectives

- FastF1 telemetry data is used (qualifying lap times, top speeds, sector times) to build race outcome predictions
- Historical betting odds are scraped and calibrated from official F1 betting articles
- Apply **Logistic Regression** and **Random Forest** classification models trained on 2022–2024 data and tested on 2025
- Simulate an **Expected Value (EV) betting strategy** by comparing model probabilities with market-implied probabilities

---

##  Data Sources

### 1. Probabilistic (Betting Odds) Data
- **Source:** Official Formula 1 Betting Articles (published before each race weekend)
- **Method:** Web scraping with `BeautifulSoup` and `Selenium`
- **Coverage:** 2022–2025 seasons
- **Manual Enrichment:** Missing or corrupted data points were verified and corrected by hand to ensure data integrity, eliminating scraping artifacts

### 2. Car Telemetry Data
- **Source:** [`FastF1`](https://theoehrly.github.io/Fast-F1/) Python library
- **Sessions used:** Friday Practice & Qualifying
- **Key features:** Lap times, sector times, top speeds, compound used, gap to pole
- **Coverage:** 2022–2025 seasons

---

##  Methodology

### Probability Calibration (Overround Removal)
Raw betting odds contain a built-in bookmaker margin (overround). To extract true market-implied probabilities, the **Power Method** is applied:

1. **Convert odds to raw probabilities:**  
   $P_{raw} = \dfrac{1}{\text{Decimal Odds}}$

2. **Calculate overround:**  
   $\text{Overround} = \sum P_{raw}$ (typically 1.05–1.15 per race)

3. **Power scaling — solve for exponent $k$:**  
   $\sum \left(P_{raw}\right)^k = 1$

This yields calibrated "True Probabilities" for each driver per race.

### Machine Learning Models
| Model | Purpose |
|---|---|
| Logistic Regression | Baseline probabilistic classification |
| Random Forest | Non-linear feature interaction & feature importance |

- **Train set:** 2022–2024 seasons  
- **Test set:** 2025 season  
- **Targets:** Race Winner (binary), Top-3 Podium Finish (binary)

### Expected Value Simulation
Model-predicted probabilities are compared against calibrated market probabilities to flag positive EV opportunities:

$$EV = (P_{model} \times \text{Decimal Odds}) - 1$$

A bet is flagged as a **value bet** when $EV > 0$.

---

##  Hypothesis Testing

### Test 1 — Does Qualifying in the Top 3 Statistically Matter?
> **H₀:** Qualifying in the Top 3 has no effect on win probability  
> **Result:** Rejected — Qualifying in the Top 3 gives a statistically massive advantage in win probability  
> **T-Statistic:** 10.06 | **P-Value:** 9.76221e-20

### Test 2 — Does Straight-Line Speed Dictate Podium Probability?
> **H₀:** Top speed has no effect on podium probability  
> **Result:** Rejected — Top speed is a statistically significant indicator of podium probability  
> **Mann-Whitney U-Statistic:** 147428.00 | **P-Value:** 1.70940e-02

---

