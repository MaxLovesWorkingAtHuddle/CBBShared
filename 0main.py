import asyncio
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from urllib.parse import urlparse, parse_qs
# import subprocess
import sys
from playwright.sync_api import sync_playwright
import time
import re
# Add utils directory to path for imports
import argparse

parser = argparse.ArgumentParser(description="Parsing the things")
# action='store_true' automatically sets the value to True if the flag is present, and False otherwise
parser.add_argument('-n', '--noAuth', action='store_true', help="Don't test auth states")
parser.add_argument('-a', '--auto', action='store_true', help="Auto Move Sliders")
parser.add_argument('-c', '--checkIds', action='store_true', help="Check match_games.json for ids")
parser.add_argument('-g', '--getIds', action='store_true', help="Get match_games.json")
parser.add_argument('-i', '--inMem', action='store_true', help="Use memory instead of files for storing json.")
# 3. Parse the command-line arguments
args = parser.parse_args()

if args.inMem:
    utilsStr = 'utilsIM'
else:
    utilsStr = 'utils'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), utilsStr))
import final_stretch3qpartial
import calcbias2parital
import argparse
# import timeit
import sendbias
from _matcher import run_matcher
import _matcher2
# TODO, Ensure that calcbias checks the under and the over, the home and away, the spread for and against. 
# ensure that we don't do funky stuff with the spraed normalization logic in calcbias https://gemini.google.com/app/5ad7a03b6968f69d
# TODO change the 0.04 back to 0.06
# use the python debugger for ur shiz
# check all hos ids are there in matchedgames
# TODO: bias for the total is displaying positive percentage for higher total. is this right? 
# TODO: Take out juice
# TODO: Injest L-sports
# TODO: FIX THE SPREAD LOGIC/Ensure it works properly
# Add auto limited offer.
# 1/17/26 adding ignore.txt
# 1/24/26 adding _matcher.py and _matcher2.py
# TODO: refresh OO screens
# 1/31/26 wow changed parsing logic to optic odds api.
# TODO: make the team_names js just get from matched_games.json
# BUG: Matching games on optic and HOS is bad again. 


# --- CONFIGURATION ---
# Define file paths relative to the main script location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OO_AUTH = os.path.join(BASE_DIR, 'credentials', 'OOauth.json')
HOS_AUTH = os.path.join(BASE_DIR, 'credentials', 'HOSauth.json')
ODDS_DUMP_JSON = os.path.join(BASE_DIR, utilsStr, 'odds_dump.json')
# OpticOdds URLs for different markets
OPTIC_ODDS_URLS = {
    "moneyline": "https://app.opticodds.com/screen/basketball/ncaab/market/moneyline",
    "point_spread": "https://app.opticodds.com/screen/basketball/ncaab/market/point_spread",
    "total_points": "https://app.opticodds.com/screen/basketball/ncaab/market/total_points",
}

# HOS Screen URL (multiview)
HOS_SCREEN_URL = "https://backoffice-huddle.netlify.app/operations/trading-ui/multiview?ids=aa59775b-113b-44e4-9ac7-af4638cfac1c&ids=ad9205fa-2232-437d-949a-fdfa291d5706&ids=dd5ac78a-09eb-4acb-af5f-0a5474b5378f&ids=0e52105d-cb4b-4f53-85c8-0798586cb05a&ids=66f997ec-0fbf-4670-8386-7b143b729074&ids=776a9878-adab-4fd6-ba4d-33b89242ddb2&ids=df2b2b54-a707-4c29-9385-2ddaba0c61e4&ids=60281fbd-88c2-4334-9f0c-620672194024&ids=c3707c1a-697e-41ea-add6-c46e836fea42&ids=c092cb19-0c84-4fd8-92cf-144986efca4e&ids=f9014cbf-ac4b-4ce7-aa0b-72a63b759b79&ids=82112c2f-5b4a-4bcc-a26e-e2a0f69ae6c4&ids=396cb15c-9e71-46d9-b178-2e3cab9fbc06&ids=2e8ec261-6151-455b-8be3-f26f69ac9b5a&ids=1d5c8135-7a52-40f3-aecf-eb4266ce69fe&ids=a97ec0f4-2c07-4fd7-be4b-e3f441ebca3b&ids=920d6fcd-aa35-4b61-9a37-ecbe0bf3be22&ids=4f90071b-013a-4ae7-8f7a-875b9d8ee593&ids=96318cde-a016-4563-9d39-2d6e4d58670a&ids=b9b31d13-5a0e-4db8-85f2-49b86b80a5e3&ids=b194d5b9-83e0-42e5-9b48-b13f2d9a2dba&ids=d3b62949-86f4-4ab8-8582-a27d7d65df75&ids=3d7db612-5332-4989-bd55-7062b49a38b0&ids=df9d5363-cec0-4ac2-b103-16e1a0ece1f7&ids=1948385c-73a8-44a1-a2be-88fc6d03b677&ids=f1ee93b6-fc6e-4899-ab5c-5d1be2b44327&ids=52e59dad-1ffc-4b58-a326-a8fd77959020&client=Huddle"
current_datetime = datetime.now()
HOS_GRAPHQL_ENDPOINT = "gqls.phxp.huddle.tech/graphql"

