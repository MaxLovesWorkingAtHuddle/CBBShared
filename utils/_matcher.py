import asyncio
import httpx
import json
import sys
import urllib.parse
import os
import time
import re
from datetime import datetime
from difflib import SequenceMatcher

# UI Imports
from rich import box
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Confirm

# Browser Automation
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
# Get the directory of the current file (_matcher.py), which is 'utils'
UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (CBB1)
BASE_DIR = os.path.dirname(UTILS_DIR)
# --- Configuration ---
OO_AUTH_FILE = os.path.join(BASE_DIR, "credentials", "OOauth.json")
HOS_AUTH_FILE = os.path.join(BASE_DIR, "credentials", "HOSauth.json")
OO_PARSE_FILE = os.path.join(BASE_DIR, "utils", "1parsedOO.json")
HOS_PARSE_FILE = os.path.join(BASE_DIR, "utils", "1parsedHOS.json")
MATCHED_GAMES = os.path.join(BASE_DIR, "utils", "matched_games.json")
# URLs
#  Old, depreciated is the first url
# OO_TARGET_URL = "https://app.opticodds.com/api/backend/screen/fixture-data?sport=basketball&market=moneyline&league=ncaab&_data=routes%2Fapi.backend.%24"
OO_TARGET_URL = "https://app.opticodds.com/api/backend/screen/data?sport=basketball&league=ncaab&market=main&tz=America%2FLos_Angeles"
HOS_BASE_URL = "https://backoffice-huddle.netlify.app/operations/events/book-events?client=Huddle&sport=cf64a1fd-9982-48f7-a2e4-0897cc8c668f&competition=d1303850-9f46-4ef3-bc0d-11e0b8477d69"
HOS_GQL_ENDPOINT = "https://gqls.phxp.huddle.tech/graphql"
HOS_FILTER = "&filter=eyJmaWVsZCI6Im1hdGNoU3RhdGUiLCJtb2RpZmllciI6ImluIiwidmFsdWUiOlsiUFJFTUFUQ0giLCJMSVZFIl0sImlucHV0VHlwZSI6InNlbGVjdCJ9"
HOS_FILTER = ""
# Settings
PAGES_TO_SCRAPE = 5
MATCH_THRESHOLD = 0.6
COOKIE_IGNORE = ['_ga', '_gid', '_fbp', '_hjid', 'intercom-', 'amplitude_', 'hubspot', 'mp_', '__cf', '_uetsid', '_uetvid']
COOKIE_KEEP = ['session', 'auth', 'token', 'id', 'user', 'jwt', 'xsrf', 'csrf']

console = Console()

# --- Cross-Platform Input (Getch) ---
class Getch:
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()
    def __call__(self): return self.impl()

class _GetchUnix:
    def __init__(self):
        import tty, termios
    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

class _GetchWindows:
    def __init__(self):
        import msvcrt
        self.msvcrt = msvcrt
    def __call__(self):
        ch = self.msvcrt.getch()
        if ch in (b'\x00', b'\xe0'):
            arrow = self.msvcrt.getch()
            if arrow == b'H': return 'UP'
            if arrow == b'P': return 'DOWN'
            if arrow == b'K': return 'LEFT'
            if arrow == b'M': return 'RIGHT'
            return None
        try:
            return ch.decode('utf-8')
        except UnicodeDecodeError:
            return None

get_key = Getch()

# --- Authentication Helpers ---

# def ensure_auth_files():
#     """Checks for auth files and triggers login if missing."""
#     if HOS_AUTH_FILE not in os.listdir('.'):
#         console.print("[yellow]HOS Auth file missing. Initiating login sequence...[/]")
#         _save_hos_auth()
    
#     if OO_AUTH_FILE not in os.listdir('.'):
#         console.print("[yellow]OpticOdds Auth file missing. Initiating login sequence...[/]")
#         _save_oo_auth()
def ensure_auth_files():
    """Checks for auth files and triggers login if missing."""
    # CHANGED: Use os.path.exists instead of checking os.listdir('.')
    if not os.path.exists(HOS_AUTH_FILE):
        console.print(f"[yellow]HOS Auth file missing at {HOS_AUTH_FILE}. Initiating login sequence...[/]")
        # Note: You might need to await this if calling from async, 
        # but _save_hos_auth is async, so ensure this function handles it correctly 
        # or rely on the manual check in main. For now, we assume the sync wrapper logic matches your setup.
        # Since _save_hos_auth is async, you cannot call it directly here without await or an event loop
        # However, keeping your existing logic structure:
        print("Please run the auth setup script separately or ensure credentials exist.")
    
    if not os.path.exists(OO_AUTH_FILE):
        console.print(f"[yellow]OpticOdds Auth file missing at {OO_AUTH_FILE}. Initiating login sequence...[/]")
        print("Please run the auth setup script separately or ensure credentials exist.")

