import statsapi
from datetime import datetime, timedelta
from typing import Optional, Dict
import traceback

# In src/capper_ranks/services/sports_api.py

def get_player_league(player_name: str) -> Optional[str]:
    """
    Looks up a player by name using a two-step fuzzy search to find their league.
    """
    try:
        # Step 1: Try looking up the full name directly.
        player_info_list = statsapi.lookup_player(player_name)

        # Step 2: If the full name yields no results, try just the last name.
        # This handles cases like "Wheeler" when the full name is "Zack Wheeler".
        if not player_info_list:
            last_name = player_name.split(' ')[-1]
            print(f"  DEBUG: Full name lookup failed. Trying last name: '{last_name}'")
            player_info_list = statsapi.lookup_player(last_name)

        if not player_info_list:
            print(f"  DEBUG: No player found for name '{player_name}'.")
            return None
        
        # We assume the first result is the correct one.
        player_info = player_info_list[0]
        league = player_info.get('primarySport', {}).get('abbreviation')
        
        # Only return a league if it's one we support.
        if league in ['MLB', 'NBA', 'NFL']:
            # Return the full name from the API for consistency
            # This also helps correct minor typos from the tweet.
            print(f"  DEBUG: Successfully validated player: {player_info.get('fullName')} in {league}")
            return league
        else:
            return None

    except Exception as e:
        print(f"An error occurred during player lookup for '{player_name}': {e}")
        return None
    
def _get_mlb_player_prop_result(leg_details: dict) -> Dict:
    """Fetches the boxscore for a game and grades a player prop."""
    try:
        pick_date_str = datetime.fromisoformat(str(leg_details['tweet_timestamp'])).strftime('%Y-%m-%d')
        player_name = leg_details['subject']
        
        player_info = statsapi.lookup_player(player_name)
        if not player_info: return {'status': 'ERROR', 'details': f"Player '{player_name}' not found."}
        
        player_id_str = f"ID{player_info[0]['id']}"
        player_team_id = player_info[0].get('currentTeam', {}).get('id')
        if not player_team_id: return {'status': 'ERROR', 'details': f"Could not determine team for '{player_name}'."}

        games = statsapi.schedule(date=pick_date_str, team=player_team_id)
        if not games: return {'status': 'GAME_NOT_FOUND'}

        game = games[0]
        if game.get('status') != "Final": return {'status': 'PENDING_RESULT'}

        boxscore = statsapi.boxscore_data(game.get('game_pk'))
        player_stats = boxscore.get('playerInfo', {}).get(player_id_str, {}).get('stats', {})
        if not player_stats: return {'status': 'ERROR', 'details': f"Could not find stats for '{player_name}' in boxscore."}
        
        # Expanded mapping for all supported MLB stat types
        prop_stat_map = {
            'total bases': 'totalbases',
            'hits': 'hits',
            'home runs': 'homeruns',
            'rbis': 'rbi',
            'runs': 'runs',
            'strikeouts': 'strikeouts',
            'walks': 'baseonballs',
            'stolen bases': 'stolenbases',
            'hits allowed': 'hitsallowed',
            'earned runs': 'earnedruns',
            'outs recorded': 'outs',
            'runs allowed': 'runsallowed',
            'saves': 'saves',
            'wins': 'wins',
            'losses': 'losses',
            'innings pitched': 'inningsPitched',
            'doubles': 'doubles',
            'triples': 'triples',
        }
        qualifier, prop_type_text = leg_details['bet_qualifier'].split(' ', 1)
        stat_key = prop_stat_map.get(prop_type_text.lower())
        
        if not stat_key: return {'status': 'NEEDS_GRADING_LOGIC', 'details': f"No logic for prop '{prop_type_text}'"}
            
        actual_stat = player_stats.get('batting', {}).get(stat_key) or player_stats.get('pitching', {}).get(stat_key, 0)
        pick_line = leg_details['line']

        if actual_stat == pick_line: return {'status': 'PUSH'}
        elif (qualifier == 'Over' and actual_stat > pick_line) or (qualifier == 'Under' and actual_stat < pick_line):
            return {'status': 'WIN'}
        else: return {'status': 'LOSS'}
    except Exception as e:
        print(f"An error occurred fetching MLB player prop data: {e}")
        return {'status': 'ERROR'}


# In src/capper_ranks/services/sports_api.py

