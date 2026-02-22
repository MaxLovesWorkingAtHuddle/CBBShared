def runner(odds_data, matched_games):
    import json
    import os
    # Load the data files
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # with open(os.path.join(BASE_DIR, 'odds_dump.json'), "r") as f:
    # # with open('odds_dump.json', 'r') as f:
    #     odds_data = json.load(f)
    # with open(os.path.join(BASE_DIR, 'matched_games.json'), "r") as f:
    # # with open('matched_games.json', 'r') as f:
    #     matched_games = json.load(f)

    # odds_data = json.loads(odds_data)
    # matched_games = json.loads(matched_games)
    # Helper to build HOS lookup
    hos_events_lookup = {}
    if 'hos' in odds_data and 'data' in odds_data['hos'] and 'data' in odds_data['hos']['data'] and 'events' in odds_data['hos']['data']['data']:
        try:
            hos_nodes = odds_data['hos']['data']['data']['events'].get('nodes', [])
        except (KeyError, TypeError, AttributeError):
            hos_nodes = []
        for event in hos_nodes:
            hos_events_lookup[event['eventId']] = event

    # Helper to build OO -> HOS ID mapping
    oo_to_hos_id = {}
    for match in matched_games:
        oo_to_hos_id[match['oo_game_id']] = match['hos_event_id']

    # Helper to format HOS odds
    def format_hos_odds(price_info):
        if not price_info: return None
        val = price_info.get('value')
        if val is None: return None
        sign = "+" if price_info.get('signIsPlus') else "-"
        return f"{sign}{val}"

    # Helper to extract HOS markets
    def extract_hos_markets(hos_event, market_code_filter):
        extracted_markets = []
        if not hos_event or 'markets' not in hos_event:
            return extracted_markets
        
        for market in hos_event['markets'].get('nodes', []):
            if market.get('marketCode') != market_code_filter:
                continue
            if market.get('offeringStatus') != 'ACTIVE': # Check active status based on example? Example says "status": "ACTIVE"
                pass # keeping all, but noted the example status.
            
            market_obj = {
                "marketId": market.get('marketId'),
                "line": market.get('marketType', {}).get('params', {}).get('LINE'),
                "status": market.get('offeringStatus'),
                "selections": []
            }
            
            is_main_line = market.get('marketSummary', {}).get('isMainLine', False)
            is_result = (market.get('marketCode') == 'RESULT')

            for sel in market.get('selections', []):
                price = sel.get('price', {})
                formatted = price.get('originalFormattedValue', {})
                
                sel_obj = {
                    "outcome": sel.get('selectionType', {}).get('selectionCode'),
                    "odds": format_hos_odds(formatted),
                    "decimal": price.get('decimalValue'),
                    "prob": price.get('probability') + price.get('bias'),
                    "bias": price.get('bias'),
                    "isMainLine": is_main_line
                    # "offeringStatus": price.get()
                }
                
                if is_main_line or is_result:
                    sel_obj['mainLine'] = market.get('marketSummary', {}).get('mainLine')
                    sel_obj['marketId'] = market.get('marketId')

                market_obj['selections'].append(sel_obj)
            
            extracted_markets.append(market_obj)
        return extracted_markets

    # Main processing
    consolidated_data = []

    # Get the set of all OO game IDs from the moneyline section (assuming it's the master list)
    # We also check other markets just in case
    oo_game_ids = set()
    if 'optic_odds' in odds_data:
        for mkt in ['moneyline', 'point_spread', 'total_points']:
            if mkt in odds_data['optic_odds'] and 'events' in odds_data['optic_odds'][mkt]:
                oo_game_ids.update(odds_data['optic_odds'][mkt]['events'].keys())

    # Iterate through all games
    # for game_id in oo_game_ids:
    #     # Basic Info
    #     # Try to find names in moneyline first, then spread, then total
    #     team_names = {}
    #     for mkt in ['moneyline', 'point_spread', 'total_points']:
    #         if 'optic_odds' in odds_data and mkt in odds_data['optic_odds']:
    #             names = odds_data['optic_odds'][mkt].get('team_names', {}).get(game_id)
    #             if names:
    #                 team_names = names
    #                 break
        
    #     matchup = team_names.get('display', 'Unknown vs Unknown')
    for game_id in oo_game_ids:
        # Basic Info
        # Try to find names in moneyline first, then spread, then total
        team_names = {}
        for mkt in ['moneyline', 'point_spread', 'total_points']:
            if 'optic_odds' in odds_data and mkt in odds_data['optic_odds']:
                # FIX: Handle case where 'team_names' key exists but value is None
                market_data = odds_data['optic_odds'][mkt]
                all_names = market_data.get('team_names') or {} 
                
                names = all_names.get(game_id)
                if names:
                    team_names = names
                    break
        
        matchup = team_names.get('display', 'Unknown vs Unknown')    
        # IDs
        # The game_id in odds_dump usually has `_default` or similar suffix sometimes, 
        # but looking at the file content in previous turns, keys were like "18477-12313-2026-01-11_default"
        # The matched_games.json has "oo_game_id": "18477-12313-2026-01-11" (no _default)
        # We need to handle this key mismatch.
        
        clean_game_id = game_id.replace('_default', '')
        hos_id = oo_to_hos_id.get(clean_game_id)
        
        game_obj = {
            "game_matchup": matchup,
            "ids": {
                "optic_odds": clean_game_id,
                "hos": hos_id
            },
            "hos_main_lines": {},
            "markets": {}
        }
        
        # Get HOS Event Data if available
        hos_event_data = hos_events_lookup.get(hos_id)
        
        # Process Markets
        # Mapping OO market names to HOS market codes
        market_map = {
            'moneyline': {'hos_code': 'RESULT', 'out_name': 'moneyline'},
            'point_spread': {'hos_code': 'POINT_HANDICAP', 'out_name': 'spread'},
            'total_points': {'hos_code': 'POINT_OVER_UNDER', 'out_name': 'total'}
        }
        
        for oo_market, config in market_map.items():
            out_name = config['out_name']
            hos_code = config['hos_code']
            
            market_data = {
                "optic_odds": {},
                "hos": []
            }
            
            # Optic Odds Data
            if 'optic_odds' in odds_data and oo_market in odds_data['optic_odds']:
                events = odds_data['optic_odds'][oo_market].get('events', {})
                if game_id in events:
                    # Copy all bookmakers
                    # The user wants "best_price", "avg_price" keys. 
                    # The raw data has "bestPrice", "averagePrice". I will rename them to match the example format (snake_case)
                    # and keep other bookmakers as is (usually Title Case e.g. "DraftKings")
                    
                    raw_oo_books = events[game_id]
                    if isinstance(raw_oo_books, dict):
                        for book, odds_list in raw_oo_books.items():
                            key = book
                            if book == 'bestPrice': key = 'best_price'
                            if book == 'averagePrice': key = 'avg_price'
                            market_data['optic_odds'][key] = odds_list
                    else:
                        # Optional: Log the error or handle the string case
                        print(f"Warning: Expected dict for game_id {game_id}, but got {type(raw_oo_books)}")

            # HOS Data
            # if hos_event_data:
            #     market_data['hos'] = extract_hos_markets(hos_event_data, hos_code)
            # if hos_event_data:
            #     extracted = extract_hos_markets(hos_event_data, hos_code)
            #     market_data['hos'] = extracted
                
            #     # Provide direct access to the main line
            #     for mkt in extracted:
            #         if mkt['selections'] and mkt['selections'][0].get('isMainLine', False):
            #             market_data['hos_main_line'] = mkt
            #             game_obj['hos_main_lines'][out_name] = mkt
            #             break
            if hos_event_data:
                extracted = extract_hos_markets(hos_event_data, hos_code)
                market_data['hos'] = extracted
                
                # Provide direct access to the main line
                for mkt in extracted:
                    is_result = (hos_code == 'RESULT')
                    is_marked_main = (mkt['selections'] and mkt['selections'][0].get('isMainLine', False))
                    
                    if is_marked_main or is_result:
                        market_data['hos_main_line'] = mkt
                        game_obj['hos_main_lines'][out_name] = mkt
                        break
            game_obj['markets'][out_name] = market_data

        consolidated_data.append(game_obj)

    # Save to file
    # with open(os.path.join(BASE_DIR, 'consolidated_odds_all_books.json'), "w") as f:
    # # with open('consolidated_odds_all_books.json', 'w') as f:
    #     json.dump(consolidated_data, f, indent=2)
    try:
        return json.dumps(consolidated_data)
        print("Data consolidated successfully.")
    except Exception as e:
        print(f"Error code: final_stretch3qpartial return bad. Error Message: {e}")
        return {}
