import asyncio
import os
import json
from pathlib import Path
from playwright.async_api import async_playwright

# JavaScript function to extract odds data (Same as in odds_monitor.py)
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
                // Try multiple selectors for spread text
                let spread = '';
                const spreadEl = dataRows[0].querySelector('div.font-bold.tracking-tighter');
                if (spreadEl) {
                     spread = spreadEl.textContent?.split('/')[0]?.split('\\n')?.pop()?.trim() || '';
                }

                let probability = '';
                
                if (colId === 'Pinnacle') {
                    probability = dataRows[0].querySelector('span.text-\\\\[13px\\\\]')?.textContent?.trim() || '';
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
                const probLeft = dataRows[1].querySelector('div.w-1\\\\/2.text-left .font-semibold.text-brand-gray-9')?.textContent?.trim() || '';
                const probRight = dataRows[1].querySelector('div.w-1\\\\/2.text-right .font-semibold.text-brand-gray-9')?.textContent?.trim() || '';
                
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
                    let spread = '';
                    const spreadEl = dataRows[1].querySelector('div.font-bold.tracking-tighter');
                    if (spreadEl) {
                         spread = spreadEl.textContent?.split('/')[0]?.split('\\n')?.pop()?.trim() || '';
                    }

                    let probability = '';
                    
                    if (colId === 'Pinnacle') {
                        probability = dataRows[1].querySelector('span.text-\\\\[13px\\\\]')?.textContent?.trim() || '';
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

async def extract_odds_from_page(page):
    """
    Extracts odds using the pre-defined JS functions on the given Playwright page.
    """
    try:
        # Wait for the grid rows to be present
        # Reducing timeout as this is a local static file load, should be fast.
        await page.wait_for_selector('.ag-center-cols-container [role="row"][row-index]', timeout=5000)
    except Exception as e:
         print(f"Warning: Could not find grid rows (selector timeout): {e}")

    # Initial extraction
    data = await page.evaluate(EXTRACT_ODDS_JS)
    
    team_names = {}
    if data:
        game_ids = list(data.keys())
        team_names = await page.evaluate(EXTRACT_TEAM_NAMES_JS, game_ids)
            
    return {
        "events": data,
        "team_names": team_names
    }

async def master_extract_function(file_path):
    """
    The master function that takes a file path (html), loads it, and returns the extracted odds.
    """
    abs_path = os.path.abspath(file_path)
    file_uri = Path(abs_path).as_uri()
    
    async with async_playwright() as p:
        # Launch browser (headless)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"Opening {file_path}...")
        await page.goto(file_uri)
        
        result = await extract_odds_from_page(page)
        
        await browser.close()
        return result

async def main():
    files_to_process = ["moneyline.html", "spread.html", "total.html"]
    
    all_results = {}
    
    for filename in files_to_process:
        if not os.path.exists(filename):
            print(f"Skipping {filename}: File not found.")
            continue
            
        print(f"Processing {filename}...")
        try:
            data = await master_extract_function(filename)
            all_results[filename] = data
            event_count = len(data.get("events", {}))
            print(f"Successfully extracted {event_count} events from {filename}")
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    # Output results to a JSON file
    output_file = "local_extracted_odds.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"All data saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
