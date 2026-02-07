import asyncio
from playwright.async_api import async_playwright, Page, Browser
import json
from typing import Dict, Any, List

# OpticOdds URLs for different markets
OPTIC_ODDS_URLS = {
    "moneyline": "https://app.opticodds.com/screen/basketball/ncaab/market/moneyline",
    "point_spread": "https://app.opticodds.com/screen/basketball/ncaab/market/point_spread",
    "total_points": "https://app.opticodds.com/screen/basketball/ncaab/market/total_points",
}

# HOS URL - multiview trading UI
HOS_URL = "https://backoffice-huddle.netlify.app/operations/trading-ui/multiview"

# Auth file paths
OO_AUTH = '../credentials/OOauth.json'
HOS_AUTH = '../credentials/HOSauth.json'


# JavaScript function to extract odds data from OpticOdds pages
EXTRACT_ODDS_JS = """
() => {
    const rows = document.querySelectorAll('.ag-center-cols-container [role="row"][row-index]');
    const results = {};
    
    rows.forEach(row => {
        const rowId = row.getAttribute('row-id');
        if (!rowId) return;
        
        const cells = row.querySelectorAll('[role="gridcell"][col-id]');
        const rowData = {};
        
        cells.forEach(cell => {
            const colId = cell.getAttribute('col-id');
            if (!colId) return;
            
            const dataRows = cell.querySelectorAll('div.box-border.flex.w-full.cursor-pointer.flex-col.justify-center');
            const columnData = [];
            
            // Process first row (Over/Under - OVER side)
            if (dataRows[0]) {
                const spread = dataRows[0].querySelector('div.font-bold.tracking-tighter')?.textContent?.split('/')[0]?.split('\\n')?.pop()?.trim() || '';
                let probability = '';
                
                if (colId === 'Pinnacle') {
                    probability = dataRows[0].querySelector('span.text-\\[13px\\]')?.textContent?.trim() || '';
                } else if (colId === 'bestPrice') {
                    probability = dataRows[0].querySelector('div.mr-1.font-medium')?.textContent?.replace('/', '')?.trim() || '';
                } else {
                    probability = dataRows[0].querySelector('div.text-sm.text-brand-gray-7')?.textContent?.trim() || '';
                }
                
                let source = colId;
                if (colId === 'bestPrice') {
                    const img = dataRows[0].querySelector('img.remix-image');
                    source = img?.getAttribute('alt') || colId;
                }
                
                columnData.push({
                    bookmaker_source: source,
                    market_type: 'Over_Price',
                    spread: spread,
                    probability: probability,
                    outcome_index: 0
                });
            }
            
            // Process second row (Moneyline/Team Spread)
            if (dataRows[1]) {
                const probLeft = dataRows[1].querySelector('div.w-1\\/2.text-left .font-semibold.text-brand-gray-9')?.textContent?.trim() || '';
                const probRight = dataRows[1].querySelector('div.w-1\\/2.text-right .font-semibold.text-brand-gray-9')?.textContent?.trim() || '';
                
                let source = colId;
                if (colId === 'bestPrice') {
                    const img = dataRows[1].querySelector('img.remix-image');
                    source = img?.getAttribute('alt') || colId;
                }
                
                if (probLeft && probRight) {
                    // Moneyline data
                    columnData.push({
                        bookmaker_source: source,
                        market_type: 'Moneyline_Team1',
                        spread: '',
                        probability: probLeft,
                        outcome_index: 1
                    });
                    columnData.push({
                        bookmaker_source: source,
                        market_type: 'Moneyline_Team2',
                        spread: '',
                        probability: probRight,
                        outcome_index: 2
                    });
                } else {
                    // Other spread data
                    const spread = dataRows[1].querySelector('div.font-bold.tracking-tighter')?.textContent?.split('/')[0]?.split('\\n')?.pop()?.trim() || '';
                    let probability = '';
                    
                    if (colId === 'Pinnacle') {
                        probability = dataRows[1].querySelector('span.text-\\[13px\\]')?.textContent?.trim() || '';
                    } else {
                        probability = dataRows[1].querySelector('div.text-sm.text-brand-gray-7')?.textContent?.trim() || '';
                    }
                    
                    if (probability) {
                        columnData.push({
                            bookmaker_source: source,
                            market_type: 'Other_Side2',
                            spread: spread,
                            probability: probability,
                            outcome_index: 1
                        });
                    }
                }
            }
            
            rowData[colId] = columnData;
        });
        
        results[rowId] = rowData;
    });
    
    return results;
}
"""

# JavaScript to extract team names
EXTRACT_TEAM_NAMES_JS = """
(gameIds) => {
    const results = {};
    gameIds.forEach(gameId => {
        try {
            const team1El = document.querySelector(`[row-id="${gameId}"] [col-id="teamName"] div.box-border:nth-child(1) .min-w-0.truncate`);
            const team2El = document.querySelector(`[row-id="${gameId}"] [col-id="teamName"] div.box-border:nth-child(2) .min-w-0.truncate`);
            
            if (team1El && team2El) {
                results[gameId] = `${team1El.textContent.trim()} vs ${team2El.textContent.trim()}`;
            } else {
                results[gameId] = `Game ID: ${gameId}`;
            }
        } catch {
            results[gameId] = `Game ID: ${gameId}`;
        }
    });
    return results;
}
"""