# --- JAVASCRIPT & QUERIES ---

# Import your existing JS strings here (assuming they exist in the environment)
from parse_jss import EXTRACT_TOTALS_JS, EXTRACT_MONEYLINE_JS, EXTRACT_SPREAD_JS, EXTRACT_TEAM_NAMES_JS, HOS_GRAPHQL_QUERY


EXTRACTION_JS_MAP = {
    "moneyline": EXTRACT_MONEYLINE_JS,
    "point_spread": EXTRACT_SPREAD_JS,
    "total_points": EXTRACT_TOTALS_JS,
}

HOS_GRAPHQL_QUERY = HOS_GRAPHQL_QUERY




# authenticated_session.py used to check that the HOSauth.json file works to login


def run_authenticated_session():
    # 1. Define the file path for the saved authentication state
    HOS_AUTH = os.path.join(BASE_DIR, 'credentials', 'HOSauth.json')
    
    # Define the URL of the protected page you want to access
    # Use the full URL including https://
    protected_url = 'https://backoffice-huddle.netlify.app/dashboard' # Example Protected Page URL
    End_url = "https://backoffice-huddle.netlify.app/operations/events/book-events?client=Huddle"
    with sync_playwright() as p:
        # Launch the browser. Set headless=False so you can watch it open!
        browser = p.chromium.launch(headless=False)
        
        # 2. IMPORTANT: Create a new context and load the storage_state from the file
        context = browser.new_context(storage_state=HOS_AUTH)
        page = context.new_page()

        print(f"Loading session state from {HOS_AUTH}...")
        
        # 3. Navigate to the protected page
        # Playwright will use the cookies/local storage loaded from HOSauth.json
        # and should bypass the login page.
        page.goto(protected_url)
        print(f"The hope is that you get redirected to {End_url}")
        page.wait_for_url(End_url, timeout = 3000)
        global HOS_Logged_In 
        HOS_Logged_In = True
        print(f"Navigated to {protected_url}. Check the browser to confirm login.")
        # Optional: Keep the browser open briefly so you can visually verify
        print("Browser will close in 3 seconds...")
        page.wait_for_timeout(3000)
        browser.close()

# auth_setup.py

HOS_AUTH = os.path.join(BASE_DIR, 'credentials', 'HOSauth.json')

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
        context.storage_state(path=HOS_AUTH)
        # logging.DEBUG("Auth for HOS captured")

        print(f"Authentication state successfully saved to {HOS_AUTH}")

        # Close the browser
        browser.close()

def checkAuthStatesHOS():
    try: 
        run_authenticated_session()
    except:
        save_auth_state()
    




