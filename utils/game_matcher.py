import asyncio
import httpx
import json
import sys
import urllib.parse
import time
import asyncio
from difflib import SequenceMatcher
from playwright.sync_api import sync_playwright
import os
# Configuration
AUTH_FILE = '../credentials/OOauth.json'
AUTH_FILE2 = '../credentials/HOSauth.json'
TARGET_URL = "https://app.opticodds.com/api/backend/screen/fixture-data?sport=basketball&market=moneyline&league=ncaab&_data=routes%2Fapi.backend.%24"

# Cookie filtering settings
IGNORE_PREFIXES = ['_ga', '_gid', '_fbp', '_hjid', 'intercom-', 'amplitude_', 'hubspot', 'mp_', '__cf', '_uetsid', '_uetvid']
KEEP_KEYWORDS = ['session', 'auth', 'token', 'id', 'user', 'jwt', 'xsrf', 'csrf']
master = []
master2 = []
page_count = 5

def load_auth_headers(AUTH_FILE):
    try:
        with open(AUTH_FILE, 'r') as f:
            data = json.load(f)

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Origin": "https://app.opticodds.com",
            "Referer": "https://app.opticodds.com/",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "*/*" 
        }

        if 'cookies' in data:
            raw_cookies = data['cookies']
            cookie_dict = {}
            if isinstance(raw_cookies, list):
                for item in raw_cookies:
                    if 'name' in item and 'value' in item:
                        cookie_dict[item['name']] = item['value']
            elif isinstance(raw_cookies, dict):
                cookie_dict = raw_cookies

            kept_cookies = []
            xsrf_token = None

            for name, value in cookie_dict.items():
                name_lower = name.lower()
                if 'xsrf' in name_lower or 'csrf' in name_lower:
                    xsrf_token = value
                    kept_cookies.append(f"{name}={value}")
                    continue
                if any(name_lower.startswith(prefix) for prefix in IGNORE_PREFIXES):
                    continue
                if any(key in name_lower for key in KEEP_KEYWORDS) or len(str(value)) < 200:
                    kept_cookies.append(f"{name}={value}")

            if kept_cookies:
                headers["Cookie"] = "; ".join(kept_cookies)
                if xsrf_token:
                    headers["X-XSRF-TOKEN"] = urllib.parse.unquote(xsrf_token)
                return headers
            else:
                print("Error: Cookie filter removed all cookies. Auth may fail.")
                sys.exit(1)
        else:
            print("Error: No 'cookies' key in auth.json")
            sys.exit(1)
    except Exception as e:
        print(f"Error loading auth: {e}")
        sys.exit(1)

def getGames(data):
    # Handle fixtures whether it's a list or a dictionary
    fixtures_raw = data.get("fixtures", {})
    if isinstance(fixtures_raw, dict):
        games = fixtures_raw.values()
    else:
        games = fixtures_raw

    for game in games:
        try:
            # Get Game ID
            game_id = game.get("id")

            # --- HANDLE HOME TEAM ---
            # Data structure is: "home_team": [{"id": "...", "name": "...", ...}]
            home_list = game.get("home_team", [])
            if home_list and len(home_list) > 0:
                home_data = home_list[0]
                home_team_id = home_data.get("id", "N/A")
                home = home_data.get("name", "Unknown")
                home_abbr = home_data.get("abbreviation", "UNK")
            else:
                home_team_id = "N/A"
                home = game.get("home_team_display", "Unknown")
                home_abbr = "UNK"

            # --- HANDLE AWAY TEAM ---
            away_list = game.get("away_team", [])
            if away_list and len(away_list) > 0:
                away_data = away_list[0]
                away_team_id = away_data.get("id", "N/A")
                away = away_data.get("name", "Unknown")
                away_abbr = away_data.get("abbreviation", "UNK")
            else:
                away_team_id = "N/A"
                away = game.get("away_team_display", "Unknown")
                away_abbr = "UNK"

            # Output Format:
            # [Game_ID, Home_ID, Home_Name, Home_Abbr, Away_ID, Away_Name, Away_Abbr]
            print([game_id, home_team_id, home, home_abbr, away_team_id, away, away_abbr])
            yield [home, away]
        except Exception as e:
            print(f"Error parsing game: {e}")