def _get_mlb_team_bet_result(leg_details: dict) -> Optional[Dict]:
    """
    Fetches and grades a single MLB team-based bet using the correct 'game_id' key.
    """
    game_id = None # Initialize for use in the error message
    try:
        pick_date_str = datetime.fromisoformat(str(leg_details['tweet_timestamp'])).strftime('%Y-%m-%d')
        games = statsapi.schedule(start_date=pick_date_str, end_date=pick_date_str)

        game_to_grade = None
        for game in games:
            home_team_name = game.get('home_name', '').lower()
            away_team_name = game.get('away_name', '').lower()
            if leg_details['subject'].lower() in home_team_name or leg_details['subject'].lower() in away_team_name:
                game_to_grade = game
                break
        
        if not game_to_grade:
            return {'status': 'GAME_NOT_FOUND'}

        if game_to_grade.get('status') != "Final":
            print(f"  - Found matching game, but it is not final yet (Status: {game_to_grade.get('status')}).")
            return {'status': 'PENDING_RESULT'}
            
        print(f"  - Found matching final game: {game_to_grade.get('summary')}")
        
        # --- THIS IS THE FINAL FIX ---
        # We now use the correct key: 'game_id' instead of 'game_pk'
        game_id = game_to_grade.get('game_id')
        if not game_id:
            return {'status': 'ERROR', 'details': 'Could not find game_id in schedule data.'}
        # --- END OF FINAL FIX ---

        # The rest of the function will now work correctly
        game_data = statsapi.get('game', {'gamePk': game_id}) # This endpoint uses 'gamePk'
        is_f5_bet = "First 5" in leg_details.get('bet_qualifier', '')
        
        if is_f5_bet:
            innings_data = game_data.get('liveData', {}).get('linescore', {}).get('innings', [])
            if len(innings_data) < 5:
                return {'status': 'PENDING_RESULT', 'details': 'Game ended before 5 innings.'}
            home_score = sum(i.get('home', {}).get('runs', 0) for i in innings_data[:5])
            away_score = sum(i.get('away', {}).get('runs', 0) for i in innings_data[:5])
            result_details = f"F5 Final: {away_score}-{home_score}"
        else:
            home_score = game_to_grade.get('home_score')
            away_score = game_to_grade.get('away_score')
            result_details = f"Final: {away_score}-{home_score}"

        # ... (The rest of your grading logic for ML, Totals, Spreads is here and is correct) ...
        home_team_name_lower = game_to_grade.get('home_name', '').lower()
        winning_team = game_to_grade.get('winning_team', '').lower()
        if is_f5_bet:
            if home_score > away_score: winning_team = home_team_name_lower
            elif away_score > home_score: winning_team = game_to_grade.get('away_name', '').lower()
            else: winning_team = ''

        bet_type = leg_details['bet_type']
        pick_subject_lower = leg_details['subject'].lower()
        
        if bet_type == 'Moneyline':
            if not winning_team and is_f5_bet: return {'status': 'PUSH', 'details': result_details}
            return {'status': 'WIN', 'details': result_details} if pick_subject_lower in winning_team else {'status': 'LOSS', 'details': result_details}
        
        elif bet_type == 'Total':
            total_runs = home_score + away_score
            pick_line = leg_details['line']
            qualifier = leg_details['bet_qualifier'].split(' ')[0]
            if total_runs == pick_line: return {'status': 'PUSH', 'details': result_details}
            elif (qualifier == 'Over' and total_runs > pick_line) or (qualifier == 'Under' and total_runs < pick_line):
                return {'status': 'WIN', 'details': result_details}
            else: return {'status': 'LOSS', 'details': result_details}
        
        elif bet_type == 'Spread':
            is_subject_home = pick_subject_lower in home_team_name_lower
            margin = (home_score - away_score) if is_subject_home else (away_score - home_score)
            pick_line = leg_details['line']
            if (margin + pick_line) == 0: return {'status': 'PUSH', 'details': result_details}
            elif (margin + pick_line) > 0: return {'status': 'WIN', 'details': result_details}
            else: return {'status': 'LOSS', 'details': result_details}
        
        return {'status': 'NEEDS_GRADING_LOGIC'}

    except Exception as e:
        import traceback
        print(f"An error occurred while fetching MLB team bet data for game_id {game_id}:")
        traceback.print_exc()
        return {'status': 'ERROR'}
    
    
def fetch_pick_result(leg: dict) -> Optional[Dict]:
    """Main dispatcher function. Routes to the correct grading logic."""
    league, bet_type = leg.get('sport_league'), leg.get('bet_type')
    print(f"--> Checking result for a {league} {bet_type} pick (Leg ID: {leg['leg_id']})")

    if league == 'MLB':
        if bet_type == 'Player Prop':
            return _get_mlb_player_prop_result(leg)
        else: # Moneyline, Spread, Total
            return _get_mlb_team_bet_result(leg)
    else:
        print(f"  - No result fetching logic available for league: {league}")
        return None