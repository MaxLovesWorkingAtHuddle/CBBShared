import json
import os
from urllib.parse import urlparse, parse_qs
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.layout import Layout
from thefuzz import process, fuzz
from datetime import datetime


masterURL = "https://backoffice-huddle.netlify.app/operations/trading-ui/multiview?ids=cbae8e31-55d8-40b7-a292-238a7cd6abf9&ids=2c0c0329-2d97-4fa8-beb0-dafda3e60024&client=Huddle"
UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (CBB1)
BASE_DIR = os.path.dirname(UTILS_DIR)
MATCHED_FILE = os.path.join(BASE_DIR, "utilsIM", "matched_games.json")
OO_FILE = os.path.join(BASE_DIR, "utilsIM", "1parsedOO.json")
HOS_FILE = os.path.join(BASE_DIR, "utilsIM", "1parsedHOS.json")
console = Console()
def load_json(filename):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        console.print(f"[red]Error: {filename} not found.[/red]")
        return []

def save_matched(data):
    with open(MATCHED_FILE, "w") as f:
        json.dump(data, f, indent=4)
    console.print(f"[green]Saved to {MATCHED_FILE}[/green]")

def main(masterURL):
    # 1. Load Data
    # --- Configuration ---

    date = str(datetime.now()).split(" ")[0]
    matched_data = load_json(MATCHED_FILE)
    hos_parsed = load_json(HOS_FILE)
    oo_parsed = load_json(OO_FILE)
    oo_parsed = [i for i in oo_parsed if i["oo_game_id"].endswith(date)]
    # 2. Extract Missing IDs from URL
    existing_ids = {item.get("hos_event_id") for item in matched_data}
    
    parsed_url = urlparse(masterURL)
    query_params = parse_qs(parsed_url.query)
    url_ids = query_params.get("ids", [])
    
    # Filter for IDs that are NOT in matched_games.json
    missing_ids = [uid for uid in url_ids if uid not in existing_ids]
    
    console.print(f"[bold blue]Found {len(missing_ids)} IDs missing from {MATCHED_FILE}[/bold blue]\n")

    # 3. Prepare Search Corpus (Optic Odds)
    # create a dict for fast lookup by "Home vs Away" string for fuzzy matching
    oo_choices = {}
    for item in oo_parsed:
        # Create a search key. Adjust keys if your JSON uses different names
        key = f"{item.get('oo_home')} {item.get('oo_away')}"
        oo_choices[key] = item

    # 4. Iterate and Match
    for index, missing_id in enumerate(missing_ids):
        # Find the specific HOS game object
        hos_game = next((g for g in hos_parsed if g.get("hos_event_id") == missing_id), None)
        
        if not hos_game:
            console.print(f"[red]Warning: ID {missing_id} not found in {HOS_FILE}. Skipping.[/red]")
            continue

        # Construct HOS search string
        hos_search_str = f"{hos_game.get('hos_home')} {hos_game.get('hos_away')}"

        # --- TUI DISPLAY ---
        console.rule(f"[bold yellow]Match {index + 1}/{len(missing_ids)}[/bold yellow]")
        
        # Display HOS Target
        hos_panel = Panel(
            f"[bold]Home:[/bold] {hos_game.get('hos_home')}\n"
            f"[bold]Away:[/bold] {hos_game.get('hos_away')}\n"
            f"[dim]ID: {missing_id}[/dim]",
            title="🎯 TARGET (House of Sports)",
            border_style="cyan"
        )
        console.print(hos_panel)

        # Fuzzy Search
        matches = process.extract(
            hos_search_str, 
            oo_choices.keys(), 
            limit=5, 
            scorer=fuzz.token_sort_ratio
        )

        # Display Candidates Table
        table = Table(title="Top 5 Matches (Optic Odds)", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Score", justify="right")
        table.add_column("Home Team")
        table.add_column("Away Team")
        table.add_column("OO ID")

        candidate_objs = []
        
        for i, (match_key, score) in enumerate(matches):
            cand_obj = oo_choices[match_key]
            candidate_objs.append(cand_obj)
            
            # Color code score
            score_color = "green" if score > 80 else "yellow" if score > 60 else "red"
            
            table.add_row(
                str(i + 1),
                f"[{score_color}]{score}[/{score_color}]",
                cand_obj.get("oo_home", "N/A"),
                cand_obj.get("oo_away", "N/A"),
                cand_obj.get("oo_game_id", "N/A")
            )

        console.print(table)

        # User Input
        choice = Prompt.ask(
            "Select match", 
            choices=["1", "2", "3", "4", "5", "s", "q"], 
            default="1"
        )

        if choice == "q":
            break
        
        if choice == "s":
            console.print("[yellow]Skipped.[/yellow]")
            continue

        # 5. Merge and Save
        selected_index = int(choice) - 1
        selected_oo = candidate_objs[selected_index]
        
        # Merge dictionaries (OO + HOS)
        # We start with OO, then update with HOS to ensure we keep HOS IDs if keys clash (or vice versa)
        # Based on your prompt example, it's a flat merge.
        merged_game = selected_oo.copy()
        merged_game.update(hos_game)

        matched_data.append(merged_game)
        
        # Save immediately to prevent data loss
        save_matched(matched_data)
        console.print("[bold green]Match Confirmed & Saved![/bold green]\n")

    console.print("[bold green]Process Complete.[/bold green]")

if __name__ == "__main__":
    main(masterURL= masterURL)