async def _save_hos_auth():
    async with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        console.print("[cyan]Navigating to HOS Login... Please Log In manually.[/]")
        page.goto('https://backoffice-huddle.netlify.app')
        
        # Wait until we are redirected away from login
        try:
            page.wait_for_url(re.compile(r"^(?!.*login).*$"), timeout=300000)
            context.storage_state(path=HOS_AUTH_FILE)
            console.print(f"[green]HOS Auth saved to {HOS_AUTH_FILE}[/]")
        except Exception as e:
            console.print(f"[red]Failed to save HOS auth: {e}[/]")
        finally:
            browser.close()

async def _save_oo_auth():
    async with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        console.print("[cyan]Navigating to OpticOdds...[/]")
        page.goto("https://app.opticodds.com/screen/basketball/ncaab/market/total_points", wait_until="domcontentloaded")
        
        try:
            google_btn = page.locator("#oauth-google")
            if google_btn.is_visible():
                google_btn.click(force=True)
                console.print("[yellow]Please log in with Google...[/]")
            
            page.wait_for_url("**/main**", timeout=0)
            context.storage_state(path=OO_AUTH_FILE)
            console.print(f"[green]OO Auth saved to {OO_AUTH_FILE}[/]")
        except Exception as e:
            console.print(f"[red]Failed to save OO auth: {e}[/]")
        finally:
            browser.close()

def load_oo_headers():
    try:
        with open(OO_AUTH_FILE, 'r') as f:
            data = json.load(f)

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Origin": "https://app.opticodds.com",
            "Referer": "https://app.opticodds.com/",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "*/*"
        }

        if 'cookies' in data:
            cookie_dict = {c['name']: c['value'] for c in data['cookies']} if isinstance(data['cookies'], list) else data['cookies']
            kept_cookies = []
            xsrf_token = None

            for name, value in cookie_dict.items():
                name_lower = name.lower()
                if 'xsrf' in name_lower or 'csrf' in name_lower:
                    xsrf_token = value
                    kept_cookies.append(f"{name}={value}")
                    continue
                if any(name_lower.startswith(prefix) for prefix in COOKIE_IGNORE):
                    continue
                if any(key in name_lower for key in COOKIE_KEEP) or len(str(value)) < 200:
                    kept_cookies.append(f"{name}={value}")

            if kept_cookies:
                headers["Cookie"] = "; ".join(kept_cookies)
                if xsrf_token:
                    headers["X-XSRF-TOKEN"] = urllib.parse.unquote(xsrf_token)
            return headers
    except Exception as e:
        console.print(f"[red]Error parsing OO headers: {e}[/]")
        return {}

# --- Data Fetching ---
async def fetch_oo_games():
    headers = load_oo_headers()
    if not headers: return []

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        try:
            response = await client.get(OO_TARGET_URL)
            if response.status_code != 200:
                console.print(f"[red]OO Error: {response.status_code}[/]")
                return []
            
            data = response.json()
            rows = data.get("rows", [])
            # Access the fixtures metadata block to get abbreviations
            fixtures_data = data.get("fixtures", {})
            
            game_map = {}

            for row in rows:
                fid = row.get("f")
                if not fid: continue
                
                if fid not in game_map:
                    # lookup metadata using fixture id
                    fixture_meta = fixtures_data.get(fid, {})
                    
                    # Extract Home Abbreviation
                    home_abbr = "UNK"
                    home_team_list = fixture_meta.get("home_team")
                    if home_team_list and isinstance(home_team_list, list) and len(home_team_list) > 0:
                        home_abbr = home_team_list[0].get("abbreviation", "UNK")

                    # Extract Away Abbreviation
                    away_abbr = "UNK"
                    away_team_list = fixture_meta.get("away_team")
                    if away_team_list and isinstance(away_team_list, list) and len(away_team_list) > 0:
                        away_abbr = away_team_list[0].get("abbreviation", "UNK")

                    # Initialize with standard keys so _matcher.py doesn't crash
                    game_map[fid] = {
                        "id": fid,
                        "game_id": row.get("gm"),
                        "home": None,          # Matcher looks for this
                        "home_abbr": home_abbr,
                        "away": None,          # Matcher looks for this
                        "away_abbr": away_abbr
                    }
                
                # Populate team names based on row type
                if row.get("t") == "home":
                    game_map[fid]["home"] = row.get("n")
                elif row.get("t") == "away":
                    game_map[fid]["away"] = row.get("n")

            # Filter valid games
            parsed_games = []
            json_output = []

            for g in game_map.values():
                if g["home"] and g["away"]:
                    # Add to the list returned to the app (Standard Keys)
                    parsed_games.append(g)

                    # Add to the JSON output list (Mapped to 'oo_' Keys)
                    json_output.append({
                        "oo_fixture_id": g["id"],
                        "oo_game_id": g["game_id"],
                        "oo_home": g["home"],
                        "oo_home_abbr": g["home_abbr"],
                        "oo_away": g["away"],
                        "oo_away_abbr": g["away_abbr"]
                    })

            # Save the JSON in the requested specific format
            with open(OO_PARSE_FILE, "w") as f:
                json.dump(json_output, f, indent=2)

            # Return the standard list to the application flow
            return parsed_games

        except Exception as e:
            console.print(f"[red]OO Exception: {e}[/]")
            return []
