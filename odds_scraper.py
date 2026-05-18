"""
odds_scraper.py
===============
Scrapes race win and podium odds from official Formula 1 betting articles.

For each race in the 2022-2025 seasons, the script:
  1. Opens the corresponding F1 betting article in Chrome via Selenium
  2. Parses the HTML to extract driver odds (fractional or decimal format)
  3. Converts odds to implied probabilities
  4. Saves the results to F1_Master_Odds.csv

Requirements:
  pip install selenium webdriver-manager beautifulsoup4 pandas

Usage:
  python odds_scraper.py
  (Chrome browser will open automatically)
"""

import time
import re
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

print("Starting Google Chrome via Selenium...")

# ── Chrome setup ───────────────────────────────────────────────────────────────
# Disable automation flags so F1.com does not detect and block the scraper
chrome_options = Options()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

# Spoof user agent to appear as a regular Chrome browser
driver.execute_cdp_cmd('Network.setUserAgentOverride', {
    "userAgent": ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/124.0.0.0 Safari/537.36')
})

# ── Driver name → FIA 3-letter code mapping ───────────────────────────────────
# Both full names and last names are included to handle varied article styles
DRIVER_NAME_MAP: dict[str, str] = {
    "max verstappen": "VER", "verstappen": "VER",
    "sergio perez": "PER", "perez": "PER", "checo perez": "PER",
    "lewis hamilton": "HAM", "hamilton": "HAM",
    "george russell": "RUS", "russell": "RUS",
    "charles leclerc": "LEC", "leclerc": "LEC",
    "carlos sainz": "SAI", "sainz": "SAI",
    "lando norris": "NOR", "norris": "NOR",
    "oscar piastri": "PIA", "piastri": "PIA",
    "fernando alonso": "ALO", "alonso": "ALO",
    "lance stroll": "STR", "stroll": "STR",
    "pierre gasly": "GAS", "gasly": "GAS",
    "esteban ocon": "OCO", "ocon": "OCO",
    "valtteri bottas": "BOT", "bottas": "BOT",
    "guanyu zhou": "ZHO", "zhou": "ZHO",
    "yuki tsunoda": "TSU", "tsunoda": "TSU",
    "nyck de vries": "DEV", "de vries": "DEV",
    "daniel ricciardo": "RIC", "ricciardo": "RIC",
    "kevin magnussen": "MAG", "magnussen": "MAG",
    "nico hulkenberg": "HUL", "hulkenberg": "HUL",
    "alexander albon": "ALB", "albon": "ALB",
    "logan sargeant": "SAR", "sargeant": "SAR",
    "mick schumacher": "MSC", "schumacher": "MSC",
    "sebastian vettel": "VET", "vettel": "VET",
    "nicholas latifi": "LAT", "latifi": "LAT",
    "oliver bearman": "BEA", "bearman": "BEA",
    "franco colapinto": "COL", "colapinto": "COL",
}


# ── Helper: convert fractional or decimal odds to implied probability ──────────
def fractional_to_implied_prob(text: str | None) -> float | None:
    """
    Convert odds string to implied probability (%).
    Handles:
      - Fractional format: "7/2" → 22.22%
      - Decimal format:    "4.5" → 22.22%
      - Evens:             "EVS" → 50.00%
    Returns None if the input cannot be parsed.
    """
    if not text:
        return None
    upper = text.strip().upper()

    # Handle "evens" / "EVS" special case
    if upper in ("EVS", "EVENS", "1/1"):
        return 50.0

    # Try fractional format (e.g. "7/2")
    m_frac = re.search(r"(\d+)\s*/\s*(\d+)", upper)
    if m_frac:
        num, den = int(m_frac.group(1)), int(m_frac.group(2))
        return round(den / (num + den) * 100, 4) if (num + den) else None

    # Try decimal format (e.g. "4.5")
    try:
        dec = float(upper)
        return round((1 / dec) * 100, 4) if dec > 0 else None
    except ValueError:
        return None


