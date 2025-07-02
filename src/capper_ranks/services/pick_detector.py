import re
from typing import List, Optional, Tuple, Dict
from capper_ranks.core.mappings import TEAM_LEAGUE_MAP
from capper_ranks.services import sports_api

# --- Main Helper Functions ---

def _find_sport_context(tweet_text: str) -> Tuple[Optional[str], Optional[str]]:
    """Finds the earliest mentioned team in a tweet to set the context."""
    found_matches = []
    for team_alias in TEAM_LEAGUE_MAP.keys():
        for match in re.finditer(r'\b' + re.escape(team_alias) + r'\b', tweet_text, re.IGNORECASE):
            found_matches.append({'alias': team_alias, 'start': match.start(), 'league': TEAM_LEAGUE_MAP[team_alias]})
    if not found_matches:
        return None, None
    earliest_match = min(found_matches, key=lambda x: x['start'])
    return earliest_match['alias'], earliest_match['league']

# --- Sport-Specific Detection Logic ---

# List of valid MLB player prop stat types (expand as needed)
MLB_STAT_TYPES = [
    "Total Bases", "Hits", "Home Runs", "RBIs", "Runs", "Strikeouts", "Walks", "Stolen Bases", "Hits Allowed",
    "Earned Runs", "Outs Recorded", "Runs Allowed", "Saves", "Wins", "Losses", "Innings Pitched", "Doubles", "Triples"
]

# Sort by length descending for greedy matching
MLB_STAT_TYPES = sorted(MLB_STAT_TYPES, key=lambda x: -len(x))

def _detect_player_prop(line: str) -> Optional[Dict]:
    """
    Improved: Finds the bet pattern, then matches the longest valid stat type after the number.
    """
    # Regex: (Over|Under) <number> <stat type>
    bet_match = re.search(
        r"(over|under|o/u|o|u)\s*(\d+\.?\d*)\s+(.+)",
        line,
        re.IGNORECASE
    )

    if not bet_match:
        return None

    text_before_bet = line[:bet_match.start()].strip()
    words = text_before_bet.split()
    if not words:
        return None

    # Try to find the player name (up to 4 words before the bet)
    for i in range(min(4, len(words)), 0, -1):
        name_candidate = " ".join(words[-i:])
        if not name_candidate[0].isupper():
            continue
        league = sports_api.get_player_league(name_candidate)
        if league:
            qualifier_text, line_str, stat_type_candidate = bet_match.groups()
            qualifier = "Over" if qualifier_text.lower().startswith('o') else "Under"
            # Greedily match the longest valid stat type
            stat_type = None
            for stype in MLB_STAT_TYPES:
                if stat_type_candidate.lower().startswith(stype.lower()):
                    stat_type = stype
                    break
            if not stat_type:
                # fallback: use first word after number
                stat_type = stat_type_candidate.split()[0]
            return {
                'sport_league': league,
                'subject': name_candidate,
                'bet_type': 'Player Prop',
                'line': float(line_str),
                'odds': None,
                'bet_qualifier': f"{qualifier} {stat_type}"
            }
    return None

def _detect_team_bet(line: str) -> Optional[Dict]:
    """Detects a team-based bet on a single line."""
    team_context, sport_league = _find_sport_context(line)
    if not sport_league or sport_league != 'MLB':
        return None
    
    # After finding the team, we check for specific bet patterns related to it.
    text_lower = line.lower()
    is_f5 = "f5" in text_lower or "first 5" in text_lower
    bet_qualifier_suffix = "First 5" if is_f5 else "Full Game"
    
    # Check for patterns where the team name is right next to the bet
    run_line_match = re.search(r'\b' + re.escape(team_context) + r'\s*([+-]\d\.\d)\b', text_lower, re.IGNORECASE) # type: ignore
    if run_line_match:
        return {'sport_league': 'MLB', 'subject': team_context, 'bet_type': 'Spread', 'line': float(run_line_match.group(1)), 'odds': None, 'bet_qualifier': bet_qualifier_suffix}
    
    ml_match = re.search(r'\b' + re.escape(team_context) + r'\s+ML\b', text_lower, re.IGNORECASE) # type: ignore
    if ml_match:
        return {'sport_league': 'MLB', 'subject': team_context, 'bet_type': 'Moneyline', 'line': None, 'odds': None, 'bet_qualifier': bet_qualifier_suffix}
        
    # Check for a general total if the team is just mentioned for context
    total_match = re.search(r"(over|under|o/u)\s*(\d+\.?\d*)", text_lower)
    if total_match:
        qualifier = "Over" if total_match.group(1).startswith('o') else "Under"
        return {'sport_league': 'MLB', 'subject': team_context, 'bet_type': 'Total', 'line': float(total_match.group(2)), 'odds': None, 'bet_qualifier': f"{qualifier} {bet_qualifier_suffix}"}
        
    return None

# --- Main Dispatcher Function ---
def detect_pick(tweet_text: str) -> Optional[List[Dict]]:
    """Main dispatcher. Splits tweets by lines and filters for supported leagues."""
    print(f"----- Analyzing Tweet: \"{tweet_text[:100].replace(chr(10), ' ')}...\" -----")
    all_legs = []
    lines = tweet_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line: continue

        print(f"  -- Analyzing Line: '{line}'")
        
        detected_leg = _detect_player_prop(line) or _detect_team_bet(line)
        
        if detected_leg:
            # Only add picks from supported leagues to our final list
            if detected_leg.get('sport_league') in ['MLB']:
                 print(f"    ✅ MLB LEG DETECTED: {detected_leg}")
                 all_legs.append(detected_leg)
            else:
                print(f"    -- Ignoring non-MLB pick from league: {detected_leg.get('sport_league')}")

    if not all_legs:
        print("  DEBUG: No valid picks found in any line of the tweet.")
        return None

    return all_legs