# def runner():
#     import json
#     # Load the data files
#     with open('odds_dump.json', 'r') as f:
#         odds_data = json.load(f)

#     with open('matched_games.json', 'r') as f:
#         matched_games = json.load(f)

#     # Helper to build HOS lookup
#     hos_events_lookup = {}
#     if 'hos' in odds_data and 'data' in odds_data['hos'] and 'data' in odds_data['hos']['data'] and 'events' in odds_data['hos']['data']['data']:
#         hos_nodes = odds_data['hos']['data']['data']['events'].get('nodes', [])
#         for event in hos_nodes:
#             hos_events_lookup[event['eventId']] = event

#     # Helper to build OO -> HOS ID mapping
#     oo_to_hos_id = {}
#     for match in matched_games:
#         oo_to_hos_id[match['oo_game_id']] = match['hos_event_id']

#     # Helper to format HOS odds
#     def format_hos_odds(price_info):
#         if not price_info: return None
#         val = price_info.get('value')
#         if val is None: return None
#         sign = "+" if price_info.get('signIsPlus') else "-"
#         return f"{sign}{val}"

#     # Helper to extract HOS markets
#     def extract_hos_markets(hos_event, market_code_filter):
#         extracted_markets = []
#         if not hos_event or 'markets' not in hos_event:
#             return extracted_markets
        