def save_google_auth():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("1. Navigating to login page...")
        # FIX 1: Add wait_until="domcontentloaded"
        # This tells Playwright: "Don't wait for every background script to finish, just load the HTML."
        page.goto(
            "https://app.opticodds.com/screen/tab/-1?sport=basketball&league=ncaab&market=main", 
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
            page.wait_for_url("**=main**", timeout=0)
        except Exception as e:
            print(f"Error waiting for URL: {e}")
            # logging.DEBUG("You took too long to login")
            browser.close()
            return

        # 4. Save the state
        context.storage_state(path=f"{OO_AUTH}")
        # logging.DEBUG("Auth for OO captured")
        print(f"\nSUCCESS: Authentication captured and saved to '{OO_AUTH}'")
        browser.close()


def use_auth():
    # check if auth.json exists first
    if not os.path.exists(OO_AUTH):
        raise Exception(f"Error: '{OO_AUTH}' (Supposed to be the auth file for optic) not found. Please run the save_auth script first.")
        # return

    with sync_playwright() as p:
        # You can change headless=True to run this invisibly in the background
        browser = p.chromium.launch(headless=False)
        
        # 1. Create context using the saved storage state
        # This injects your cookies/local storage immediately
        context = browser.new_context(storage_state=OO_AUTH)
        
        page = context.new_page()

        print("Navigating to OpticOdds (authenticated)...")
        
        # 2. Go directly to the deep link
        page.goto("https://app.opticodds.com/screen/basketball/ncaab/market/total_points")

        # 3. Verification
        # If login failed, the URL would usually bounce back to /login
        page.wait_for_load_state("domcontentloaded")
        global OO_Logged_In
        OO_Logged_In = True # todo this is kinda dumb to just do a domcontentloaded, but wtvr
        
        if "login" not in page.url:
            print("SUCCESS: You are logged in!")
            print(f"Current Page: {page.title()}")
        else:
            print("FAILURE: redirected to login. The session might have expired.")

        # Keep browser open for 5 seconds so you can see it
        page.wait_for_timeout(5000)
        browser.close()
def checkAuthStatesOO():
    try: 
        use_auth()
    except:
        save_google_auth()


class MultiPageOddsMonitor:
    """
    Multi-page Playwright orchestrator for monitoring odds across OpticOdds and HOS.
    """
    
    def __init__(self, oo_auth_file: str = OO_AUTH, hos_auth_file: str = HOS_AUTH):
        self.oo_auth_file = oo_auth_file
        self.hos_auth_file = hos_auth_file
        
        self.playwright = None
        self.browser: Browser = None
        
        # Separate contexts for different auth states
        self.oo_context: BrowserContext = None
        self.hos_context: BrowserContext = None
        
        # OpticOdds pages (one per market)
        self.optic_pages: Dict[str, Page] = {}
        self.team_names = None
        
        # HOS page
        self.hos_page: Page = None
        self.captured_hos_headers = None # <-- Store headers here
        
        # Data storage
        self.last_extraction: Dict[str, Any] = {}

    async def _handle_hos_request(self, request):
        """Intercepts HOS network requests to find valid API headers."""
        # Only capture if we haven't already, or if we want to keep them fresh
        # Check if this request is going to the target GraphQL API
        if HOS_GRAPHQL_ENDPOINT in request.url and request.method == "POST":
            # Just print once to avoid spam
            if self.captured_hos_headers is None:
                print(f"🕵️  Captured outgoing HOS request to: {request.url}")
                
                headers = request.headers
                
                # Clean headers: remove content-length/host/connection to avoid conflicts
                clean_headers = {k: v for k, v in headers.items() 
                               if k.lower() not in ['content-length', 'host', 'connection']}
                
                self.captured_hos_headers = clean_headers
                print("✅ HOS API Headers secured!")

    async def start(self, headless: bool = False):
        """Initialize Playwright and open all browser pages."""
        print("🚀 Starting Multi-Page Odds Monitor...")
        print("="*60)
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        
        # Create OpticOdds context
        if os.path.exists(self.oo_auth_file):
            self.oo_context = await self.browser.new_context(storage_state=self.oo_auth_file)
        else:
            self.oo_context = await self.browser.new_context()
        
        # Create HOS context
        if os.path.exists(self.hos_auth_file):
            self.hos_context = await self.browser.new_context(storage_state=self.hos_auth_file)
        else:
            self.hos_context = await self.browser.new_context()
        
        # Open OpticOdds pages
        print("\n📊 Opening OpticOdds pages...")
        for market_name, url in OPTIC_ODDS_URLS.items():
            page = await self.oo_context.new_page()
            await page.goto(url, wait_until="domcontentloaded")
            self.optic_pages[market_name] = page
            print(f"   ✅ {market_name}")
        
        # Open HOS page
        print("\n🏠 Opening HOS page...")
        self.hos_page = await self.hos_context.new_page()
        
        # --- KEY CHANGE: Attach Listener BEFORE Navigation ---
        self.hos_page.on("request", self._handle_hos_request)
        
        await self.hos_page.goto(HOS_SCREEN_URL, wait_until="domcontentloaded")
        print(f"   ✅ HOS Page Loaded. Waiting for headers...")
        
        print("\n" + "="*60)
        print("🎉 All pages initialized.")
        return self
    
    async def wait_for_pages_ready(self, timeout_seconds: int = 10):
        """Wait for all pages to be fully loaded and HOS headers to be captured."""
        print(f"\n⏳ Waiting for pages ready & headers (max {timeout_seconds}s)...")
        
        # Wait for OpticOdds selectors
        for market_name, page in self.optic_pages.items():
            try:
                await page.wait_for_selector('.ag-center-cols-container [role="row"]', timeout=5000)
            except:
                pass # Proceed even if selector miss, will retry later

        # Wait for HOS Headers
        for i in range(timeout_seconds):
            if self.captured_hos_headers:
                print("   ✅ HOS Headers are ready.")
                break
            await asyncio.sleep(1)
            if i % 5 == 0: print("   ...waiting for HOS network activity...")
            
        return True
    
    async def extract_from_page(self, page: Page, market_name: str) -> Dict[str, Any]:
        """Extract odds data from a single OpticOdds page."""
        try:
            js_code = EXTRACTION_JS_MAP.get(market_name, EXTRACT_TOTALS_JS)
            data = await page.evaluate(js_code)
            
            if data:
                game_ids = list(data.keys())
                # team_names = await page.evaluate(EXTRACT_TEAM_NAMES_JS, game_ids)
                team_names = self.team_names
                return {
                    "market": market_name,
                    "event_count": len(data),
                    "events": data,
                    "team_names": team_names
                }
            return {"market": market_name, "event_count": 0, "events": {}}
            
        except Exception as e:
            return {"market": market_name, "error": str(e)}

    async def _fetch_hos_api_data(self):
        """Internal method to fetch HOS data using captured headers."""
        
        # --- RETRY LOGIC / WAITING FOR HEADERS ---
        if not self.captured_hos_headers:
            print("⚠️ Headers missing. Waiting for HOS network activity...")
            # If headers are missing, we wait up to 10 seconds for the listener to catch them
            # This handles the case where a reload was just triggered
            for _ in range(10):
                if self.captured_hos_headers:
                    print("✅ Headers re-acquired!")
                    break
                await asyncio.sleep(1)
            
            # If still no headers after waiting, force a reload and return None (will try next loop)
            if not self.captured_hos_headers:
                print("❌ Still no headers. Reloading page to force request...")
                await self.hos_page.reload(wait_until="domcontentloaded")
                return None

        # 1. Parse IDs from current URL
        parsed_url = urlparse(self.hos_page.url)
        query_params = parse_qs(parsed_url.query)
        raw_ids = query_params.get("ids", [])
        target_ids = []
        for item in raw_ids:
            target_ids.extend(item.split(','))
            
        # Safety check: If URL has no IDs, we can't fetch anything
        if not target_ids:
            print("⚠️ No IDs found in HOS URL. Cannot query API.")
            return None

        # 2. Construct Payload
        payload = {
            "operationName": "multiviewEvents",
            "variables": {
                "orderBy": ["STARTS_AT_ASC"],
                "filter": {"eventId": {"in": target_ids}},
                "condition": {}
            },
            "query": HOS_GRAPHQL_QUERY
        }

        # 3. Send Request using captured headers via the Context API
        try:
            response = await self.hos_context.request.post(
                f"https://{HOS_GRAPHQL_ENDPOINT}",
                headers=self.captured_hos_headers,
                data=payload,
                timeout=6000  # <--- INCREASED TO 6 SECONDS
            )

            if response.ok:
                data = await response.json()
                return data
            else:
                print(f"❌ HOS API Failed: {response.status} {response.status_text}")
                
                # Only reload if it's an Auth error (401/403)
                if response.status in [401, 403]:
                    print("🔄 Token likely expired. Reloading...")
                    self.captured_hos_headers = None
                    await self.hos_page.reload(wait_until="domcontentloaded")
                
                return None

        except Exception as e:
            error_msg = str(e)
            if "Timeout" in error_msg:
                print(f"⚠️ HOS Request Timed Out (Limit 60s). Skipping this cycle.")
                # Do NOT reload page on timeout, just return None so the loop continues
                return None
            else:
                print(f"❌ HOS API Exception: {error_msg}")
                # For other connection errors, maybe headers are stale
                if "ECONNRESET" in error_msg:
                     self.captured_hos_headers = None
                return None

    async def extract_hos_data(self) -> Dict[str, Any]:
        """Extract data from HOS page using the captured API method."""
        try:
            # Use the API fetcher instead of JS injection
            api_data = await self._fetch_hos_api_data()
            
            if api_data is None:
                api_data = {}
                
            return {
                "source": "HOS",
                "timestamp": datetime.now().isoformat(),
                "data": api_data
            }
        except Exception as e:
            print(f"❌ Error extracting HOS data: {e}")
            return {"source": "HOS", "error": str(e)}
    
    async def extract_all(self) -> Dict[str, Any]:
        """Extract data from all pages."""
        # Parallel extraction
        tasks = [self.extract_from_page(p, m) for m, p in self.optic_pages.items()]
        tasks.append(self.extract_hos_data())
        
        results = await asyncio.gather(*tasks)
        
        # Separate HOS result (last one) from OO results
        hos_data = results.pop()
        oo_data = {res["market"]: res for res in results}
        
        self.last_extraction = {
            "timestamp": datetime.now().isoformat(),
            "optic_odds": oo_data,
            "hos": hos_data
        }
        return self.last_extraction
    async def monitor_loop(self, interval_seconds: int = 7):
        print(f"\n📊 Starting loop (Interval: {interval_seconds}s). Ctrl+C to stop.")
        
        # Making team_names
        # 1. Read the list data from the file
        with open(os.path.join(BASE_DIR, utilsStr, '1parsedOO.json'), "r") as optic:
            new_fixtures = json.load(optic)  # This loads the list of objects
        # 2. Transform the list into the dictionary format
        transformed_dict = {
            f"{item['oo_game_id']}": {
                "team1": item['oo_home'],
                "team2": item['oo_away'],
                "display": f"{item['oo_home']} vs {item['oo_away']}"
            }
            for item in new_fixtures
        }
        # 3. Overwrite the file with the new dictionary format
        # with open("1parsedOO.json", "w") as optic:
        #     json.dump(transformed_dict, optic, indent=2)

        print("File converted from list to dictionary successfully.")
        self.team_names = transformed_dict
        try:
            currTime = datetime.now()
            while True:
                data = await self.extract_all()
                
                # Simple Logging
                print(f"\n--- {datetime.now().strftime('%H:%M:%S')} ---")
                for m, d in data["optic_odds"].items():
                    print(f"OO {m}: {d.get('event_count',0)} events")
                
                # hos_data = data.get("hos") or {} # TODO Experimental handle bad startup
                # hos_events = len(hos_data.get("data", {}).get("data", {}).get("events", {}).get("nodes", []))
                # print(f"HOS: {hos_events} events")
                
                # Save
                with open(os.path.join(BASE_DIR, utilsStr, 'odds_dump.json'), "w") as f:
                    json.dump(data, f, indent=2)
                await asyncio.sleep(1)
                final_stretch3qpartial.runner()
                await asyncio.sleep(1)
                results : list = calcbias2parital.runner2()

                # print(results[0])
                await asyncio.sleep(0.5)
                if len(results) <1:
                    print("🔄 Token likely expired. Reloading... This error code is for results")
                    self.captured_hos_headers = None
                    await self.hos_page.reload(wait_until="domcontentloaded")
                # print(results)
                # for res in results:
                #     await sendbias.update_market_bias(self.hos_page, self.hos_context, str(res["hos_event_id"]), str(res["hos_market_id"]), round(res["new_bias"]/100,2))

                with open(os.path.join(BASE_DIR, utilsStr, 'ignored.txt'),"r") as i:
                    ignore = [a.split(" ") for a in i.read().splitlines()]
                if args.auto:
                    ignores = set()
                    for res in range(len(results)):
                        for i in ignore:
                            # Check if the team name (i[0]) is in the game string
                            if len(i) > 0 and i[0] in results[res]["game"]:
                                # Check if the market type matches
                                if len(i) > 1 and i[-1].lower() == results[res]["market"]:
                                    print(f"Ignoring {results[res]['game']}, {results[res]['market']}")
                                    ignores.add(res)
                    results = [element for index, element in enumerate(results) if index not in ignores]    
                # if args.auto:
                    sent = 0
                    for res in results:
                        # HOS bias value is decimal (e.g. 0.04 for +4%). Do not divide by 100.
                        # Avoid rounding to 2dp (0.01 == 1%) which can collapse real biases to 0.
                        try:
                            # if res["new_total_bias_decimal"] != res["existing_bias_decimal"] and res["status"] != "SUSPENDED":
                            if max(-0.05, min(res["new_total_bias_decimal"], 0.05)) != max(-0.05, min(res["existing_bias_decimal"], 0.05)) and res["status"] != "SUSPENDED":
                                await sendbias.update_market_bias(
                                self.hos_page,
                                self.hos_context,
                                str(res["hos_event_id"]),
                                str(res["hos_market_id"]),
                                float(res["new_total_bias_decimal"]),
                                ) 
                                sent += 1
                                await asyncio.sleep(0.2)
                        except Exception as e:
                                print(f"⚠️ Failed to send bias for {res['game']}: {e}")
                                # If it's a connection reset, headers might be stale
                                if "ECONNRESET" in str(e):
                                    self.captured_hos_headers = None
                                    await self.hos_page.reload(wait_until="domcontentloaded")

                    print(f"{sent=}")
                # print(str(res["hos_event_id"]), str(res["hos_market_id"]), float(res["new_total_bias_decimal"]))
                # we need the current bias. or we need it to be like the abs bias. yeah, just make it abs bias, also keep the relative bias. 
                if (datetime.now() - currTime).total_seconds() > 300: # 5 mins
                    for market_name, page in self.optic_pages.items():
                        await page.reload()
                    currTime = datetime.now()
                else: 
                    print(f"Page reload in {(300 - (datetime.now() - currTime).total_seconds()):.2f} seconds")
                await asyncio.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("Stopped.")

    async def close(self):
        print("\n🔒 Closing browser...")
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    async def IMmonitor_loop(self, interval_seconds: int = 7):
        print(f"\n📊 Starting loop (Interval: {interval_seconds}s). Ctrl+C to stop.")
        
        # Making team_names
        # 1. Read the list data from the file
        with open(os.path.join(BASE_DIR, utilsStr, '1parsedOO.json'), "r") as optic:
            new_fixtures = json.load(optic)  # This loads the list of objects
        # 2. Transform the list into the dictionary format
        
        transformed_dict = {
            f"{item['oo_game_id']}": {
                "team1": item['oo_home'],
                "team2": item['oo_away'],
                "display": f"{item['oo_home']} vs {item['oo_away']}"
            }
            for item in new_fixtures
        }
        # 3. Overwrite the file with the new dictionary format
        # with open("1parsedOO.json", "w") as optic:
        #     json.dump(transformed_dict, optic, indent=2)

        print("File converted from list to dictionary successfully.")
        self.team_names = transformed_dict


        with open(os.path.join(BASE_DIR,utilsStr, 'matched_games.json'), "r") as f:
            # with open('matched_games.json', 'r') as f:
            matched_games = json.load(f)
        
        try:
            currTime = datetime.now()
            while True:
                data = await self.extract_all()
                
                # Simple Logging
                print(f"\n--- {datetime.now().strftime('%H:%M:%S')} ---")
                for m, d in data["optic_odds"].items():
                    print(f"OO {m}: {d.get('event_count',0)} events")
                
                # hos_data = data.get("hos") or {} # TODO Experimental handle bad startup
                # hos_events = len(hos_data.get("data", {}).get("data", {}).get("events", {}).get("nodes", []))
                # print(f"HOS: {hos_events} events")
                
                # Save
                # with open(os.path.join(BASE_DIR, utilsStr, 'odds_dump.json'), "w") as f:
                #     json.dump(data, f, indent=2)
                await asyncio.sleep(1)
                consolidated_odds_all_books = final_stretch3qpartial.runner(data,matched_games)
                await asyncio.sleep(1)
                results : list = calcbias2parital.runner2(consolidated_odds_all_books)

                # print(results[0])
                await asyncio.sleep(0.5)
                if len(results) <1:
                    print("🔄 Token likely expired. Reloading... This error code is for results")
                    self.captured_hos_headers = None
                    await self.hos_page.reload(wait_until="domcontentloaded")
                # print(results)
                # for res in results:
                #     await sendbias.update_market_bias(self.hos_page, self.hos_context, str(res["hos_event_id"]), str(res["hos_market_id"]), round(res["new_bias"]/100,2))

                with open(os.path.join(BASE_DIR, utilsStr, 'ignored.txt'),"r") as i:
                    ignore = [a.split(" ") for a in i.read().splitlines()]
                if args.auto:
                    ignores = set()
                    for res in range(len(results)):
                        for i in ignore:
                            # Check if the team name (i[0]) is in the game string
                            if len(i) > 0 and i[0] in results[res]["game"]:
                                # Check if the market type matches
                                if len(i) > 1 and i[-1].lower() == results[res]["market"]:
                                    print(f"Ignoring {results[res]['game']}, {results[res]['market']}")
                                    ignores.add(res)
                    results = [element for index, element in enumerate(results) if index not in ignores]    
                # if args.auto:
                    sent = 0
                    for res in results:
                        # HOS bias value is decimal (e.g. 0.04 for +4%). Do not divide by 100.
                        # Avoid rounding to 2dp (0.01 == 1%) which can collapse real biases to 0.
                        try:
                            # if res["new_total_bias_decimal"] != res["existing_bias_decimal"] and res["status"] != "SUSPENDED":
                            if max(-0.05, min(res["new_total_bias_decimal"], 0.05)) != max(-0.05, min(res["existing_bias_decimal"], 0.05)) and res["status"] != "SUSPENDED":
                                await sendbias.update_market_bias(
                                self.hos_page,
                                self.hos_context,
                                str(res["hos_event_id"]),
                                str(res["hos_market_id"]),
                                float(res["new_total_bias_decimal"]),
                                ) 
                                sent += 1
                                await asyncio.sleep(0.2)
                        except Exception as e:
                                print(f"⚠️ Failed to send bias for {res['game']}: {e}")
                                # If it's a connection reset, headers might be stale
                                if "ECONNRESET" in str(e):
                                    self.captured_hos_headers = None
                                    await self.hos_page.reload(wait_until="domcontentloaded")

                    print(f"{sent=}")
                # print(str(res["hos_event_id"]), str(res["hos_market_id"]), float(res["new_total_bias_decimal"]))
                # we need the current bias. or we need it to be like the abs bias. yeah, just make it abs bias, also keep the relative bias. 
                if (datetime.now() - currTime).total_seconds() > 300: # 5 mins
                    for market_name, page in self.optic_pages.items():
                        await page.reload()
                    currTime = datetime.now()
                else: 
                    print(f"Page reload in {(300 - (datetime.now() - currTime).total_seconds()):.2f} seconds")
                await asyncio.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("Stopped.")

    async def close(self):
        print("\n🔒 Closing browser...")
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


async def main():
    monitor = MultiPageOddsMonitor()
    try:
        await monitor.start(headless=False)
        await monitor.wait_for_pages_ready()
        # matchIds: dict = monitor.matchIds()
        # Interactive loop
        print("\nCommands: [Enter] Extract, [m] Monitor, [q] Quit")
        while True:
            cmd = await asyncio.get_event_loop().run_in_executor(None, input, "> ")
            if cmd.lower() == 'q': break
            elif cmd.lower() == 'm': 
                if args.inMem:
                    await monitor.IMmonitor_loop()
                else:
                    await monitor.monitor_loop()
            else:
                res = await monitor.extract_all()
                print("Extracted.")
    finally:
        await monitor.close()
async def run_matcher_helpers():
    result = await run_matcher(pages=5)    

if __name__ == "__main__":
    HOS_Logged_In  = False
    OO_Logged_In = False
    Login_Attempts = 1
    Login_AttemptsOO = 1
    
    
    # matrixAnimation() # by Nik


    if not args.noAuth:
        checkAuthStatesHOS()
        while not HOS_Logged_In:
            print(f"Let\'s Try That Again. Login Attempt {Login_Attempts}", 5, 0.009, False, 50, 25)
            Login_Attempts += 1
            checkAuthStatesHOS()
        print('HOS ACCSESED', 5, 0.01, False, 50, 25)

        Login_AttemptsOO = 1
        checkAuthStatesOO()
        while not OO_Logged_In:
            print(f"Let\'s Try That Again. Login Attempt {Login_AttemptsOO}", 5, 0.009, False, 50, 25)
            Login_AttemptsOO += 1
            checkAuthStatesOO()
        print('Optic Odds ACCSESED', 5, 0.01, False, 50, 25)
    if args.getIds:
        asyncio.run(run_matcher_helpers())
    if args.checkIds:
        # _matcher.main()
        _matcher2.main(HOS_SCREEN_URL)
    asyncio.run(main())