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
    "H+R+RBI", "Total Bases", "Hits", "Home Runs", "RBIs", "Runs", "Strikeouts", "Walks", "Stolen Bases", "Hits Allowed",
    "Earned Runs", "Outs Recorded", "Runs Allowed", "Saves", "Wins", "Losses", "Innings Pitched", "Doubles", "Triples"
]

# Sort by length descending for greedy matching
MLB_STAT_TYPES = sorted(MLB_STAT_TYPES, key=lambda x: -len(x))

# Keywords that indicate a parlay bet
PARLAY_KEYWORDS = [
    'parlay', 'parlays', 'parlayed', 'parlaying',
    'all must hit', 'all must win', 'all legs',
    'combined', 'combo', 'combination',
    'multi-leg', 'multileg', 'multi leg',
    'bundle', 'package', 'set',
    'sgp', 'same game parlay', 'leg'  # Added for SGP and leg-based slips
]

def _is_parlay_tweet(tweet_text: str) -> bool:
    """
    Determines if a tweet contains parlay keywords indicating it's a true parlay bet.
    Returns True if parlay keywords are found, False otherwise (defaults to singles).
    """
    tweet_lower = tweet_text.lower()
    return any(keyword in tweet_lower for keyword in PARLAY_KEYWORDS)

def _detect_player_prop(line: str) -> Optional[Dict]:
    """
    Improved: Finds the bet pattern, then matches the longest valid stat type after the number.
    Now also strips team abbreviations in parentheses from player names.
    Handles formats like "Player Name (Team) O/U <number> <stat_type>"
    Also handles alt prop formats like "Player Name 1+ Home Run(s)"
    """
    # First, try to match the standard Over/Under format
    bet_match = re.search(
        r"(over|under|o/u|o|u)\s*(\d+\.?\d*)\s+([A-Za-z\s''+/]+?)(?:\s*$)",
        line,
        re.IGNORECASE
    )
    if bet_match:
        text_before_bet = line[:bet_match.start()].strip()
        words = text_before_bet.split()
        if not words:
            return None
        # Try to find the player name (up to 4 words before the bet)
        for i in range(min(4, len(words)), 0, -1):
            name_candidate = " ".join(words[-i:])
            # Remove team abbreviation in parentheses, e.g., 'Hunter Brown (HOU)' -> 'Hunter Brown'
            name_candidate_clean = re.sub(r"\s*\([A-Za-z0-9 .]+\)$", "", name_candidate).strip()
            if not name_candidate_clean or not name_candidate_clean[0].isupper():
                continue
            league = sports_api.get_player_league(name_candidate_clean)
            if league:
                qualifier_text, line_str, stat_type_candidate = bet_match.groups()
                qualifier = "Over" if qualifier_text.lower().startswith('o') else "Under"
                stat_type_candidate = stat_type_candidate.strip()
                # Special handling for H+R+RBI
                if stat_type_candidate.upper() == "H+R+RBI":
                    stat_type = "H+R+RBI"
                else:
                    # Greedily match the longest valid stat type
                    stat_type = None
                    for stype in MLB_STAT_TYPES:
                        if stype == "H+R+RBI":
                            continue
                        if stat_type_candidate.lower().startswith(stype.lower()):
                            stat_type = stype
                            break
                    if not stat_type:
                        stat_type = stat_type_candidate.split()[0]
                return {
                    'sport_league': league,
                    'subject': name_candidate_clean,
                    'bet_type': 'Player Prop',
                    'line': float(line_str),
                    'odds': None,
                    'bet_qualifier': f"{qualifier} {stat_type}"
                }
    # Now, try to match the alt prop format: "Player Name 1+ Home Run(s)"
    alt_match = re.search(
        r"([A-Za-z .'-]+)\s+1\+\s+(Home Run|Home Runs|HR|Hits|Total Bases|RBI|RBIs|Runs|Stolen Bases)",
        line,
        re.IGNORECASE
    )
    if alt_match:
        player_name = alt_match.group(1).strip()
        stat_type = alt_match.group(2).strip()
        league = sports_api.get_player_league(player_name)
        if league:
            # 1+ means Over 0.5 for most stat types
            return {
                'sport_league': league,
                'subject': player_name,
                'bet_type': 'Player Prop',
                'line': 0.5,
                'odds': None,
                'bet_qualifier': f"Over {stat_type}"
            }
    
    # Handle ParlayScience format: "Player Name 2+ TOTAL BASES"
    bases_match = re.search(
        r"([A-Za-z .'-]+)\s+(\d+)\+\s*(TOTAL\s*BASES?|Total\s*Bases?)",
        line,
        re.IGNORECASE
    )
    if bases_match:
        player_name = bases_match.group(1).strip()
        line_value = int(bases_match.group(2))
        stat_type = bases_match.group(3).strip()
        league = sports_api.get_player_league(player_name)
        if league:
            return {
                'sport_league': league,
                'subject': player_name,
                'bet_type': 'Player Prop',
                'line': float(line_value - 0.5),  # 2+ means Over 1.5
                'odds': None,
                'bet_qualifier': f"Over {stat_type}"
            }
    
    # Handle ParlayScience format: "Player Name TO HIT A HOME RUN"
    home_run_match = re.search(
        r"([A-Za-z .'-]+)\s+TO\s+HIT\s+A?\s*(HOME RUN|Home Run)",
        line,
        re.IGNORECASE
    )
    if home_run_match:
        player_name = home_run_match.group(1).strip()
        stat_type = home_run_match.group(2).strip()
        
        # Clean up player name - remove any single letters or abbreviations at the end
        player_name = re.sub(r'\s+[A-Z]{1,2}\s*$', '', player_name).strip()
        
        league = sports_api.get_player_league(player_name)
        if league:
            return {
                'sport_league': league,
                'subject': player_name,
                'bet_type': 'Player Prop',
                'line': 0.5,  # "TO HIT A HOME RUN" means Over 0.5 Home Runs
                'odds': None,
                'bet_qualifier': f"Over {stat_type}"
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
    # This should take priority over player prop detection for team totals
    total_match = re.search(r"(over|under|o/u)\s*(\d+\.?\d*)", text_lower)
    if total_match:
        qualifier = "Over" if total_match.group(1).startswith('o') else "Under"
        return {'sport_league': 'MLB', 'subject': team_context, 'bet_type': 'Total', 'line': float(total_match.group(2)), 'odds': None, 'bet_qualifier': f"{qualifier} {bet_qualifier_suffix}"}
        
    return None

# --- Main Dispatcher Function ---
def detect_pick(tweet_text: str) -> Optional[Dict]:
    """
    Main dispatcher. Splits tweets by lines and filters for supported leagues.
    Returns a dictionary with 'legs' and 'is_parlay' keys.
    """
    print(f"----- Analyzing Tweet: \"{tweet_text[:100].replace(chr(10), ' ')}...\" -----")
    all_legs = []
    lines = tweet_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line: continue

        print(f"  -- Analyzing Line: '{line}'")
        
        # Prioritize team bets when a team is mentioned in the context
        team_context, _ = _find_sport_context(line)
        if team_context:
            detected_leg = _detect_team_bet(line) or _detect_player_prop(line)
        else:
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

    # Determine if this is a parlay based on keywords
    is_parlay = _is_parlay_tweet(tweet_text)
    print(f"  DEBUG: Tweet {'IS' if is_parlay else 'IS NOT'} a parlay (based on keywords)")
    
    return {
        'legs': all_legs,
        'is_parlay': is_parlay
    }