# ── Helper: parse odds from one article's HTML ────────────────────────────────
def parse_article_odds(html: str) -> list[dict]:
    """
    Extract driver odds from an F1 betting article HTML string.
    Scans paragraph and list elements for driver name + odds patterns.
    Tracks whether the current context is 'win' or 'podium' market.
    Returns a list of dicts: {driver_code, race_win_odds, podium_odds}.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove navigation, footer, and non-content elements
    for tag in soup.find_all(["nav", "footer", "script", "style", "aside", "header"]):
        tag.decompose()

    rows_out = []
    text_blocks = soup.find_all(['p', 'li', 'h2', 'h3', 'h4'])

    current_category = "win"   # default: race win market
    seen_drivers = set()       # prevent duplicate entries per market

    for block in text_blocks:
        text = block.get_text().replace('\xa0', ' ').strip()
        text_lower = text.lower()

        # Detect market context switch based on section headers
        if len(text_lower) < 150:
            if 'podium' in text_lower or 'top three' in text_lower:
                current_category = "podium"
            elif any(kw in text_lower for kw in
                     ['pole', 'fastest lap', 'most points', 'qualifying', 'safety car']):
                current_category = None   # irrelevant market — skip
            elif 'win' in text_lower or 'victory' in text_lower:
                current_category = "win"

        if current_category is None:
            continue

        # Split block into chunks and look for odds patterns
        chunks = [c.strip() for c in re.split(r'•|●|\n|<br/>', text) if c.strip()]

        for chunk in chunks:
            if len(chunk) > 150:
                continue   # too long to be a driver-odds line

            # Match an odds value at the end of the chunk
            match = re.search(
                r'\b(\d+\s*/\s*\d+|\d+\.\d+|\d+|evens|evs)[.,\s]*$',
                chunk.lower()
            )

            if match:
                odds_str = match.group(1)

                # Skip year numbers that match the pattern
                if odds_str in ["2022", "2023", "2024", "2025"]:
                    continue

                # Match driver names in the chunk
                found_codes = set()
                chunk_lower = chunk.lower()
                for name_key, code in DRIVER_NAME_MAP.items():
                    if re.search(rf'\b{re.escape(name_key)}\b', chunk_lower):
                        found_codes.add(code)

                # Record first occurrence per driver per market
                for code in found_codes:
                    if (code, current_category) not in seen_drivers:
                        seen_drivers.add((code, current_category))
                        rows_out.append({
                            "driver_code":    code,
                            "race_win_odds":  odds_str if current_category == "win" else None,
                            "podium_odds":    odds_str if current_category == "podium" else None
                        })

    return rows_out


# ── Helper: merge win and podium rows for the same driver ─────────────────────
def merge_driver_rows(rows: list[dict]) -> list[dict]:
    """
    Combine separate win and podium entries for the same driver into one row.
    If a driver appears twice (once per market), their odds are merged.
    """
    merged = {}
    for row in rows:
        code = row["driver_code"]
        if code not in merged:
            merged[code] = row.copy()
        else:
            if row.get("race_win_odds"):
                merged[code]["race_win_odds"] = row["race_win_odds"]
            if row.get("podium_odds"):
                merged[code]["podium_odds"] = row["podium_odds"]
    return list(merged.values())


# ── Helper: extract race name from URL ────────────────────────────────────────
def extract_race_name(url):
    """
    Derive a human-readable race name from the article URL slug.
    Used only for logging — not stored in the output CSV.
    """
    names = [
        "bahrain", "saudi", "australi", "japan", "miami", "monaco",
        "spain", "canad", "austria", "brit", "hungar", "belgi",
        "dutch", "ital", "singapore", "united-states", "mexic",
        "sao-paulo", "las-vegas", "qatar", "abu-dhabi", "azerbaijan", "emilia"
    ]
    for n in names:
        if n in url:
            return n.capitalize() + " Grand Prix"
    return "Grand Prix"


# ── Article URL list by season ────────────────────────────────────────────────
# One URL per race — official F1 betting guide articles published before each race
if __name__ == "__main__":

    raw_urls = {
        2022: [
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-bahrain-grand-prix-whos-favourite-to-win-the-first-race.24H3iX8BNvsPuCo0vY3ZoP",
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-saudi-arabian-grand-prix-are-ferrari-favourites-for.6qkhDX7wGU52enfOTmlFrO",
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-australian-grand-prix-who-are-the-favourites-in.15lV4g5qWJCK4pgNVuRL1c",
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-emilia-romagna-grand-prix-will-ferrari-shine-on-home.3HjWVBTKWCjwMbrJ5Nl7sZ",
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-miami-grand-prix-who-is-the-favourite-to-shine-in-the.50CwQuaczlUpAXpkaNLl9x",
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-spanish-grand-prix-who-is-favourite-for-the-win-in.32sGu4ZFuquSLvUfSJBKmO",
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-2022-monaco-grand-prix-who-might-prevail-around-the.64XByufLdrPydNhRnwe6Jy",
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-2022-azerbaijan-grand-prix-who-is-the-favourite-around.3kYz805FFD8Nk9l1f3p2Go",
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-canadian-grand-prix-who-are-the-favourites-as-f1.HGUMjG5jzvFSDsciqMKeP",
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-british-grand-prix-who-is-the-favourite-to-shine-at.2MatTdErSOggqPuzB0zzqU",
            "https://www.formula1.com/en/latest/article/betting-guide-what-are-the-odds-for-the-austrian-grand-prix-as-the-sprint.7cizysopqld7IleMyOIGeB",
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-french-grand-prix-who-are-the-favourites-at-paul-ricard.7rHpsNTu7rkmWZUTTnGQSp",
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-hungarian-grand-prix-who-are-the-favourites-in-budapest.376Txl5o2srsmYZJW2jTqk",
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-belgian-grand-prix-who-are-the-favourites-at-circuit-de.1sVkMw7HPXatBIyE86HSPD",
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-dutch-grand-prix-who-will-shine-the-brightest-in.6O7pS1qm03SjOdfUMOhix4",
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-italian-grand-prix-who-is-tipped-to-take-the-spoils-at.4SZkRlrHI3SQ1J5K9ukFN8",
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-singapore-grand-prix-who-is-set-to-star-in-f1s-return.76xT3eEXlHWW8vdO6ywxQh",
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-japanese-grand-prix-who-will-fly-high-on-formula-1s.4CHLyJaXbnpz6zEtcYCMdY",
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-united-states-grand-prix-who-are-the-favourites-to-star.2or7JaFfuXNxs82289USKQ",
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-mexico-city-grand-prix-will-verstappen-make-f1-history.5r6MJN6amIweg0AKfZTzUJ",
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-sao-paulo-grand-prix-who-looks-set-to-star-in-the-final.6O3dUNMhYoqjmpcmhgFHlr",
            "https://www.formula1.com/en/latest/article/betting-odds-for-the-abu-dhabi-grand-prix-who-are-the-favourites-for-the.pYiAFRXtpZJWqdB4XKUKy"
        ],
        2023: [
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-for-the-first-race-of-the-2023-season.4mi7RW0soEpFsTRMrWF3Jo",
            "https://www.formula1.com/en/latest/article/betting-guide-who-is-set-to-shine-brightest-under-the-lights-at-the-saudi.593BApoBZoAk5enaLt9EW8",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-to-shine-on-the-streets-of-melbourne.5X6YrYUU7tWT821fv7WbEW",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-to-star-on-the-streets-of-azerbaijan.14iUtrHb0Ovhn97bgHtRoN",
            "https://www.formula1.com/en/latest/article/betting-guide-whos-favourite-to-make-it-count-in-miami.457FVEnOp8UlnnyuskBrr2",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-to-star-on-the-streets-of-monte-carlo.34AB92IKJOfseEDZcTQzr7",
            "https://www.formula1.com/en/latest/article/betting-guide-who-could-upset-the-odds-in-barcelona.7L4ePOdXh2jbk0CWt2Qsrl",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-heads-to-canada.1CMGcY8iYXNF8jYHB7qhh0",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-to-shine-at-the-second-sprint-weekend.6HVSHDNs9xGsysPWWxuEWZ",
            "https://www.formula1.com/en/latest/article/betting-guide-how-the-odds-are-stacked-ahead-of-the-british-grand-prix.5gKZubD92rtfYl1wQRg84Y",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-heads-to-hungary.2M7EQKaFBWcBbbfih2HuOs",
            "https://www.formula1.com/en/latest/article/betting-guide-who-could-stop-red-bulls-record-breaking-run-in-belgium.1Phm4J6ERhBBaDnUiuOHjj",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-to-star-after-f1s-summer-break-in.5QcLvxrtWjKlQG1KPV3Ji4",
            "https://www.formula1.com/en/latest/article/betting-guide-who-could-excel-as-f1-returns-to-italy-and-the-temple-of-speed.3XCFVxTwKEgChBT9FWfC5T",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-to-light-up-marina-bay-as-f1-returns-to.3fSvDeN2Uq0A3pBeoBcRD0",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-for-the-win-in-the-land-of-the-rising.5UEgRGTfIkVpVbxE8pMWPl",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-returns-to-qatar.42GwMbgeftGOnc5VE96ms0",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-returns-to-the-united-states-for.1fA3vs72M5nw7CEhJbPY05",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-returns-to-mexico-city-for-the.2sENJPPDxbtollNP6Adfkp",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-heads-to-interlagos.2uffjMUu3nqeYuC512UhSt",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-to-shine-under-the-lights-at-the.1oeDk0MK5ArtP5sTkuQSlu"
        ],
        2024: [
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-for-the-season-opener-in-bahrain.4UosIz6SdyGAwyPxZjjo8J",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-heads-to-saudi-arabia-for-the.UkbWZA2g9dSOsXEMqMzbC",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-visits-australia-for-the-third.4RytOusgGYP6tcpQKFXKq",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-heads-to-japan-for-the-fourth.eru3CX4ZEcobkCpt8TPF4",
            "https://www.formula1.com/en/latest/article/betting-guide-who-looks-set-to-shine-at-the-first-sprint-of-the-season-in.zy5NOK4qlvLhqSfZau6k8",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-heads-to-miami-for-another-sprint.20SiBWBausoLYewi06XPqe",
            "https://www.formula1.com/en/latest/article/betting-guide-imola-2024-emilia-romagna-grand-prix.3F43SqCS9qRSc83n4Hye58",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-heads-to-monaco.5y4m4xZD9FcsF5Dr9EEmOv",
            "https://www.formula1.com/en/latest/article/betting-guide-who-is-tipped-to-make-their-mark-in-montreal.41oOYFOyxFX7WlgNMqVEb5",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-returns-to-europe-for-the-spanish.2joOsXigevRHN71LUEF9vl",
            "https://www.formula1.com/en/latest/article/betting-guide-who-do-the-odds-favour-as-the-sprint-returns-in-austria.3iQrUO65R6TMZxhSlHtBLZ",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-heads-to-silverstone.4AYLVUu3Qmwll0WYkOjXFm",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-heads-to-hungary-2024.rNnmIayAEGJE4et5vkjwE",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-heads-to-belgium-for-the-final.5PSR1z03uJG4DnnCQCpU1p",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-returns-to-action-in-zandvoort.4kVOcEIHP4eXRipvvsrZYk",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-reaches-the-ferrari-heartland-of.74K5RGpZqDE4uMkrrKvTOn",
            "https://www.formula1.com/en/latest/article/betting-guide-who-do-the-odds-favour-as-f1-heads-to-baku-azerbaijan-grand-prix.53HooDyRVpnUY8rs520D9s",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-heads-to-singapore.3VjJ7FnULZ0rdNRRDUvgvC",
            "https://www.formula1.com/en/latest/article/betting-guide-who-do-the-odds-favour-as-the-sprint-returns-in-austin.3sjvwzzgTvzY0VUzx4Qqq6",
            "https://www.formula1.com/en/latest/article/betting-guide-who-do-the-odds-favour-as-f1-heads-to-mexico.2oyzwc8baCQp5XGa4OIkEr",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-heads-to-sao-paulo-for-another.4tqpoK3HV8QL5ee1coz1me",
            "https://www.formula1.com/en/latest/article/betting-guide-who-is-favourite-to-hit-the-jackpot-under-the-las-vegas-lights.3CUnBCPPc9RsdHyKapoifF",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-heads-to-qatar-for-the.3zdQfi2enEmghiUm3ZjQeV",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-to-end-their-season-on-a-high-in-abu.7v5jG3U2siKlZVzc7m3D7d"
        ],
        # 2025 odds were collected manually and stored in F1_2025_Odds.numbers.
        # The scraper was not used for 2025 due to changes in the F1.com article
        # page structure that prevented reliable automated parsing.
    }

    all_data = []

    try:
        total_urls = sum(len(urls) for urls in raw_urls.values())
        print(f"Loaded {total_urls} URLs. Starting Master Scrape...")

        for year, urls in raw_urls.items():
            for url in urls:
                race_name = extract_race_name(url.lower())
                print(f"Scraping {year} {race_name}...")

                driver.get(url)
                time.sleep(3.5)  # wait for page to fully render

                # Handle Cloudflare bot detection prompt
                if "Just a moment" in driver.title:
                    print("Cloudflare detected — 15 seconds to complete the challenge...")
                    time.sleep(15)

                html = driver.page_source
                raw_rows = parse_article_odds(html)
                merged_rows = merge_driver_rows(raw_rows)

                if merged_rows:
                    print(f"  -> Success: {len(merged_rows)} drivers found.")
                    for r in merged_rows:
                        r.update({"year": year, "race": race_name})
                        # Convert raw odds strings to implied probabilities
                        r["race_win_prob"] = fractional_to_implied_prob(r.get("race_win_odds"))
                        r["podium_prob"]   = fractional_to_implied_prob(r.get("podium_odds"))
                        all_data.append(r)
                else:
                    print("  -> Failed: No odds matched in text.")

        # Save all collected odds to CSV
        if all_data:
            df = pd.DataFrame(all_data)
            cols = ["year", "race", "driver_code",
                    "race_win_odds", "race_win_prob",
                    "podium_odds",   "podium_prob"]
            df = df[[c for c in cols if c in df.columns]]
            df.to_csv("F1_Master_Odds.csv", index=False)
            print(f"\nFULL SUCCESS! Shape: {df.shape}")
        else:
            print("\nShape: (0, 0) — Check the parsing logic.")

    finally:
        # Always close the browser, even if an error occurs
        driver.quit()
        print("Browser closed.")