async def fetch_hos_games():
    games = []
    temp_games = []
    # Use Async Playwright to support the pagination loop
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=HOS_AUTH_FILE)
        page = await context.new_page()

        async def handle_response(response):
            if HOS_GQL_ENDPOINT in response.url:
                try:
                    data = await response.json()
                    if "data" in data and "events" in data["data"]:
                        nodes = data["data"]["events"].get("nodes", [])
                        for node in nodes:
                            comps = node.get("competitors", [])
                            home = next((c for c in comps if c["side"] == "HOME"), {})
                            away = next((c for c in comps if c["side"] == "AWAY"), {})
                            
                            games.append({
                                'id': node.get("eventId"),
                                'home': home.get("name", "Unknown"),
                                'home_id': home.get("teamId", "N/A"),
                                'home_cid': home.get("competitorId", "N/A"),
                                'away': away.get("name", "Unknown"),
                                'away_id': away.get("teamId", "N/A"),
                                'away_cid': away.get("competitorId", "N/A")
                            })
                            temp_games.append({
                                'hos_event_id': node.get("eventId"),
                                'hos_home': home.get("name", "Unknown"),
                                'hos_home_id': home.get("teamId", "N/A"),
                                'hos_home_cid': home.get("competitorId", "N/A"),
                                'hos_away': away.get("name", "Unknown"),
                                'hos_away_id': away.get("teamId", "N/A"),
                                'hos_away_cid': away.get("competitorId", "N/A")
                            })
                except: pass

        page.on("response", handle_response)
        
        console.print("[cyan]Scraping HOS Pages...[/]")
        for i in range(1, PAGES_TO_SCRAPE + 1):
            url = f"{HOS_BASE_URL}&page={i}{HOS_FILTER}"
            # console.print(f"Loading Page {i}...")
            await page.goto(url)
            await page.wait_for_timeout(3000) # Wait for network
        with open(HOS_PARSE_FILE, "w") as f:
                f.write(json.dumps(temp_games, indent = 2))
        await browser.close()
    # Deduplicate based on ID
    unique_games = {g['id']: g for g in games}.values()
    return list(unique_games)

# --- Matching Logic ---

def similarity(a, b):
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()

def auto_match_games(hos_games, oo_games):
    matches = []
    unmatched_oo = list(range(len(oo_games)))
    
    for hos_idx, hos_game in enumerate(hos_games):
        best_match_idx = None
        best_score = 0
        match_type = "DIRECT" # DIRECT or SWAP
        
        for oo_idx in unmatched_oo:
            oo_game = oo_games[oo_idx]
            
            # Direct Match Score
            s_direct = (similarity(hos_game['home'], oo_game['home']) + 
                        similarity(hos_game['away'], oo_game['away'])) / 2
            
            # Swapped Match Score
            s_swap = (similarity(hos_game['home'], oo_game['away']) + 
                      similarity(hos_game['away'], oo_game['home'])) / 2
            
            current_max = max(s_direct, s_swap)
            
            if current_max > best_score and current_max > MATCH_THRESHOLD:
                best_score = current_max
                best_match_idx = oo_idx
                match_type = "SWAP" if s_swap > s_direct else "DIRECT"
        
        if best_match_idx is not None:
            matches.append({
                'hos_game': hos_game,
                'oo_game': oo_games[best_match_idx],
                'oo_idx': best_match_idx,
                'confidence': best_score,
                'type': match_type
            })
            unmatched_oo.remove(best_match_idx)
        else:
            matches.append({
                'hos_game': hos_game,
                'oo_game': None,
                'oo_idx': None,
                'confidence': 0,
                'type': None
            })
            
    return matches