async def get_fixture_data():
    headers = load_auth_headers(AUTH_FILE)
    
    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        try:
            response = await client.get(TARGET_URL)
            
            if response.status_code == 200:
                data = response.json()
                master.extend(getGames(data))
            else:
                print(f"Error: Received status code {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"An error occurred: {e}")
  
# --------------------------------------------------------------------------------------------------------------------------------

from playwright.sync_api import sync_playwright
import json

# Initialize the master list globally so the handler can access it

def run_authenticated_session():
    
    # Base URL (removed the number at the end so we can add it dynamically)
    base_url = "https://backoffice-huddle.netlify.app/operations/events/book-events?client=Huddle&sport=cf64a1fd-9982-48f7-a2e4-0897cc8c668f&competition=d1303850-9f46-4ef3-bc0d-11e0b8477d69&page="
    filter = "&filter=eyJmaWVsZCI6Im1hdGNoU3RhdGUiLCJtb2RpZmllciI6ImluIiwidmFsdWUiOlsiUFJFTUFUQ0giLCJMSVZFIl0sImlucHV0VHlwZSI6InNlbGVjdCJ9"
    
    gql_endpoint = "https://gqls.phxp.huddle.tech/graphql"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=AUTH_FILE2)
        page = context.new_page()

        def handle_response(response):
            if gql_endpoint in response.url:
                try:
                    data = response.json()
                    # Only parse if the JSON contains the 'events' key
                    if "data" in data and "events" in data["data"]:
                        nodes = data["data"]["events"].get("nodes", [])
                        for node in nodes:
                            event_id = node.get("eventId")
                            competitors = node.get("competitors", [])
                            
                            home_team = next((c["name"] for c in competitors if c["side"] == "HOME"), "Unknown")
                            away_team = next((c["name"] for c in competitors if c["side"] == "AWAY"), "Unknown")
                            
                            print(f"ID: {event_id} | HOME: {home_team} | AWAY: {away_team}")
                            
                            # --- FIX: Used home_team/away_team instead of home/away ---
                            master2.append([home_team, away_team]) 
                except Exception:
                    pass 

        # Attach the listener
        page.on("response", handle_response)

        print(f"Logging in and starting scrape...")

        # --- PAGINATION LOOP ---
        # Change range(1, 4) to however many pages you want (e.g., 1 to 3)
        for i in range(1, 4):
            target_url = f"{base_url}{i}{filter}"
            print(f"Scraping Page {i}...")
            
            page.goto(target_url)
            
            # Wait 5 seconds on each page to allow the network request to fire and complete
            page.wait_for_timeout(5000)

        browser.close()


# ... Include your run_authenticated_session and get_fixture_data functions here ...

def get_similarity(a, b):
    """Returns a ratio between 0 and 1 of how similar two strings are."""
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()

def compare_fuzzy(api_list, scraped_list):
    print(f"\n--- FUZZY COMPARISON ---")
    print(f"API Games: {len(api_list)} | Scraped Games: {len(scraped_list)}")
    print("-" * 60)

    matches = []
    swaps = []
    unmatched_api = []
    
    # Work on a copy of scraped list so we can remove games as they are matched
    remaining_scraped = list(scraped_list)

    for api_game in api_list:
        api_h, api_a = api_game[0], api_game[1]
        
        best_score = 0
        best_match_index = -1
        match_type = "NONE" # can be DIRECT or SWAP

        # Loop through all remaining scraped games to find the best candidate
        for i, scr_game in enumerate(remaining_scraped):
            scr_h, scr_a = scr_game[0], scr_game[1]

            # 1. Check Normal Order: (API Home vs Scrape Home) + (API Away vs Scrape Away)
            score_normal = get_similarity(api_h, scr_h) + get_similarity(api_a, scr_a)
            
            # 2. Check Swapped Order: (API Home vs Scrape Away) + (API Away vs Scrape Home)
            score_swap = get_similarity(api_h, scr_a) + get_similarity(api_a, scr_h)

            # Determine the best fit for this specific scraped game
            # We look for a combined score > 1.2 (since max is 2.0)
            threshold = 1.1

            if score_normal > best_score and score_normal > threshold:
                best_score = score_normal
                best_match_index = i
                match_type = "DIRECT"
            
            elif score_swap > best_score and score_swap > threshold:
                best_score = score_swap
                best_match_index = i
                match_type = "SWAP"

        # --- PROCESS RESULT ---
        if best_match_index != -1:
            matched_game = remaining_scraped[best_match_index]
            
            if match_type == "SWAP":
                swaps.append((api_game, matched_game))
                print(f"⚠️  SWAP FOUND: API[{api_h} vs {api_a}]  <==>  SCRAPE[{matched_game[0]} vs {matched_game[1]}]")
            else:
                matches.append((api_game, matched_game))
                # Optional: Print matches to verify fuzzy logic is working
                # print(f"✅ Match: {api_h}/{api_a} == {matched_game[0]}/{matched_game[1]}")

            # Remove this game so it doesn't get matched again
            remaining_scraped.pop(best_match_index)
        else:
            unmatched_api.append(api_game)

    print("\n" + "="*30)
    print("       FINAL STATS       ")
    print("="*30)
    print(f"✅ Total Matches:      {len(matches)}")
    print(f"⚠️  Total Swaps:        {len(swaps)}")
    print(f"❌ Unmatched API:      {len(unmatched_api)}")
    print(f"❓ Scraped Leftover:   {len(remaining_scraped)}")
    print("="*30)

    if swaps:
        print("\n!!! ACTION REQUIRED: SWAPPED GAMES LIST !!!")
        for s in swaps:
            print(f"API: {s[0]} | SCRAPE: {s[1]}")
    
    if unmatched_api:
        print("\n--- Unmatched API Examples (Check for naming mismatch) ---")
        for u in unmatched_api[:5]: # Show first 5
            print(u)

