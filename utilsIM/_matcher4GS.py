import asyncio
import json
import os
from playwright.async_api import async_playwright
import csv
# Old
# # --- Configuration ---
# HOS_AUTH_FILE = "../credentials/HOSauth.json"
# HOS_BASE_URL = "https://backoffice-huddle.netlify.app/operations/events/book-events?client=Huddle&sport=cf64a1fd-9982-48f7-a2e4-0897cc8c668f&competition=d1303850-9f46-4ef3-bc0d-11e0b8477d69"
# HOS_GQL_ENDPOINT = "https://gqls.phxp.huddle.tech/graphql"
# PAGES_TO_SCRAPE = 8  # Adjust as needed
# OUTPUT_FILE = "2parsedHOS.json"


# Get the directory of the current file (_matcher4GS.py), which is 'utils'
UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (CBB1)
BASE_DIR = os.path.dirname(UTILS_DIR)

# Construct absolute paths
HOS_AUTH_FILE = os.path.join(BASE_DIR, "credentials", "HOSauth.json")
OUTPUT_FILE = os.path.join(UTILS_DIR, "2parsedHOS.json")
CSV_OUTPUT_FILE = os.path.join(UTILS_DIR, "output.csv")

HOS_BASE_URL = "https://backoffice-huddle.netlify.app/operations/events/book-events?client=Huddle&sport=cf64a1fd-9982-48f7-a2e4-0897cc8c668f&competition=d1303850-9f46-4ef3-bc0d-11e0b8477d69"
HOS_GQL_ENDPOINT = "https://gqls.phxp.huddle.tech/graphql"
PAGES_TO_SCRAPE = 8  # Adjust as needed


async def ensure_hos_auth():
    """Checks for HOS auth file and triggers login if missing."""
    if not os.path.exists(HOS_AUTH_FILE):
        print(f"Auth file {HOS_AUTH_FILE} missing. Opening browser for manual login...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto('https://backoffice-huddle.netlify.app')
            
            print("Please log in. The script will save state once you leave the login page.")
            # Wait for navigation away from login (up to 5 minutes)
            await page.wait_for_url(lambda url: "login" not in url.lower(), timeout=300000)
            await context.storage_state(path=HOS_AUTH_FILE)
            print(f"Auth saved to {HOS_AUTH_FILE}")
            await browser.close()

async def scrape_hos():
    await ensure_hos_auth()
    
    all_parsed_games = []
    
    async with async_playwright() as p:
        # Launching headless=True for efficiency, change to False to debug
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=HOS_AUTH_FILE)
        page = await context.new_page()

        async def handle_response(response):
            if HOS_GQL_ENDPOINT in response.url:
                try:
                    data = await response.json()
                    # Drill down into the Huddle GraphQL structure
                    events = data.get("data", {}).get("events", {}).get("nodes", [])
                    for node in events:
                        comps = node.get("competitors", [])
                        home = next((c for c in comps if c.get("side") == "HOME"), {})
                        away = next((c for c in comps if c.get("side") == "AWAY"), {})
                        
                        all_parsed_games.append({
                            'hos_event_id': node.get("eventId"),
                            'hos_home': home.get("name", "Unknown"),
                            'hos_home_id': home.get("teamId", "N/A"),
                            'hos_home_cid': home.get("competitorId", "N/A"),
                            'hos_away': away.get("name", "Unknown"),
                            'hos_away_id': away.get("teamId", "N/A"),
                            'hos_away_cid': away.get("competitorId", "N/A")
                        })
                except Exception:
                    pass

        # Attach the listener to capture background API traffic
        page.on("response", handle_response)
        
        print(f"Starting scrape for {PAGES_TO_SCRAPE} pages...")
        for i in range(1, PAGES_TO_SCRAPE + 1):
            url = f"{HOS_BASE_URL}&page={i}"
            print(f"Scraping Page {i}...")
            await page.goto(url)
            # Short wait to allow GraphQL requests to fire and resolve
            await page.wait_for_timeout(3000) 

        await browser.close()

    # Deduplicate by event_id
    unique_data = {g['hos_event_id']: g for g in all_parsed_games}.values()
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(list(unique_data), f, indent=2)
    
    print(f"Successfully saved {len(unique_data)} games to {OUTPUT_FILE}")

async def makeurl():
    import csv
    import json
    # 1. Added encoding='utf-8' to handle special characters in the source
    with open("2parsedHOS.json", "r", encoding='utf-8') as f1:
        data = json.load(f1)
        
        if data:
            headers = data[0].keys()

            # 2. Added encoding='utf-8' here to prevent the 'charmap' crash
            with open('output.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
                
            print("Successfully wrote output.csv")
        else:
            print("JSON file was empty or list was empty.")
async def makeurl():
    # 1. Added encoding='utf-8' to handle special characters in the source
    if not os.path.exists(OUTPUT_FILE):
        print(f"Error: {OUTPUT_FILE} does not exist.")
        return

    with open(OUTPUT_FILE, "r", encoding='utf-8') as f1:
        data = json.load(f1)
        
        if data:
            headers = data[0].keys()

            # 2. Added encoding='utf-8' here to prevent the 'charmap' crash
            with open(CSV_OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
                
            print(f"Successfully wrote {CSV_OUTPUT_FILE}")
        else:
            print("JSON file was empty or list was empty.")
if __name__ == "__main__":
    asyncio.run(scrape_hos())
    print("ZZZZ... 3 secs")
    asyncio.run(makeurl())
    print("Go to output.csv. Copy paste.")