# --- UI Components ---

def make_layout() -> Layout:
    layout = Layout(name="root")
    layout.split(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=7)
    )
    return layout

def render_matches(matches, selected_idx, oo_games):
    table = Table(box=box.ROUNDED, expand=True, row_styles=["none", "dim"])
    table.add_column("#", style="cyan", width=3)
    table.add_column("HOS (Home vs Away)", style="green", width=35)
    table.add_column("Link", justify="center", width=4)
    table.add_column("OpticOdds (Home vs Away)", style="yellow", width=35)
    table.add_column("Info", style="magenta", width=10)
    
    # Calculate visible range to handle scrolling
    start_idx = max(0, selected_idx - 10)
    end_idx = min(len(matches), start_idx + 22)
    
    for idx in range(start_idx, end_idx):
        match = matches[idx]
        hos = match['hos_game']
        oo = match['oo_game']
        
        h_text = f"{hos['home']} vs {hos['away']}"
        
        if oo:
            o_text = f"{oo['home']} vs {oo['away']}"
            link = "↔"
            conf = f"{match['confidence']:.2f}"
            if match['type'] == "SWAP":
                link = "⤮" # Crossed arrows
                conf += " (S)"
        else:
            o_text = "[dim]Unmatched[/]"
            link = "○"
            conf = "-"
            
        style = "bold white on blue" if idx == selected_idx else ""
        table.add_row(str(idx), h_text, link, o_text, conf, style=style)
        
    return Panel(table, title=f"Matches ({selected_idx+1}/{len(matches)})", box=box.ROUNDED)

def render_footer(matches, selected_idx, oo_games, input_buffer):
    current = matches[selected_idx]
    
    # Find available OO games for suggestion
    matched_oo_ids = {m['oo_game']['id'] for m in matches if m['oo_game']}
    available_oo = [g for g in oo_games if g['id'] not in matched_oo_ids]
    
    # If currently typing a number
    if input_buffer:
        return Panel(f"Selecting OO Game Index: [bold yellow]{input_buffer}[/]", title="Input", box=box.ROUNDED)

    status = "[bold]Controls:[/]\n[cyan]↑/↓[/]: Navigate  |  [cyan]←[/]: Unmatch  |  [cyan]→[/]: Auto-Match (Retry)\n[cyan]Number[/]: Set OO Index manually  |  [cyan]S[/]: Save  |  [cyan]Q[/]: Quit"
    
    if current['oo_game']:
        status += f"\n[green]Currently Matched:[/ in OO list index {current['oo_idx']}"
        
    return Panel(status, title="Status", box=box.ROUNDED)

# --- Application Class ---

class GameMatcherApp:
    def __init__(self, hos_games, oo_games):
        self.hos_games = hos_games
        self.oo_games = oo_games
        self.matches = auto_match_games(hos_games, oo_games)
        self.selected_idx = 0
        self.input_buffer = ""
        self.layout = make_layout()
        
    def save_data(self):
        output = []
        for match in self.matches:
            if match['oo_game']:
                h, o = match['hos_game'], match['oo_game']
                output.append({
                    'hos_event_id': h['id'],
                    'hos_home': h['home'], 'hos_home_id': h['home_id'],
                    'hos_away': h['away'], 'hos_away_id': h['away_id'],
                    'oo_fixture_id': o['id'],
                    'oo_game_id': o['game_id'],
                    'oo_home': o['home'], 'oo_home_abbr': o['home_abbr'],
                    'oo_away': o['away'], 'oo_away_abbr': o['away_abbr'],
                    'match_confidence': match['confidence'],
                    'is_swap': match['type'] == "SWAP"
                })
        
        with open(MATCHED_GAMES, 'w') as f:
            # dump = list({i["oo_game_id"]: i for i in output if i["oo_game_id"].endswith("2-01")}.values())
            json.dump(output, f, indent=2)
        return len(output)

    def run(self):
        with Live(self.layout, refresh_per_second=12, screen=True) as live:
            while True:
                # Update UI
                self.layout['header'].update(Panel(Align.center(f"Game Matcher | {datetime.now().strftime('%H:%M:%S')}"), style="white on blue"))
                self.layout['main'].update(render_matches(self.matches, self.selected_idx, self.oo_games))
                self.layout['footer'].update(render_footer(self.matches, self.selected_idx, self.oo_games, self.input_buffer))
                
                # Input Handling
                key = get_key()
                if key is None: continue
                
                if key == 'UP':
                    self.selected_idx = max(0, self.selected_idx - 1)
                    self.input_buffer = ""
                elif key == 'DOWN':
                    self.selected_idx = min(len(self.matches) - 1, self.selected_idx + 1)
                    self.input_buffer = ""
                
                elif key == 'LEFT':
                    self.matches[self.selected_idx].update({'oo_game': None, 'oo_idx': None, 'confidence': 0, 'type': None})
                
                elif key in '0123456789':
                    self.input_buffer += key
                
                elif key == '\r' or key == '\n': # Enter key
                    if self.input_buffer:
                        idx = int(self.input_buffer)
                        if 0 <= idx < len(self.oo_games):
                            # Manual match assignment
                            oo = self.oo_games[idx]
                            self.matches[self.selected_idx].update({
                                'oo_game': oo,
                                'oo_idx': idx,
                                'confidence': 1.0,
                                'type': "MANUAL"
                            })
                        self.input_buffer = ""
                
                elif key.lower() == 's':
                    count = self.save_data()
                    # Flash confirmation (hacky but works in loop)
                    self.layout['footer'].update(Panel(f"[green bold]Saved {count} matches to ../utils/matched_games.json![/]", style="white on green"))
                    live.refresh()
                    time.sleep(1)
                    
                elif key.lower() == 'q':
                    break

