# For bias calculation:
# Moneyline: Towards the home team is positive.
# Away team is negative.
# Spread: Towards the Home team is positive.
# Towards the Away team is negative.
# Total: Towards the Over is positive.
# Towards the Under is negative.

def runner() -> list[dict]:
    import json
    import numpy as np

    def solve_optimal_bias(data):
        # Header for the output table
        header = f"{'Game':<40} | {'Market':<10} | {'Opt Bias':<12} | {'Min SSE':<12} | {'Matches'}"
        print(header)
        print("-" * len(header))

        results = []

        for game in data:
            game_name = game.get('game_matchup', 'Unknown')
            markets = game.get('markets', {})

            # We analyze three distinct market types
            for market_type in ['moneyline', 'spread', 'total']:
                market_data = markets.get(market_type, {})
                optic_odds = market_data.get('optic_odds', {})
                hos_data = market_data.get('hos', [])

                # Skip if we don't have House data to compare against
                if not hos_data:
                    continue

                # --- 1. Flatten Optic Odds Data ---
                # We create a normalized list of all available market odds for this game/market
                oo_points = []
                
                for book, entries in optic_odds.items():
                    if not isinstance(entries, list): continue
                    for entry in entries:
                        try:
                            # Parse Probability (handle strings like "52.4%")
                            prob_str = str(entry.get('probability', '0')).replace('%', '')
                            if not prob_str or prob_str == 'nan': continue
                            prob = float(prob_str)

                            # Parse Line/Spread value
                            raw_spread = str(entry.get('spread', ''))
                            line_val = None
                            
                            if market_type == 'total':
                                # Normalize "o145.5" -> 145.5
                                clean = raw_spread.lower().replace('o', '').replace('u', '')
                                if clean: line_val = float(clean)
                            elif market_type == 'spread':
                                # Normalize "-7.5" -> -7.5
                                if raw_spread: line_val = float(raw_spread)
                            
                            # Determine Outcome (HOME/AWAY/OVER/UNDER)
                            # We use outcome_index conventions and confirm with strings if available
                            idx = entry.get('outcome_index')
                            outcome_type = None

                            if market_type == 'moneyline':
                                if idx == 1: outcome_type = 'HOME'
                                elif idx == 0: outcome_type = 'AWAY'
                            elif market_type == 'total':
                                if 'o' in raw_spread.lower() or idx == 0: outcome_type = 'OVER'
                                elif 'u' in raw_spread.lower() or idx == 1: outcome_type = 'UNDER'
                            elif market_type == 'spread':
                                # Typically idx 1 is Home (Favorite usually negative), idx 0 is Away
                                if idx == 1: outcome_type = 'HOME'
                                elif idx == 0: outcome_type = 'AWAY'

                            if outcome_type:
                                oo_points.append({
                                    'line': line_val,
                                    'outcome': outcome_type,
                                    'prob': prob
                                })
                        except ValueError:
                            continue

                # --- 2. Calculate Targets for Bias ---
                # A 'target' is the bias required to make HOS equal OO for a specific data point.
                # We assume: Prob_Final = Prob_HOS + (Bias * Direction)
                # Direction is +1 for Primary (Home/Over), -1 for Secondary (Away/Under)
                targets = []

                for hos_line in hos_data:
                    h_line_val = hos_line.get('line')
                    # DEBUG: Print the line being checked
                    # print(f"Checking House Line: {h_line_val} for {market_type}")
                    
                    for sel in hos_line.get('selections', []):
                        # Normalize HOS prob to 0-100 scale to match Optic Odds
                        h_prob = sel.get('prob') * 100 
                        h_outcome = sel.get('outcome') # HOME, AWAY, OVER, UNDER
                        
                        # Find matching OO points
                        for oo in oo_points:
                            is_match = False
                            
                            # A. Match Lines
                            if market_type == 'moneyline':
                                is_match = True
                            elif market_type == 'total':
                                # Match if totals are within small margin (float precision)
                                if h_line_val is not None and oo['line'] is not None:
                                    if abs(float(h_line_val) - oo['line']) < 0.01:
                                        is_match = True
                            elif market_type == 'spread':
                                # HOS line is usually the Home spread.
                                # If HOS is -7: Home is -7, Away is +7.
                                target_spread = float(h_line_val) if h_outcome == 'HOME' else -1 * float(h_line_val)
                                
                                if oo['line'] is not None:
                                    if abs(oo['line'] - target_spread) < 0.01:
                                        is_match = True

                            if not is_match: continue

                            # B. Match Outcomes & Calculate Target Bias
                            if h_outcome == oo['outcome']:
                                # Difference between Market and House
                                diff = oo['prob'] - h_prob
                                
                                # If we are looking at Home/Over, Bias adds to probability.
                                # Bias = Market - House
                                if h_outcome in ['HOME', 'OVER']:
                                    targets.append(diff)
                                
                                # If we are looking at Away/Under, Bias subtracts from probability.
                                # Market = House - Bias  =>  Bias = House - Market
                                else:
                                    targets.append(-diff)

                # --- 3. Compute Statistics ---
                if targets:
                    # Optimal bias is the mean of all required adjustments
                    optimal_bias:float = np.mean(targets)
                    
                    # SSE: Sum of Squared Errors based on this optimal bias
                    sse = np.sum([(t - optimal_bias) ** 2 for t in targets])
                    
                    print(f"{game_name[:38]:<40} | {market_type:<10} | {optimal_bias:>11.4f}% | {sse:>12.4f} | {len(targets)}")
                    
                    results.append({
                        "game": game_name,
                        "market": market_type,
                        "bias": optimal_bias,
                        "sse": sse,
                        "hos_event_id": game.get("ids", {}).get("hos"),
                        "hos_market_id": game.get("hos_main_lines", {}).get(market_type, {}).get("marketId"),
                        # "new_bias": optimal_bias + game.get("hos_main_lines", {}).get(market_type, {}).get("selections", [{}])[0].get("bias"),
                        # HOS bias is stored as a decimal (e.g. 0.04 for +4%).
                        # `optimal_bias` is computed in percent-points (0-100) because we compare to OO probs in 0-100.
                        # Convert percent-points -> decimal before accumulating.
                        "new_bias": float(hos_data[0].get('selections')[0].get('bias') or 0.0) + (optimal_bias / 100.0),
                    })

        return results

    # --- Execution ---
    # Load the data (assuming the json content provided in the prompt is saved or passed directly)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    try:
        with open(os.path.join(BASE_DIR, 'consolidated_odds_all_books.json'), "r") as f:
        # with open("consolidated_odds_all_books.json", "r") as f:
            data = json.load(f)
            results: list = solve_optimal_bias(data)
            return results
    except FileNotFoundError:
        print("Error: File 'consolidated_odds_all_books.json' not found. Please ensure the file is in the directory.")
