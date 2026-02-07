import json
import csv
import re

# 1. Load your content
# We use 'utf-8' encoding to safely read the file
try:
    with open('cbbOOapicalls\\totalresponse.txt', 'r', encoding='utf-8') as f:
        raw_text = f.read()
except FileNotFoundError:
    print("Error: The file 'reloadtestrespsonse.txt' was not found in the same folder.")
    exit()

# 2. Clean the data
# This specific regex removes the "" tags found in your file
# The error was previously caused by an incomplete pattern here
clean_text = re.sub('\\\\', '', raw_text)
# 3. Parse JSON
try:
    data = json.loads(clean_text)
except json.JSONDecodeError as e:
    print(f"Error parsing JSON: {e}")
    # Optional: Print part of the text to see where it failed
    # print(clean_text[:100]) 
    exit()

# 4. Extract Column Headers
headers = ['Date', 'Game', 'Team', 'Side']
# Add sportsbook names from the 'columns' section of the JSON
sb_columns = [col['sb'] for col in data.get('columns', [])]
headers.extend(sb_columns)

# 5. Process Rows
csv_rows = []

if 'rows' in data:
    for row in data['rows']:
        # Get Game Metadata using the fixture ID (f)
        fixture_id = row.get('f')
        fixture = data.get('fixtures', {}).get(fixture_id, {})
        
        # Metadata fields
        game_date = fixture.get('start_date', '').split('T')[0]
        home_team = fixture.get('home_team_display', 'Unknown')
        away_team = fixture.get('away_team_display', 'Unknown')
        game_name = f"{away_team} @ {home_team}"
        
        current_row = [
            game_date,
            game_name,
            row.get('n', ''),      # Team Name
            row.get('t', '')       # Side (home/away)
        ]
        
        # Get Odds Data (The 'c' array aligns with 'columns')
        for cell in row.get('c', []):
            if cell and 'pr' in cell and 'v' in cell['pr']:
                current_row.append(cell['pr']['v'])
            else:
                current_row.append('') # Empty if null or no price found
                
        csv_rows.append(current_row)

# 6. Write to CSV
output_filename = 'cbbOOapicalls\\odds_output.csv'
with open(output_filename, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(csv_rows)

print(f"Success! CSV generated at: {output_filename}")