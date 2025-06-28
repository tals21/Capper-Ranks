import re
from typing import Tuple, Optional
from ..core.mappings import TEAM_LEAGUE_MAP

def _find_team_and_league_from_subject(subject_text: str) -> Tuple[Optional[str], Optional[str]]:
    """Given a potential subject text, finds the longest matching alias and its league."""
    subject_lower = subject_text.lower()
    # Find all possible aliases that match the end of the subject string
    possible_matches = [alias for alias in TEAM_LEAGUE_MAP.keys() if subject_lower.endswith(alias)]
    if not possible_matches:
        return None, None
    
    # Return the longest matching alias to handle "New York Yankees" over "Yankees"
    best_match = max(possible_matches, key=len)
    return best_match, TEAM_LEAGUE_MAP[best_match]

def _detect_mlb_pick(tweet_text: str):
    """Contains all pick detection logic specifically for MLB."""
    
    # --- Detection Priority 1: Run Lines (Spreads) ---
    # Looks for a team name followed by a spread like -1.5 or +1.5
    # The team name part is non-greedy (.*?) to capture the shortest possible text.
    run_line_match = re.search(r"\b(.*?)\s*([+-]\d{1,2}(?:\.5)?)\b", tweet_text, re.IGNORECASE)
    if run_line_match:
        subject, line_str = run_line_match.groups()
        team_alias, league = _find_team_and_league_from_subject(subject)
        if league == 'MLB':
            print(f"  DEBUG: Found Run Line pick: {team_alias} {line_str}")
            return {'sport_league': 'MLB', 'subject': team_alias, 'bet_type': 'Spread', 'line': float(line_str), 'odds': None, 'bet_qualifier': 'Full Game'}

    # --- Detection Priority 2: Moneyline (ML) ---
    ml_match = re.search(r"\b(.*?)\s+ML\b", tweet_text, re.IGNORECASE)
    if ml_match:
        subject = ml_match.group(1).strip()
        team_alias, league = _find_team_and_league_from_subject(subject)
        if league == 'MLB':
            print(f"  DEBUG: Found Moneyline pick: {team_alias}")
            return {'sport_league': 'MLB', 'subject': team_alias, 'bet_type': 'Moneyline', 'line': None, 'odds': None, 'bet_qualifier': 'Full Game'}

    # --- Detection Priority 3: Totals (Over/Under) ---
    total_match = re.search(r"(over|under|o/u)\s*(\d+\.?\d*)", tweet_text, re.IGNORECASE)
    if total_match:
        qualifier = "Over" if total_match.group(1).lower().startswith('o') else "Under"
        line = float(total_match.group(2))
        # For a total, we need to find which game it refers to. Find the first MLB team mentioned.
        team_context, league = _find_sport_context(tweet_text) # Re-using your original helper for context
        if league == 'MLB':
            print(f"  DEBUG: Found Total pick: {qualifier} {line} for a game involving '{team_context}'")
            # For F5 bets, we can add a check here for "F5" or "First 5" in the tweet text
            bet_qualifier = "First 5" if "f5" in tweet_text.lower() or "first 5" in tweet_text.lower() else "Full Game"
            return {'sport_league': 'MLB', 'subject': team_context, 'bet_type': 'Total', 'line': line, 'odds': None, 'bet_qualifier': f"{qualifier} {bet_qualifier}"}

    return None

def _detect_nfl_pick(tweet_text: str):
    """[PLACEHOLDER] This is where you will add detection logic for NFL picks."""
    pass
    return None

def _detect_nba_pick(tweet_text: str):
    """[PLACEHOLDER] This is where you will add detection logic for NBA picks."""
    pass
    return None

# --- Main Dispatcher Function (Updated) ---

def detect_pick(tweet_text: str):
    """
    Main dispatcher function. It determines the sport context and routes to the
    appropriate specialized detection function.
    """
    print(f"----- Analyzing: '{tweet_text}' -----")
    
    # For now, we will just run the MLB detector. In the future, this dispatcher can be made smarter.
    # It could look for keywords for each sport first.
    
    detected_leg = _detect_mlb_pick(tweet_text)
    
    if detected_leg:
        # We return the pick as a list to support parlays later
        return [detected_leg]
    
    # Logic for other sports would be called here
    # detected_leg = _detect_nfl_pick(tweet_text)
    # if detected_leg:
    #     return [detected_leg]

    print("  DEBUG: No recognizable pick format found.")
    return None

# --- Original Helper Function (still used by Totals logic) ---

def _find_sport_context(tweet_text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Scans the tweet for ALL known team aliases, and returns the one that
    appears EARLIEST in the string to correctly determine the context.
    """
    found_matches = []
    
    # First, find every possible team match and its starting position in the tweet
    for team_alias in TEAM_LEAGUE_MAP.keys():
        # finditer finds all non-overlapping matches
        for match in re.finditer(r'\b' + re.escape(team_alias) + r'\b', tweet_text, re.IGNORECASE):
            # Store the match's start index, the alias found, and its league
            found_matches.append((match.start(), team_alias, TEAM_LEAGUE_MAP[team_alias]))

    if not found_matches:
        return None, None # No teams were found at all

    # Sort the list of matches by their starting position (the first item in our tuple)
    found_matches.sort(key=lambda x: x[0])
    
    # The first item in the sorted list is the one that appeared earliest in the tweet
    earliest_match = found_matches[0]
    
    # Return the alias (item 1) and league (item 2) of the earliest match
    return earliest_match[1], earliest_match[2]