#         for market in hos_event['markets'].get('nodes', []):
#             if market.get('marketCode') != market_code_filter:
#                 continue
#             if market.get('offeringStatus') != 'ACTIVE': # Check active status based on example? Example says "status": "ACTIVE"
#                 pass # keeping all, but noted the example status.
            
#             market_obj = {
#                 "line": market.get('marketType', {}).get('params', {}).get('LINE'),
#                 "status": market.get('offeringStatus'),
#                 "selections": []
#             }
            
#             is_main_line = market.get('marketSummary', {}).get('isMainLine', False)
#             for sel in market.get('selections', []):
#                 price = sel.get('price', {})
#                 formatted = price.get('originalFormattedValue', {})
                
#                 sel_obj = {
#                     "outcome": sel.get('selectionType', {}).get('selectionCode'),
#                     "odds": format_hos_odds(formatted),
#                     "decimal": price.get('decimalValue'),
#                     "prob": price.get('probability') + price.get('bias'),
#                     "bias": price.get('bias'),
#                     "isMainLine": is_main_line
#                 }
                
#                 if is_main_line:
#                     sel_obj['mainLine'] = market.get('marketSummary', {}).get('mainLine')
#                     sel_obj['marketId'] = market.get('marketId')

#                 market_obj['selections'].append(sel_obj)
            
#             extracted_markets.append(market_obj)
#         return extracted_markets

#     # Main processing
#     consolidated_data = []

#     # Get the set of all OO game IDs from the moneyline section (assuming it's the master list)
#     # We also check other markets just in case
#     oo_game_ids = set()
#     if 'optic_odds' in odds_data:
#         for mkt in ['moneyline', 'point_spread', 'total_points']:
#             if mkt in odds_data['optic_odds'] and 'events' in odds_data['optic_odds'][mkt]:
#                 oo_game_ids.update(odds_data['optic_odds'][mkt]['events'].keys())