def runner2() -> list[dict]:
    import json
    import numpy as np
    import os
    def solve_optimal_bias2(data):
    # Header for the output table
        header = f"{'Game':<40} | {'Market':<10} | {'Delta (pp)':<12} | {'New Bias (%)':<12} | {'Matches'}"
        print(header)
        print("-" * len(header))

        results = []

        for game in data:
            game_name = game.get('game_matchup', 'Unknown')
            markets = game.get('markets', {})

            # We analyze three distinct market types
            for market_type in ['moneyline', 'spread', 'total']:
                market_data = markets.get(market_type, {})
                optic_odds = market_data.get('optic_odds', {})
                hos_data = market_data.get('hos', [])

                # Skip if we don't have House data to compare against
                if not hos_data:
                    continue

                # --- 1. Flatten Optic Odds Data ---
                oo_points = []
                for book, entries in optic_odds.items():
                    if not isinstance(entries, list): continue
                    for entry in entries:
                        try:
                            prob_str = str(entry.get('probability', '0')).replace('%', '')
                            if not prob_str or prob_str == 'nan': continue
                            prob = float(prob_str)

                            raw_spread = str(entry.get('spread', ''))
                            line_val = None
                            
                            if market_type == 'total':
                                clean = raw_spread.lower().replace('o', '').replace('u', '')
                                if clean: line_val = float(clean)
                            elif market_type == 'spread':
                                if raw_spread: line_val = float(raw_spread)
                            
                            idx = entry.get('outcome_index')
                            outcome_type = None

                            if market_type == 'moneyline':
                                if idx == 1: outcome_type = 'HOME'
                                elif idx == 0: outcome_type = 'AWAY'
                            elif market_type == 'total':
                                if 'o' in raw_spread.lower() or idx == 0: outcome_type = 'OVER'
                                elif 'u' in raw_spread.lower() or idx == 1: outcome_type = 'UNDER'
                            elif market_type == 'spread':
                                if idx == 1: outcome_type = 'HOME'
                                elif idx == 0: outcome_type = 'AWAY'

                            if outcome_type:
                                oo_points.append({'line': line_val, 'outcome': outcome_type, 'prob': prob})
                        except ValueError:
                            continue

                # --- 2. Calculate Targets for Bias ---
                targets = []
                
                # SAFEGUARD: Extract Existing Bias Here
                # We look at the first available HOS line to find the current bias applied
                existing_bias = 0.0
                try:
                    # Iterate to find the first valid bias, or default to 0.0
                    if hos_data and 'selections' in hos_data[0]:
                        existing_bias = float(hos_data[0]['selections'][0].get('bias', 0.0))
                except (IndexError, TypeError, ValueError):
                    existing_bias = 0.0

                for hos_line in hos_data:
                    h_line_val = hos_line.get('line')
                    
                    for sel in hos_line.get('selections', []):
                        h_prob = sel.get('prob') * 100 
                        h_outcome = sel.get('outcome')
                        
                        for oo in oo_points:
                            is_match = False
                            
                            if market_type == 'moneyline':
                                is_match = True
                            elif market_type == 'total':
                                if h_line_val is not None and oo['line'] is not None:
                                    if abs(float(h_line_val) - oo['line']) < 0.01:
                                        is_match = True
                            elif market_type == 'spread':
                                target_spread = float(h_line_val) if h_outcome == 'HOME' else -1 * float(h_line_val)
                                if oo['line'] is not None:
                                    if abs(oo['line'] - target_spread) < 0.01:
                                        is_match = True

                            if not is_match: continue

                            if h_outcome == oo['outcome']:
                                diff = oo['prob'] - h_prob
                                
                                # Calculate the adjustment needed (Delta)
                                if h_outcome in ['HOME', 'OVER']:
                                    targets.append(diff)
                                else:
                                    targets.append(-diff)

                # --- 3. Compute Statistics ---
                if targets:
                    # calculated_delta is the amount we need to shift the CURRENT odds
                    calculated_delta_pct_points = float(np.mean(targets))

                    # Units:
                    # - `existing_bias` from HOS is a decimal probability bias (0-1), e.g. 0.04 == +4%.
                    # - `targets`/`calculated_delta` are percent-points because we compared OO probs (0-100) vs HOS prob*100.
                    # Convert percent-points -> decimal before accumulating.
                    calculated_delta_decimal = calculated_delta_pct_points / 100.0

                    # new_total_bias_decimal is the absolute bias to apply (decimal 0-1)
                    new_total_bias_decimal = existing_bias + calculated_delta_decimal

                    # For display/debugging convenience
                    new_total_bias_pct = new_total_bias_decimal * 100.0

                    sse = np.sum([(t - calculated_delta_pct_points) ** 2 for t in targets])
                    
                    print(f"{game_name[:38]:<40} | {market_type:<10} | {calculated_delta_pct_points:>11.4f}pp | {new_total_bias_pct:>11.4f}% | {len(targets)}")
                    
                    results.append({
                        "game": game_name,
                        "market": market_type,
                        # Delta required (percent-points) and equivalent decimal value
                        "delta_adjustment_pct_points": calculated_delta_pct_points,
                        "delta_adjustment_decimal": calculated_delta_decimal,
                        # Bias values (decimal is the value to send to HOS)
                        "existing_bias_decimal": existing_bias,
                        "new_total_bias_decimal": round(new_total_bias_decimal,2),
                        "new_total_bias_pct": new_total_bias_pct,
                        "sse": sse,
                        "hos_event_id": game.get("ids", {}).get("hos"),
                        "hos_market_id": game.get("hos_main_lines", {}).get(market_type, {}).get("marketId"),
                        "status": game.get("hos_main_lines", {}).get(market_type, {}).get("status")
                    })

        return results
    # --- Execution ---    # --- Execution ---
    # Load the data (assuming the json content provided in the prompt is saved or passed directly)
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(BASE_DIR, 'consolidated_odds_all_books.json'), "r") as f:
        # with open("consolidated_odds_all_books.json", "r") as f:
            data = json.load(f)
            results: list = solve_optimal_bias2(data)
            return results
    except FileNotFoundError:
        print("Error: File 'consolidated_odds_all_books.json' not found. Please ensure the file is in the directory.")