# --------------------------------------------------------------------------------
# auth_setup.py
from playwright.sync_api import sync_playwright
import time
import re
AUTH_FILE2 = 'HOSauth.json'

def save_auth_state():
    # Define the file path for the authentication state    
    # Use 'with' to ensure the browser context is properly closed
    with sync_playwright() as p:
        # Launch the browser (Chromium is used by default)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("Starting authentication process...")
        
        # 1. Navigate to your website's login page
        page.goto('https://backoffice-huddle.netlify.app')

        # 2. Perform the login actions
        # Replace these locators and values with the ones specific to your site
        
        # page.fill('input[name="email"]', 'YOUR_USERNAME') 
        # page.fill('input[name="password"]', 'YOUR_PASSWORD') 
        # page.click('button:has-text("Sign In")')

        # 3. Wait for the page to navigate to a protected page after successful login
        # This is crucial to ensure the auth process is complete

        # print("You have 20 secs")
        # for i in range(20):
        #     time.sleep(1)
        print("waiting for not having login")
        page.wait_for_url(re.compile(r"^(?!.*login).*$"), timeout=1000000000000)

        # 4. Save the storage state (cookies and local storage) to the specified file
        context.storage_state(path=AUTH_FILE2)
        print(f"Authentication state successfully saved to {AUTH_FILE2}")

        # Close the browser
        browser.close()



def save_google_auth():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("1. Navigating to login page...")
        # FIX 1: Add wait_until="domcontentloaded"
        # This tells Playwright: "Don't wait for every background script to finish, just load the HTML."
        page.goto(
            "https://app.opticodds.com/screen/basketball/ncaab/market/total_points", 
            wait_until="domcontentloaded"
        ) 

        print("2. Clicking Google Login...")
        # FIX 2: Add force=True
        # This tells Playwright: "Click NOW, do not wait for the page to be stable."
        # We also explicitly wait for the button to be visible first.
        google_btn = page.locator("#oauth-google")
        google_btn.wait_for(state="visible", timeout=10000)
        google_btn.click(force=True)

        print("--- ACTION REQUIRED ---")
        print("Please manually log in to Google.")
        print("Script is waiting for the URL to contain 'main'...")

        # 3. Wait for the final URL (Success State)
        try:
            # Ensures we wait until the login is totally done
            page.wait_for_url("**/main**", timeout=0) 
        except Exception as e:
            print(f"Error waiting for URL: {e}")
            browser.close()
            return

        # 4. Save the state
        context.storage_state(path="auth.json")
        print("\nSUCCESS: Authentication captured and saved to 'auth.json'")
        
        browser.close()


if __name__ == "__main__":
    # Logins
    if AUTH_FILE2 not in os.listdir('.'):
        save_auth_state()
    if AUTH_FILE not in os.listdir('.'):
        save_google_auth()

    # 1. Run Scraper
    run_authenticated_session() # Populates master2
    
    # 2. Run API
    asyncio.run(get_fixture_data()) # Populates master
    
    # 3. Compare
    compare_fuzzy(master, master2)

    # os.remove(AUTH_FILE)
    # os.remove(AUTH_FILE2)
