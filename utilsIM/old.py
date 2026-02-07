from playwright.sync_api import sync_playwright
import time
import json
import numpy as np 
import math
from typing import Dict, Any, List

# ======================================================================
# CORE UTILITY FUNCTIONS 
# ======================================================================

# Cookie filtering settings
IGNORE_PREFIXES = ['_ga', '_gid', '_fbp', '_hjid', 'intercom-', 'amplitude_', 'hubspot', 'mp_', '__cf', '_uetsid', '_uetvid']
KEEP_KEYWORDS = ['session', 'auth', 'token', 'id', 'user', 'jwt', 'xsrf', 'csrf']


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



def clean_probability(prob_value: Any) -> float | None:
    """Converts a probability value (string with '%' or raw number) to a float."""
    if prob_value is None or prob_value == "":
        return None
        
    if isinstance(prob_value, (int, float)):
        return float(prob_value)

    try:
        if '|' in str(prob_value):
            return None 

        cleaned_value = str(prob_value).replace('%', '').strip()
        return float(cleaned_value)
    except ValueError:
        return None

def normalizeSpread(data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Parses and normalizes the implied probabilities for two opposing outcomes 
    (assumed to be stored as a list of exactly two items: index 0 and index 1).
    """
    for bookmaker_key in list(data.keys()):
        if bookmaker_key in ["startTime", "rotationNumber", "teamName", "averagePrice", "bestPrice"]:
            continue

        bookmaker_odds = data[bookmaker_key]
        if len(bookmaker_odds) != 2:
            continue
            
        try:
            prob_str_0 = bookmaker_odds[0]["probability"].replace('%', '').strip()
            prob_str_1 = bookmaker_odds[1]["probability"].replace('%', '').strip()
            
            if not prob_str_0 or not prob_str_1:
                continue

            prob_0 = float(prob_str_0)
            prob_1 = float(prob_str_1)
            
            total_implied_prob = prob_0 + prob_1
            if total_implied_prob <= 0:
                continue

            normalization_factor = 100.0 / total_implied_prob
            
            normalized_prob_0 = prob_0 * normalization_factor
            normalized_prob_1 = prob_1 * normalization_factor
            
            bookmaker_odds[0]["probability_normalized"] = normalized_prob_0
            bookmaker_odds[1]["probability_normalized"] = normalized_prob_1

        except Exception:
            pass
            
    return data

def analyze_spread_deviation(data: Dict[str, List[Dict[str, Any]]], target_sportsbook_name: str, probability_field: str = "probability_normalized") -> Dict[str, Any]:
    """
    Calculates Z-score AND Min/Max deviation for a two-sided market.
    """
    results = {"target_sportsbook": target_sportsbook_name}
    
    if target_sportsbook_name not in data or len(data[target_sportsbook_name]) < 2:
        return {"error": f"Target sportsbook '{target_sportsbook_name}' not found or incomplete."}

    target_odds = data[target_sportsbook_name]
    target_spread_0 = target_odds[0].get("spread", "")
    target_spread_1 = target_odds[1].get("spread", "")
    
    target_prob_0 = clean_probability(target_odds[0].get(probability_field, ""))
    target_prob_1 = clean_probability(target_odds[1].get(probability_field, ""))

    if target_prob_0 is None or target_prob_1 is None:
        return {"error": f"Target sportsbook '{target_sportsbook_name}' is missing {probability_field} data."}

    matching_probs_0 = []
    matching_probs_1 = []

    for sportsbook, odds_list in data.items():
        if not isinstance(odds_list, list) or len(odds_list) != 2:
            continue
            
        spread_0 = odds_list[0].get("spread", "")
        spread_1 = odds_list[1].get("spread", "")
        
        prob_0 = clean_probability(odds_list[0].get(probability_field, ""))
        prob_1 = clean_probability(odds_list[1].get(probability_field, ""))
        
        # Match checks: same spread for both outcomes, and valid probabilities exist
        if (spread_0 == target_spread_0 and spread_1 == target_spread_1 and 
            prob_0 is not None and prob_1 is not None):
            
            matching_probs_0.append(prob_0)
            matching_probs_1.append(prob_1)

    def calculate_metrics(target_prob, matching_probs, outcome_name):
        if len(matching_probs) > 1: 
            mean = np.mean(matching_probs)
            std_dev = np.std(matching_probs, ddof=1) 
            min_prob = min(matching_probs)
            max_prob = max(matching_probs)
            
            # Z-Score Calculation
            if std_dev > 0 and not math.isnan(std_dev):
                z_score = (target_prob - mean) / std_dev
            else:
                z_score = 0.0

            return {
                "target_prob": round(target_prob, 3),
                "snipped_mean": round(mean, 3),
                "std_dev": round(std_dev, 3),
                "z_score_stds_away": round(z_score, 3),
                "min_market_prob": round(min_prob, 3),
                "max_market_prob": round(max_prob, 3),
                "diff_vs_min": round(target_prob - min_prob, 3),
                "diff_vs_max": round(target_prob - max_prob, 3),
                "matching_sportsbooks_count": len(matching_probs)
            }
        else:
            return {"error": f"Insufficient data (less than 2 matching sportsbooks) for {outcome_name}."}

    results[f"Outcome 1 Spread ({target_spread_0 or 'Team 1'})"] = calculate_metrics(
        target_prob_0, matching_probs_0, f"Outcome 1 Spread ({target_spread_0 or 'Team 1'})"
    )
    
    results[f"Outcome 2 Spread ({target_spread_1 or 'Team 2'})"] = calculate_metrics(
        target_prob_1, matching_probs_1, f"Outcome 2 Spread ({target_spread_1 or 'Team 2'})"
    )

    return results


def analyze_single_outcome_deviation(data: Dict[str, List[Dict[str, Any]]], target_sportsbook_name: str, target_market_type: str) -> Dict[str, Any]:
    """
    Calculates Z-score AND Min/Max deviation for a single outcome (e.g., O/U Over).
    """
    results = {"target_sportsbook": target_sportsbook_name, "market_type": target_market_type}
    
    # 1. Find the target sportsbook's specific odds
    target_entry = None
    for odds in data.get(target_sportsbook_name, []):
        if odds.get("market_type") == target_market_type:
            target_entry = odds
            break

    if not target_entry:
        return {"error": f"Target sportsbook '{target_sportsbook_name}' missing data for market type '{target_market_type}'."}

    target_spread = target_entry.get("spread", "")
    target_prob = clean_probability(target_entry.get("probability", ""))

    if not target_prob:
        return {"error": f"Target sportsbook '{target_sportsbook_name}' missing probability data for market type '{target_market_type}'."}
    
    matching_probs = []

    # 2. Collect probabilities from all sportsbooks matching the spread
    for sportsbook, odds_list in data.items():
        if sportsbook in ["startTime", "rotationNumber", "teamName", "averagePrice", "bestPrice"]:
            continue
        
        for odds in odds_list:
            if odds.get("market_type") == target_market_type and odds.get("spread") == target_spread:
                prob = clean_probability(odds.get("probability"))
                if prob is not None:
                    matching_probs.append(prob)

    # 3. Calculate deviation
    if len(matching_probs) > 1: 
        mean = np.mean(matching_probs)
        std_dev = np.std(matching_probs, ddof=1) 
        min_prob = min(matching_probs)
        max_prob = max(matching_probs)
        
        if std_dev > 0 and not math.isnan(std_dev):
            z_score = (target_prob - mean) / std_dev
        else:
            z_score = 0.0

        results["Deviation"] = {
            "target_prob": round(target_prob, 3),
            "snipped_mean": round(mean, 3),
            "std_dev": round(std_dev, 3),
            "z_score_stds_away": round(z_score, 3),
            "min_market_prob": round(min_prob, 3),
            "max_market_prob": round(max_prob, 3),
            "diff_vs_min": round(target_prob - min_prob, 3),
            "diff_vs_max": round(target_prob - max_prob, 3),
            "matching_spread": target_spread,
            "matching_sportsbooks_count": len(matching_probs)
        }
    else:
        results["Deviation"] = {"error": "Insufficient data (less than 2 matching spreads) for deviation calculation."}

    return results
    
def check_for_outlier_spread(
    analysis_results: Dict[str, Any], 
    z_threshold: float = 2.0, 
    pct_threshold: float = 3.0,
    min_std: float = 1.0,
    min_std_z_threshold: float = 3.0
) -> Dict[str, Any]:
    """
    Analyzes results to determine if target is an outlier based on:
    1. Z-Score (Standard Deviations away).
       - Uses 'z_threshold' normally.
       - Uses 'min_std_z_threshold' if market std_dev is < 'min_std'.
    2. Percentage Distance from Min or Max market price.
    """
    outlier_status = {
        "is_outlier": False,
        "z_threshold": z_threshold,
        "details": [],
        "target_sportsbook": analysis_results.get("target_sportsbook", "N/A"),
        "market_type": analysis_results.get("market_type", "Moneyline/TeamSpread")
    }
    
    def evaluate_metrics(data_obj, label):
        if "error" in data_obj or "z_score_stds_away" not in data_obj:
            return

        z_score = data_obj.get("z_score_stds_away")
        std_dev = data_obj.get("std_dev", 0)
        diff_vs_min = data_obj.get("diff_vs_min", 0)
        diff_vs_max = data_obj.get("diff_vs_max", 0)

        # Dynamic Z-Threshold Logic based on Market Tightness (Std Dev)
        active_z_threshold = z_threshold
        is_tight_market = False
        
        if std_dev < min_std:
            active_z_threshold = min_std_z_threshold
            is_tight_market = True

        # Check conditions
        is_z_outlier = abs(z_score) >= active_z_threshold
        is_min_outlier = abs(diff_vs_min) >= pct_threshold
        is_max_outlier = abs(diff_vs_max) >= pct_threshold

        if is_z_outlier or is_min_outlier or is_max_outlier:
            outlier_status["is_outlier"] = True
            
            reasons = []
            if is_z_outlier: 
                threshold_msg = f"{active_z_threshold} (Tight Market)" if is_tight_market else f"{active_z_threshold}"
                reasons.append(f"Z-Score {z_score} >= {threshold_msg}")
            if is_min_outlier: reasons.append(f"Diff from Min {diff_vs_min}%")
            if is_max_outlier: reasons.append(f"Diff from Max {diff_vs_max}%")
            
            action = "Significantly Higher" if (z_score > 0 or diff_vs_max > 0) else "Significantly Lower"

            outlier_status["details"].append({
                "market_side": label,
                "reasons": ", ".join(reasons),
                "action": action,
                "target_prob": data_obj["target_prob"],
                "market_std": std_dev,
                "market_range": f"{data_obj['min_market_prob']} - {data_obj['max_market_prob']}",
                "market_mean": data_obj["snipped_mean"],
                "z_score": z_score
            })

    # Handle single outcome (Over Price)
    if "Deviation" in analysis_results and isinstance(analysis_results["Deviation"], dict):
        data = analysis_results["Deviation"]
        label = f"{outlier_status['market_type']} ({data.get('matching_spread', '')})"
        evaluate_metrics(data, label)

    # Handle two-outcome (Moneyline/Spread)
    else:
        for outcome, data in analysis_results.items():
            if outcome.startswith("Outcome") and isinstance(data, dict):
                evaluate_metrics(data, outcome)

    return outlier_status


def extract_odds_data_all_events(page) -> Dict[str, Dict[str, List[Dict[str, Any]]]] | None:
    """
    Highly optimized extraction using batch operations and reduced DOM queries.
    """
    try:
        # Single wait for the entire grid to load
        page.wait_for_selector('.ag-center-cols-container [role="row"][row-index]', timeout=3000)
        
        # Get all data in one JavaScript execution to minimize Python-browser communication
        grid_data = page.evaluate("""
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
                                const spread = dataRows[1].querySelector('div.font-bold.tracking-tighter')?.textContent?.split('/')[0]?.split('\\n')?.pop()?.trim() || '';
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
        """)
        
        return grid_data
        
    except Exception as e:
        print(f"[ERROR] Failed to extract odds data: {e}")
        return None


def extract_team_names_batch(page, game_ids):
    """Optimized team name extraction using single JavaScript execution."""
    try:
        team_names_data = page.evaluate("""
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
        """, list(game_ids))
        
        return team_names_data
    except:
        return {game_id: f"Game ID: {game_id}" for game_id in game_ids}

# ======================================================================
# MAIN EXECUTION SCRIPT
# ======================================================================
def filter_games_by_word(data_list, words_list):
    """
    Filters a list of game data dictionaries, returning only those where the 
    'Game' value contains at least one of the specified words (case-insensitive).
    """
    lower_words = [word.lower() for word in words_list]
    
    filtered_list = [
        item for item in data_list
        if any(word in item.get("Game", "").lower() for word in lower_words)
    ]
    
    return filtered_list

def game_matches_word_list(team_names_string: str, words_list: List[str]) -> bool:
    """
    Checks if any word in words_list (case-insensitive) is present 
    in the team names string.
    """
    lower_team_names = team_names_string.lower()
    lower_words = [word.lower() for word in words_list]
    
    return any(word in lower_team_names for word in lower_words)

def main():
    
    # !!! MANDATORY: REPLACE THIS URL WITH THE ACTUAL WEBSITE URL YOU WANT TO SCRAPE !!!
    target_url = "https://app.opticodds.com/screen/hockey/nhl/market/main" 
    AUTH_FILE = "auth.json"
    # Configuration
    TARGET_SPORTSBOOK = "Betr"
    PROBABILITY_FIELD = "probability_normalized" 
    words_list = ["Minnesota","Pittsburgh","Boston","Dallas","New","Utah","Nashville","Edmonton"]
    
    # OUTLIER SETTINGS
    OUTLIER_THRESHOLD = 1.5      # Normal Z-Score threshold
    MIN_MAX_DIFF_THRESHOLD = 5.69 # Percentage diff from Min/Max
    
    # TIGHT MARKET SETTINGS (New)
    MIN_STD_THRESHOLD = 1.25      # If market std < 1.0% (tight market)
    MIN_STD_Z_THRESHOLD = 2.5    # Require 3.0 stds away instead of 1.5

    print(f"Starting live monitoring for: {target_url}")
    print(f"Target Sportsbook for Analysis: {TARGET_SPORTSBOOK}")
    print(f"Normal Thresholds: Z-Score >= {OUTLIER_THRESHOLD} OR Min/Max Diff >= {MIN_MAX_DIFF_THRESHOLD}%")
    print(f"Tight Market Rule: If Market STD < {MIN_STD_THRESHOLD}, require Z-Score >= {MIN_STD_Z_THRESHOLD}")
    print(f"Processing ONLY games containing: {', '.join(words_list)}")
    print("Press Ctrl+C to stop the script.")
    
    lower_filter_words = [word.lower() for word in words_list]
    header = load_auth_headers(AUTH_FILE=AUTH_FILE)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False) 
            import os
            if AUTH_FILE in os.listdir("."):
                context = browser.new_context(storage_state=AUTH_FILE)
            else:
                context = browser.new_context()
            page1 = context.new_page() 
            
            print("Navigating to the target URL...")
            page1.goto(target_url, wait_until="domcontentloaded") 
            
            while True:
                all_outliers_summary = []
                
                try:
                    print(f"\n[{time.strftime('%H:%M:%S')}] Attempting data extraction...")
                    
                    # Reduced timeout for faster processing
                    page1.wait_for_selector('.ag-center-cols-container [role="row"][row-index]', timeout=2000)

                    data_all_events = extract_odds_data_all_events(page1)
                    
                    if data_all_events is not None and data_all_events:
                        print(f"Data Extracted Successfully for {len(data_all_events)} events.")
                        
                        # Batch extract team names for all games at once
                        team_names_dict = extract_team_names_batch(page1, list(data_all_events.keys()))
                        
                        for game_id, game_data in data_all_events.items():
                            
                            team_names = team_names_dict.get(game_id, f"Game ID: {game_id}")
                            
                            # Filter check - skip if no matching words
                            lower_game_name = team_names.lower()
                            if not any(word in lower_game_name for word in lower_filter_words):
                                continue 
                            
                            # =================================================================
                            # A. MONEYLINE/TEAM SPREAD OUTLIER CHECK
                            # =================================================================
                            
                            moneyline_market_data = {}
                            for bookmaker, odds_list in game_data.items():
                                if len(odds_list) >= 3 and odds_list[1].get('market_type') == "Moneyline_Team1":
                                    moneyline_market_data[bookmaker] = [odds_list[1], odds_list[2]]
                            
                            if len(moneyline_market_data) > 1 and TARGET_SPORTSBOOK in moneyline_market_data:
                                
                                normalized_moneyline_data = normalizeSpread(moneyline_market_data)
                                
                                std_analysis = analyze_spread_deviation(
                                    normalized_moneyline_data, 
                                    TARGET_SPORTSBOOK, 
                                    probability_field=PROBABILITY_FIELD
                                )
                                
                                outlier_check = check_for_outlier_spread(
                                    std_analysis, 
                                    z_threshold=OUTLIER_THRESHOLD,
                                    pct_threshold=MIN_MAX_DIFF_THRESHOLD,
                                    min_std=MIN_STD_THRESHOLD,
                                    min_std_z_threshold=MIN_STD_Z_THRESHOLD
                                )
                                
                                if outlier_check["is_outlier"]:
                                    outlier_check["Game"] = team_names
                                    outlier_check["market_type"] = "Moneyline/Team Spread"
                                    all_outliers_summary.append(outlier_check)

                            # =================================================================
                            # B. OVER PRICE OUTLIER CHECK
                            # =================================================================
                            
                            single_outcome_analysis = analyze_single_outcome_deviation(
                                game_data, 
                                TARGET_SPORTSBOOK, 
                                target_market_type="Over_Price"
                            )
                            
                            outlier_check_ou = check_for_outlier_spread(
                                single_outcome_analysis, 
                                z_threshold=OUTLIER_THRESHOLD,
                                pct_threshold=MIN_MAX_DIFF_THRESHOLD,
                                min_std=MIN_STD_THRESHOLD,
                                min_std_z_threshold=MIN_STD_Z_THRESHOLD
                            )
                            
                            if outlier_check_ou["is_outlier"]:
                                outlier_check_ou["Game"] = team_names
                                outlier_check_ou["market_type"] = "Over Price (Raw)"
                                all_outliers_summary.append(outlier_check_ou)

                        
                        print("\n" + "="*80)
                        print(f"FINAL OUTLIER ANALYSIS SUMMARY (Target: {TARGET_SPORTSBOOK})")
                        print("="*80)
                        
                        if all_outliers_summary:
                            print(f"\n🚨 {len(all_outliers_summary)} OUTLIER(S) FOUND (Matching Teams Only):")
                            print(json.dumps(all_outliers_summary, indent=4))
                        else:
                            print("✅ No outliers found at the specified threshold for the filtered teams.")

                        print("\n" + "="*80)
                        
                    else:
                        print("Extraction skipped: No events found.")
                        
                except Exception as e:
                    print(f"\n[Execution Error] Could not complete data extraction or analysis. Waiting for retry. Error: {e}")
                    
                time.sleep(5) 

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user (Ctrl+C).")
    except Exception as e:
        print(f"\n[Critical Error] Script failed: {e}")
    finally:
        if 'browser' in locals() and browser:
            browser.close()
        print("Browser session closed.")

if __name__ == "__main__":
    main()