# --- Verification ---

def verify_matches(master_url):
    if not master_url: return
    try:
        parsed = urllib.parse.urlparse(master_url)
        query_ids = urllib.parse.parse_qs(parsed.query).get("ids", [])
        
        if not os.path.exists(MATCHED_GAMES):
            console.print("[red]No ../utils/matched_games.json found to verify.[/]")
            return

        with open(MATCHED_GAMES, "r") as f:
            saved = json.load(f)
            saved_ids = [s['hos_event_id'] for s in saved]
        
        missing = [i for i in query_ids if i not in saved_ids]
        
        if missing:
            console.print(f"[red bold]VERIFICATION FAILED![/] Missing Game IDs: {missing}")
        else:
            console.print("[green bold]VERIFICATION SUCCESSFUL![/] All master IDs found in local matches.")
            
    except Exception as e:
        console.print(f"[red]Verification Error: {e}[/]")

# --- Main ---



async def main():
    # 1. Auth Check
    ensure_auth_files()
    
    # 2. Fetch Data
    console.print(f"[cyan]Fetching HOS games (scans {PAGES_TO_SCRAPE} pages)...[/]")
    hos_games = await fetch_hos_games()
    console.print(f"[green]Found {len(hos_games)} HOS events.[/]")
    
    console.print("[cyan]Fetching OpticOdds games...[/]")
    oo_games = await fetch_oo_games()
    console.print(f"[green]Found {len(oo_games)} OO fixtures.[/]")
    
    if not hos_games or not oo_games:
        console.print("[red bold]Critical Error: One or both sources returned 0 games. Exiting.[/]")
        return

    print(oo_games, hos_games)
    # 3. Interactive Matcher
    app = GameMatcherApp(hos_games, oo_games)
    
    # Add a buffer for user to read logs before UI starts
    console.print("[yellow]Starting Interactive Matcher in 2 seconds...[/]")
    await asyncio.sleep(2)
    app.run()
    
    # 4. Optional Verification
    # You can hardcode a URL here or ask for input
    # master_url = "https://...?ids=..."
    # verify_matches(master_url)

# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         print("\nExiting...")
async def run_matcher(oo_url=None, pages=5):
    """
    Wraps the main logic into a callable function.
    """
    # Note: Global variables (OO_AUTH_FILE, etc.) are used here.
    # Do NOT redefine them locally.

    # 1. Ensure Auth
    ensure_auth_files()
    
    # 2. Fetch Data (using parameters if provided)
    # You might want to update the global variable dynamically if 'pages' is passed:
    global PAGES_TO_SCRAPE
    if pages:
        PAGES_TO_SCRAPE = pages

    hos_games = await fetch_hos_games() 
    oo_games = await fetch_oo_games()
    
    if not hos_games or not oo_games:
        return {"error": "No games found"}

    # 3. Start UI
    app = GameMatcherApp(hos_games, oo_games)
    app.run()
    
    return {"status": "success"}

# Keep the entry point for direct execution
if __name__ == "__main__":
    asyncio.run(run_matcher())