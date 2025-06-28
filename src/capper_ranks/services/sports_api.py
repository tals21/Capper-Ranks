import statsapi
from datetime import datetime, timedelta

def _get_mlb_game_result(leg_details: dict):
    """
    Fetches and grades a single MLB leg for Moneyline, Totals, and Spreads.
    """
    try:
        pick_date_str = datetime.fromisoformat(str(leg_details['tweet_timestamp'])).strftime('%Y-%m-%d')
        print(f"  - Searching for games on {pick_date_str} for subject: {leg_details['subject']}")
        
        # The schedule function finds all games on the dates involving any MLB team
        games = statsapi.schedule(start_date=pick_date_str, end_date=pick_date_str)

        if not games:
            return {'status': 'GAME_NOT_FOUND'}

        for game in games:
            home_team = game.get('home_name', '').lower()
            away_team = game.get('away_name', '').lower()
            pick_subject_lower = leg_details['subject'].lower()

            # Check if this game involves the team we're looking for
            if pick_subject_lower in home_team or pick_subject_lower in away_team:
                print(f"  - Found matching MLB game: {game.get('summary')} (Status: {game.get('status')})")

                if game.get('status') != "Final":
                    return {'status': 'PENDING_RESULT'}

                # Game is final, let's grade the pick
                home_score = game.get('home_score')
                away_score = game.get('away_score')
                
                # --- Moneyline Logic ---
                if leg_details['bet_type'] == 'Moneyline':
                    winning_team = game.get('winning_team', '').lower()
                    if pick_subject_lower in winning_team:
                        return {'status': 'WIN', 'details': f"Final: {away_score}-{home_score}"}
                    else:
                        return {'status': 'LOSS', 'details': f"Final: {away_score}-{home_score}"}
                
                # --- NEW: Total (Over/Under) Logic ---
                elif leg_details['bet_type'] == 'Total':
                    total_runs = home_score + away_score
                    pick_line = leg_details['line']
                    pick_qualifier = leg_details['bet_qualifier'] # 'Over' or 'Under'

                    if total_runs == pick_line:
                        return {'status': 'PUSH', 'details': f"Final Total: {total_runs}"}
                    elif (pick_qualifier == 'Over' and total_runs > pick_line) or \
                         (pick_qualifier == 'Under' and total_runs < pick_line):
                        return {'status': 'WIN', 'details': f"Final Total: {total_runs}"}
                    else:
                        return {'status': 'LOSS', 'details': f"Final Total: {total_runs}"}

                # --- NEW: Spread (Run Line) Logic ---
                elif leg_details['bet_type'] == 'Spread':
                    # Determine which team is the "subject" of the pick
                    is_subject_home_team = pick_subject_lower in home_team
                    
                    # Calculate score from the perspective of the picked team
                    # e.g., if they won 5-3, their margin is +2. If they lost 3-5, their margin is -2.
                    subject_score = home_score if is_subject_home_team else away_score
                    opponent_score = away_score if is_subject_home_team else home_score
                    margin = subject_score - opponent_score
                    
                    pick_line = leg_details['line'] # e.g., -1.5 or +1.5

                    if (margin + pick_line) == 0:
                        return {'status': 'PUSH', 'details': f"Final: {away_score}-{home_score}"}
                    elif (margin + pick_line) > 0:
                        return {'status': 'WIN', 'details': f"Final: {away_score}-{home_score}"}
                    else:
                        return {'status': 'LOSS', 'details': f"Final: {away_score}-{home_score}"}

                return {'status': 'NEEDS_GRADING_LOGIC'}

        return {'status': 'GAME_NOT_FOUND'}

    except Exception as e:
        print(f"An error occurred while fetching MLB data: {e}")
        return {'status': 'ERROR'}


def fetch_pick_result(leg: dict):
    """
    Main dispatcher function. It looks at the league and calls the
    appropriate helper function to get the result.
    """
    league = leg.get('sport_league')
    print(f"--> Checking result for a {league} pick (Leg ID: {leg['leg_id']})")

    if league == 'MLB':
        return _get_mlb_game_result(leg)
    # Future logic for other sports will go here
    else:
        print(f"  - No result fetching logic available for league: {league}")
        return None