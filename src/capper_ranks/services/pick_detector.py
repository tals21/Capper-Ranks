import re
from typing import Dict, List, Tuple, Optional
from capper_ranks.core.mappings import TEAM_LEAGUE_MAP
from capper_ranks.services import sports_api

# --- Sport-Specific Detection Logic ---

# In src/capper_ranks/services/pick_detector.py

# In src/capper_ranks/services/pick_detector.py

def _detect_player_prop(line: str) -> Optional[Dict]:
    """
    Final robust version. It finds the bet first, then works backward to
    identify the most likely player name using a precise regex.
    """
    # Step 1: Find the bet pattern itself (e.g., "Over 1.5 Total Bases"). This is our anchor.
    bet_match = re.search(
        r"(over|under|o/u|o|u)\s*(\d+\.?\d*)\s+([A-Za-z\s'’]+)",
        line,
        re.IGNORECASE
    )

    if not bet_match:
        return None

    # Step 2: Get the text that appeared directly BEFORE our bet pattern.
    text_before_bet = line[:bet_match.start()].strip()
    
    if not text_before_bet:
        return None

    # --- THIS IS THE KEY FIX ---
    # Step 3: From that preceding text, extract the capitalized name at the very end.
    # This regex looks for a pattern of 1-4 capitalized words at the end of the string ($).
    # This correctly isolates the name from surrounding verbs like "Fading" or "betting on".
    player_name_match = re.search(r"([A-Z][a-z'.-]+(?:\s[A-Z][a-z'.-]+){0,3})$", text_before_bet)
    
    if not player_name_match:
        print(f"  DEBUG: Found a prop bet, but couldn't isolate a player name from '{text_before_bet}'.")
        return None
    
    # Now we have a clean player name!
    player_name = player_name_match.group(1).strip()
    
    # --- The rest of the function proceeds as before ---
    print(f"  DEBUG: Found potential player prop for '{player_name}'. Validating...")
    league = sports_api.get_player_league(player_name)
    
    if not league:
        print(f"  DEBUG: Could not validate '{player_name}' as a player. Ignoring.")
        return None
    
    print(f"  DEBUG: Validated '{player_name}' in league '{league}'.")
    qualifier_text, line_str, prop_type = bet_match.groups()
    qualifier = "Over" if qualifier_text.lower().startswith('o') else "Under"
    
    return {
        'sport_league': league,
        'subject': player_name,
        'bet_type': 'Player Prop',
        'line': float(line_str),
        'odds': None,
        'bet_qualifier': f"{qualifier} {prop_type.strip()}"
    }

# This function is being updated to be simpler, as it only needs to check one line at a time
def _detect_team_bet(line: str) -> Optional[dict]:
    """Detects a team-based bet (ML, Spread, Total) on a single line of text."""
    team_context, sport_league = _find_sport_context(line)
    if not sport_league:
        return None

    # This function now gets the simple team context for this specific line
    return _detect_mlb_pick(line, team_context) # type: ignore # We can reuse our MLB-specific logic


def _find_sport_context(tweet_text: str) -> Tuple[Optional[str], Optional[str]]:
    found_matches = []
    for team_alias in TEAM_LEAGUE_MAP.keys():
        for match in re.finditer(r'\b' + re.escape(team_alias) + r'\b', tweet_text, re.IGNORECASE):
            found_matches.append({'alias': team_alias, 'start': match.start(), 'league': TEAM_LEAGUE_MAP[team_alias]})
    if not found_matches:
        return None, None
    earliest_match = min(found_matches, key=lambda x: x['start'])
    return earliest_match['alias'], earliest_match['league']

def _detect_mlb_pick(tweet_text: str, team_context: str):
    text_lower = tweet_text.lower()
    is_f5 = "f5" in text_lower or "first 5" in text_lower
    bet_qualifier_suffix = "First 5" if is_f5 else "Full Game"
    run_line_match = re.search(r'\b' + re.escape(team_context) + r'\s*([+-]\d\.\d)\b', text_lower, re.IGNORECASE)
    if run_line_match:
        return {'sport_league': 'MLB', 'subject': team_context, 'bet_type': 'Spread', 'line': float(run_line_match.group(1)), 'odds': None, 'bet_qualifier': bet_qualifier_suffix}
    ml_match = re.search(r'\b' + re.escape(team_context) + r'\s+ML\b', text_lower, re.IGNORECASE)
    if ml_match:
        return {'sport_league': 'MLB', 'subject': team_context, 'bet_type': 'Moneyline', 'line': None, 'odds': None, 'bet_qualifier': bet_qualifier_suffix}
    total_match = re.search(r"(over|under|o/u)\s*(\d+\.?\d*)", text_lower)
    if total_match:
        qualifier = "Over" if total_match.group(1).startswith('o') else "Under"
        return {'sport_league': 'MLB', 'subject': team_context, 'bet_type': 'Total', 'line': float(total_match.group(2)), 'odds': None, 'bet_qualifier': f"{qualifier} {bet_qualifier_suffix}"}
    return None

def _detect_nfl_pick(tweet_text: str, team_context: str): pass
def _detect_nba_pick(tweet_text: str, team_context: str): pass

def detect_pick(tweet_text: str) -> Optional[List[dict]]:
    """
    Main dispatcher. Now splits tweets by lines to find all possible picks,
    including multiple picks in one tweet (parlays).
    """
    print(f"----- Analyzing Tweet -----")
    
    all_legs = []
    # Split the tweet into individual lines to check each one
    lines = tweet_text.split('\n')
    
    for line in lines:
        if not line.strip():  # Skip empty lines
            continue

        print(f"  -- Analyzing Line: '{line}'")
        
        # Priority 1: Player Props
        detected_leg = _detect_player_prop(line)
        
        # Priority 2: Team Bets (if no player prop was found on this line)
        if not detected_leg:
            detected_leg = _detect_team_bet(line)
        
        if detected_leg:
            print(f"    ✅ LEG DETECTED: {detected_leg}")
            all_legs.append(detected_leg)

    if not all_legs:
        print("  DEBUG: No valid picks found in any line of the tweet.")
        return None

    return all_legs