class OddsMonitor:
    def __init__(self, hos_url: str = None):
        self.playwright = None
        self.browser: Browser = None
        self.oo_context = None
        self.hos_context = None
        self.optic_pages: Dict[str, Page] = {}
        self.hos_page: Page = None
        self.hos_url = hos_url or HOS_URL
        
    async def start(self):
        """Initialize Playwright and open all browser pages"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        
        # Create OpticOdds context with auth
        try:
            self.oo_context = await self.browser.new_context(storage_state=OO_AUTH)
            print(f"✅ Loaded OpticOdds auth from {OO_AUTH}")
        except Exception as e:
            print(f"⚠️ Could not load OO auth ({e}), starting fresh context")
            self.oo_context = await self.browser.new_context()
        
        # Create HOS context with auth
        try:
            self.hos_context = await self.browser.new_context(storage_state=HOS_AUTH)
            print(f"✅ Loaded HOS auth from {HOS_AUTH}")
        except Exception as e:
            print(f"⚠️ Could not load HOS auth ({e}), starting fresh context")
            self.hos_context = await self.browser.new_context()
        
        # Open OpticOdds pages for each market
        for market_name, url in OPTIC_ODDS_URLS.items():
            page = await self.oo_context.new_page()
            await page.goto(url)
            self.optic_pages[market_name] = page
            print(f"✅ Opened {market_name} page: {url}")
        
        # Open HOS page
        self.hos_page = await self.hos_context.new_page()
        await self.hos_page.goto(self.hos_url)
        print(f"✅ Opened HOS page: {self.hos_url}")
        
        print("\n🚀 All pages initialized successfully!")
        
    async def extract_odds_from_page(self, page: Page, market_name: str) -> Dict[str, Any]:
        """Extract odds data from a single OpticOdds page"""
        try:
            # Wait for the grid to load
            await page.wait_for_selector('.ag-center-cols-container [role="row"][row-index]', timeout=10000)
            
            # Execute the extraction JavaScript
            data = await page.evaluate(EXTRACT_ODDS_JS)
            
            if data:
                # Extract team names
                game_ids = list(data.keys())
                team_names = await page.evaluate(EXTRACT_TEAM_NAMES_JS, game_ids)
                
                return {
                    "market": market_name,
                    "events": data,
                    "team_names": team_names
                }
            return {"market": market_name, "events": {}, "team_names": {}}
            
        except Exception as e:
            print(f"❌ Error extracting from {market_name}: {e}")
            return {"market": market_name, "events": {}, "team_names": {}, "error": str(e)}
    
    async def extract_all_odds(self) -> Dict[str, Any]:
        """Extract odds data from all OpticOdds pages in parallel"""
        tasks = [
            self.extract_odds_from_page(page, market_name)
            for market_name, page in self.optic_pages.items()
        ]
        
        results = await asyncio.gather(*tasks)
        
        return {result["market"]: result for result in results}
    
    async def refresh_page(self, market_name: str):
        """Refresh a specific OpticOdds page"""
        if market_name in self.optic_pages:
            await self.optic_pages[market_name].reload()
            print(f"🔄 Refreshed {market_name} page")
    
    async def refresh_all_pages(self):
        """Refresh all OpticOdds pages"""
        tasks = [page.reload() for page in self.optic_pages.values()]
        await asyncio.gather(*tasks)
        print("🔄 Refreshed all OpticOdds pages")
    
    async def get_hos_data(self) -> Any:
        """
        Extract data from HOS page
        TODO: Implement HOS-specific extraction logic
        """
        # Placeholder - implement based on HOS page structure
        try:
            # Example: wait for page load and extract data
            await self.hos_page.wait_for_load_state('networkidle')
            # Add HOS-specific JavaScript extraction here
            return {"hos_data": "TODO: Implement HOS extraction"}
        except Exception as e:
            print(f"❌ Error extracting HOS data: {e}")
            return {"error": str(e)}
    
    async def monitor_loop(self, interval_seconds: int = 30):
        """
        Continuously monitor odds at specified interval
        """
        print(f"\n📊 Starting monitoring loop (interval: {interval_seconds}s)")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                print(f"\n{'='*60}")
                print("🔍 Extracting odds data...")
                
                all_odds = await self.extract_all_odds()
                
                for market, data in all_odds.items():
                    event_count = len(data.get("events", {}))
                    print(f"  {market}: {event_count} events")
                
                # Save to file
                with open("live_odds_data.json", "w") as f:
                    json.dump(all_odds, f, indent=2)
                print("💾 Data saved to live_odds_data.json")
                
                # TODO: Add outlier detection logic here
                # analyze_outliers(all_odds)
                
                await asyncio.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n⏹️ Monitoring stopped by user")
    
    async def close(self):
        """Clean up resources"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("🔒 Browser closed")


async def main():
    monitor = OddsMonitor()
    
    try:
        await monitor.start()
        
        # Wait for user to log in if needed
        print("\n⏳ Waiting 10 seconds for pages to fully load...")
        await asyncio.sleep(10)
        
        # Extract initial data
        print("\n📊 Initial data extraction...")
        all_odds = await monitor.extract_all_odds()
        
        for market, data in all_odds.items():
            event_count = len(data.get("events", {}))
            print(f"  {market}: {event_count} events found")
        
        # Save initial data
        with open("initial_odds_data.json", "w") as f:
            json.dump(all_odds, f, indent=2)
        print("\n💾 Initial data saved to initial_odds_data.json")
        
        # Start monitoring loop (uncomment to enable continuous monitoring)
        # await monitor.monitor_loop(interval_seconds=30)
        
        # Keep browser open for manual inspection
        print("\n🔍 Browser windows are open for inspection.")
        print("Press Enter to close...")
        await asyncio.get_event_loop().run_in_executor(None, input)
        
    finally:
        await monitor.close()


if __name__ == "__main__":
    asyncio.run(main())
