# F1 Betting Odds Scraper

A robust Selenium-based web scraper for extracting historical betting odds from Formula1.com articles for your DSA 210 project.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. What You Get

- **Selenium**: Handles Cloudflare blocking with a live browser
- **webdriver_manager**: Automatically manages ChromeDriver
- **BeautifulSoup**: Parses the rendered HTML to extract odds
- **Pandas**: Structures data and exports to CSV

## How It Works

1. **Selenium opens Chrome** and navigates to each Formula1.com article URL
2. **Waits 10 seconds** per page (solve any "I am not a robot" CAPTCHA during this time)
3. **BeautifulSoup extracts** all `<p>` and `<li>` tags from the rendered page
4. **Regex pattern matching** identifies driver names and decimal odds
5. **Handles common formats**: 
   - Single drivers: _"Hamilton 2.50"_
   - Multiple drivers: _"Verstappen, Russell, Norris 45.0"_  
   - Various bullet symbols: _•, ●_
6. **Exports to CSV**: `F1_Master_Odds.csv` with columns: Year, Race, Bet_Type, Driver, Decimal_Odds

## Usage

### Step 1: Add Your URLs

Edit `odds_scraper.py` and replace the `raw_urls` dictionary:

```python
raw_urls = {
    2022: [
        "https://www.formula1.com/en/latest/article/...",  # Replace with actual URLs
        "https://www.formula1.com/en/latest/article/...",
    ],
    2023: [
        # Add 2023 URLs here
    ]
}
```

### Step 2: Run the Script

```bash
python odds_scraper.py
```

### Step 3: Solve CAPTCHAs

When the script runs:
- Chrome will open automatically
- When you see the Cloudflare "Just a moment" screen, you have **10 seconds** to solve the CAPTCHA
- After 10 seconds, the script continues automatically (page will be fully loaded)

### Sample Output

```
Scraping: 2022 Bahrain Grand Prix...
   -> Loading URL: https://www.formula1.com/...
   -> Waiting 10 seconds... (solve CAPTCHA if prompted)
   -> Page Title: Betting Odds for the Bahrain Grand Prix...
   -> ✓ Success: Extracted 28 odds entries
   
...

✓ SUCCESS: Exported 142 odds to 'F1_Master_Odds.csv'
  Columns: Year, Race, Bet_Type, Driver, Decimal_Odds

Sample rows:
   Year               Race Bet_Type       Driver Decimal_Odds
0  2022  Bahrain Grand Prix      Win  Verstappen          2.50
1  2022  Bahrain Grand Prix      Win    Hamilton          5.00
2  2022  Bahrain Grand Prix   Podium      Sainz         12.50
```

## Features

✅ **Cloudflare-resistant**: Uses live browser rendering  
✅ **Manual CAPTCHA handling**: 10-second window for solving  
✅ **Robust driver detection**: 40+ historical F1 drivers  
✅ **Multi-driver parsing**: Handles 1+ drivers per line  
✅ **Race name extraction**: Automatically from URL  
✅ **Duplicate removal**: Cleans extracted data  
✅ **CSV export**: Structured format for analysis  

## Troubleshooting

### "Just a moment" page persists
- **Cause**: CAPTCHA wasn't solved in time  
- **Solution**: Increase the wait time in `scrape_targeted_odds()` (change `time.sleep(10)` to a higher value like 20)

### No odds extracted
- **Cause**: HTML structure differs from expected  
- **Solution**: Check BeautifulSoup is finding `<p>` and `<li>` tags. Add debugging:
  ```python
  print(soup.prettify()[:2000])  # Print first 2000 chars of HTML
  ```

### Chrome doesn't open
- **Cause**: ChromeDriver not installed correctly  
- **Solution**: webdriver_manager should handle this automatically, but try:
  ```bash
  pip install --upgrade webdriver-manager
  ```

### Memory issues
- **Cause**: Keeping browser open for many URLs  
- **Solution**: Script reuses a single driver, but if needed, adjust headless mode in `init_selenium_driver()`:
  ```python
  options.add_argument("--headless")  # Run browser in background
  ```

## Data Schema

**F1_Master_Odds.csv** contains:

| Column | Example | Description |
|--------|---------|-------------|
| Year | 2022 | Race year |
| Race | Bahrain Grand Prix | Race name |
| Bet_Type | Win or Podium | Type of betting odds |
| Driver | Verstappen | Driver name |
| Decimal_Odds | 2.50 | Decimal odds format |

## Notes for DSA 210

- This script respects Formula1.com's terms of service (uses realistic browser behavior)
- Data is for educational use in your university project
- Adjust `KNOWN_DRIVERS` list if you find drivers not being recognized
- Consider adding date headers if Formula1.com changes article timestamps

Good luck with your project! 🏎️
