import time
import re
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

print("Starting Google Chrome via Selenium...")
chrome_options = Options()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
driver.execute_cdp_cmd('Network.setUserAgentOverride', {
    "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
})
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

def fractional_to_implied_prob(text: str | None) -> float | None:
    if not text: return None
    upper = text.strip().upper()
    if upper in ("EVS", "EVENS", "1/1"): return 50.0
    
    m_frac = re.search(r"(\d+)\s*/\s*(\d+)", upper)
    if m_frac:
        num, den = int(m_frac.group(1)), int(m_frac.group(2))
        return round(den / (num + den) * 100, 4) if (num + den) else None
        
    try:
        dec = float(upper)
        return round((1 / dec) * 100, 4) if dec > 0 else None
    except ValueError:
        return None


def parse_article_odds(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["nav", "footer", "script", "style", "aside", "header"]): 
        tag.decompose()
    
    rows_out = []
    text_blocks = soup.find_all(['p', 'li', 'h2', 'h3', 'h4'])
    
    current_category = "win" 
    seen_drivers = set()
    
    for block in text_blocks:
        text = block.get_text().replace('\xa0', ' ').strip()
        text_lower = text.lower()
        
        if len(text_lower) < 150:
            if 'podium' in text_lower or 'top three' in text_lower: 
                current_category = "podium"
            elif any(kw in text_lower for kw in ['pole', 'fastest lap', 'most points', 'qualifying', 'safety car']): 
                current_category = None
            elif 'win' in text_lower or 'victory' in text_lower: 
                current_category = "win"

        if current_category is None:
            continue
            
        chunks = [c.strip() for c in re.split(r'•|●|\n|<br/>', text) if c.strip()]
        
        for chunk in chunks:
            if len(chunk) > 150: continue 
                
            match = re.search(r'\b(\d+\s*/\s*\d+|\d+\.\d+|\d+|evens|evs)[.,\s]*$', chunk.lower())
            
            if match:
                odds_str = match.group(1)
                
                if odds_str in ["2022", "2023", "2024", "2025"]:
                    continue
                    
                found_codes = set()
                chunk_lower = chunk.lower()
                for name_key, code in DRIVER_NAME_MAP.items():
                    if re.search(rf'\b{re.escape(name_key)}\b', chunk_lower):
                        found_codes.add(code)
                        
                for code in found_codes:
                    if (code, current_category) not in seen_drivers:
                        seen_drivers.add((code, current_category))
                        rows_out.append({
                            "driver_code": code,
                            "race_win_odds": odds_str if current_category == "win" else None,
                            "podium_odds": odds_str if current_category == "podium" else None
                        })
                        
    return rows_out

def merge_driver_rows(rows: list[dict]) -> list[dict]:
    merged = {}
    for row in rows:
        code = row["driver_code"]
        if code not in merged: 
            merged[code] = row.copy()
        else:
            if row.get("race_win_odds"): merged[code]["race_win_odds"] = row["race_win_odds"]
            if row.get("podium_odds"): merged[code]["podium_odds"] = row["podium_odds"]
    return list(merged.values())

def extract_race_name(url):
    names = ["bahrain", "saudi", "australi", "japan", "miami", "monaco", "spain", "canad", "austria", "brit", "hungar", "belgi", "dutch", "ital", "singapore", "united-states", "mexic", "sao-paulo", "las-vegas", "qatar", "abu-dhabi", "azerbaijan", "emilia"]
    for n in names:
        if n in url: return n.capitalize() + " Grand Prix"
    return "Grand Prix"

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
        2025: [
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-for-the-season-opening-australian-grand.FovJxXkSiqOtcQ72FbX3T",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-heads-to-china-for-the-first.3Ka7hqJ3EA7hq71t3qO8bM",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-heads-to-japan.30YNiP5d6yHcPeYGtuzOK6",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-heads-to-bahrain.5pX2ddYhS5deZrZuW995lw",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-heads-to-saudi-arabia.7dOVcAJcOKCvMe7vQh4Vmy",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-the-sprint-returns-in-miami.qfK2LlwGMgvoZcsvzPtjn",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-moves-on-to-imola.1h2gDR88erNsNARX48npaT",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-hits-the-streets-of-monaco.7caQmT5Fu4yGlPnNRDCTFN",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-heads-to-spain.4H121O20IoSuzIdCgl86tQ",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-moves-on-to-canada.675ec1lRJmkLZBacGnvV8w",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-returns-to-europe-for-the.6rXPWNnfslibR2EJDOotCM",
            "https://www.formula1.com/en/latest/article/betting-guide-who-do-the-odds-favour-as-f1-arrives-at-silverstone-for-the.2ZvodOPKQW1uwum4cTbta1",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-the-sprint-returns-in-belgium.5wqu7kazFnEKgxA8oih6Fd",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-heads-to-the-streets-of-baku.6Xm7Nwu3Im3PHDFBoCmNe7",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-moves-on-to-singapore.5P5grfveA0dFk4s2iftREj",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-arrives-in-austin-for-the-united.1CA762jQOPgMWtne0VbuUe",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-arrives-for-the-mexico-city-grand.4DJqIrrzzDcfG3Yom4BjxX",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-heads-to-sao-paulo.11JS0a82dZ2y05akvIevy4",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-arrives-in-las-vegas.5NxbgHd4Zna6w2bk4wTQp6",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-for-the-qatar-grand-prix.7oVyx8DQ4onHm1s1ne9a52",
            "https://www.formula1.com/en/latest/article/betting-guide-who-are-the-favourites-as-f1-arrives-in-abu-dhabi-for-the.Ovn5gsOACFTonJoVWhwsq"
        ]
    }

    all_data = []
    
    try:
        print(f"Loaded {sum(len(urls) for urls in raw_urls.values())} URLs. Starting Master Scrape...")
        for year, urls in raw_urls.items():
            for url in urls:
                race_name = extract_race_name(url.lower())
                print(f"Scraping {year} {race_name}...")
                
                driver.get(url)
                time.sleep(3.5) 
                
                if "Just a moment" in driver.title:
                    print("🚨 Cloudflare caught us! You have 15 seconds to click the human box...")
                    time.sleep(15)
                
                html = driver.page_source
                raw_rows = parse_article_odds(html)
                merged_rows = merge_driver_rows(raw_rows)
                
                if merged_rows:
                    print(f"  -> Success: {len(merged_rows)} drivers found.")
                    for r in merged_rows:
                        r.update({"year": year, "race": race_name})
                        r["race_win_prob"] = fractional_to_implied_prob(r.get("race_win_odds"))
                        r["podium_prob"] = fractional_to_implied_prob(r.get("podium_odds"))
                        all_data.append(r)
                else:
                    print("  -> Failed: No odds matched in text.")

        if all_data:
            df = pd.DataFrame(all_data)
            
            cols = ["year", "race", "driver_code", "race_win_odds", "race_win_prob", "podium_odds", "podium_prob"]
            df = df[[c for c in cols if c in df.columns]]
            
            df.to_csv("F1_Master_Odds.csv", index=False)
            print(f"\n✅ FULL SUCCESS! Shape: {df.shape}")
        else:
            print("\n❌ Shape: (0, 0) - Check the parsing logic.")

    finally:
        driver.quit()
        print("Browser closed.")