#     # Iterate through all games
#     for game_id in oo_game_ids:
#         # Basic Info
#         # Try to find names in moneyline first, then spread, then total
#         team_names = {}
#         for mkt in ['moneyline', 'point_spread', 'total_points']:
#             if 'optic_odds' in odds_data and mkt in odds_data['optic_odds']:
#                 names = odds_data['optic_odds'][mkt].get('team_names', {}).get(game_id)
#                 if names:
#                     team_names = names
#                     break
        
#         matchup = team_names.get('display', 'Unknown vs Unknown')
        
#         # IDs
#         # The game_id in odds_dump usually has `_default` or similar suffix sometimes, 
#         # but looking at the file content in previous turns, keys were like "18477-12313-2026-01-11_default"
#         # The matched_games.json has "oo_game_id": "18477-12313-2026-01-11" (no _default)
#         # We need to handle this key mismatch.
        
#         clean_game_id = game_id.replace('_default', '')
#         hos_id = oo_to_hos_id.get(clean_game_id)
        
#         game_obj = {
#             "game_matchup": matchup,
#             "ids": {
#                 "optic_odds": clean_game_id,
#                 "hos": hos_id
#             },
#             "hos_main_lines": {},
#             "markets": {}
#         }
        
#         # Get HOS Event Data if available
#         hos_event_data = hos_events_lookup.get(hos_id)
        
#         # Process Markets
#         # Mapping OO market names to HOS market codes
#         market_map = {
#             'moneyline': {'hos_code': 'RESULT', 'out_name': 'moneyline'},
#             'point_spread': {'hos_code': 'POINT_HANDICAP', 'out_name': 'spread'},
#             'total_points': {'hos_code': 'POINT_OVER_UNDER', 'out_name': 'total'}
#         }
        
#         for oo_market, config in market_map.items():
#             out_name = config['out_name']
#             hos_code = config['hos_code']
            
#             market_data = {
#                 "optic_odds": {},
#                 "hos": []
#             }
            
#             # Optic Odds Data
#             if 'optic_odds' in odds_data and oo_market in odds_data['optic_odds']:
#                 events = odds_data['optic_odds'][oo_market].get('events', {})
#                 if game_id in events:
#                     # Copy all bookmakers
#                     # The user wants "best_price", "avg_price" keys. 
#                     # The raw data has "bestPrice", "averagePrice". I will rename them to match the example format (snake_case)
#                     # and keep other bookmakers as is (usually Title Case e.g. "DraftKings")
                    
#                     raw_oo_books = events[game_id]
#                     for book, odds_list in raw_oo_books.items():
#                         key = book
#                         if book == 'bestPrice': key = 'best_price'
#                         if book == 'averagePrice': key = 'avg_price'
#                         market_data['optic_odds'][key] = odds_list

#             # HOS Data
#             # if hos_event_data:
#             #     market_data['hos'] = extract_hos_markets(hos_event_data, hos_code)
#             # if hos_event_data:
#             #     extracted = extract_hos_markets(hos_event_data, hos_code)
#             #     market_data['hos'] = extracted
                
#             #     # Provide direct access to the main line
#             #     for mkt in extracted:
#             #         if mkt['selections'] and mkt['selections'][0].get('isMainLine', False):
#             #             market_data['hos_main_line'] = mkt
#             #             game_obj['hos_main_lines'][out_name] = mkt
#             #             break
#             if hos_event_data:
#                 extracted = extract_hos_markets(hos_event_data, hos_code)
#                 market_data['hos'] = extracted
                
#                 # Provide direct access to the main line
#                 for mkt in extracted:
#                     is_result = (hos_code == 'RESULT')
#                     is_marked_main = (mkt['selections'] and mkt['selections'][0].get('isMainLine', False))
                    
#                     if is_marked_main or is_result:
#                         market_data['hos_main_line'] = mkt
#                         game_obj['hos_main_lines'][out_name] = mkt
#                         break
#             game_obj['markets'][out_name] = market_data

#         consolidated_data.append(game_obj)

#     # Save to file
#     with open('consolidated_odds_all_books.json', 'w') as f:
#         json.dump(consolidated_data, f, indent=2)

#     print("Data consolidated successfully.")