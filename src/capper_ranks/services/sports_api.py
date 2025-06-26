import statsapi
from datetime import datetime, timedelta # <-- Make sure timedelta is imported

def _get_mlb_game_result(leg_details: dict):
    """
    Fetches the result for a single MLB leg by searching for the first
    matching game within a 24-hour window of the tweet's timestamp.
    """
    try:
        # --- NEW: Time Window Logic ---
        
        # Convert the timestamp string from the database into a Python datetime object
        # The .replace('Z', '+00:00') makes it compatible with fromisoformat for UTC time
        tweet_timestamp_str = str(leg_details['tweet_timestamp'])
        tweet_dt = datetime.fromisoformat(tweet_timestamp_str.replace('Z', '+00:00'))

        # Define the search window: the day the tweet was made and the next day.
        # This reliably covers any game in the "next 24 hours".
        start_date = tweet_dt.date()
        end_date = start_date + timedelta(days=1)
        
        # --- END OF NEW Time Window Logic ---

        print(f"  - Searching for games between {start_date} and {end_date} for subject: {leg_details['subject']}")
        
        # Updated API call to use the start and end dates
        games = statsapi.schedule(start_date=start_date.strftime('%Y-%m-%d'), end_date=end_date.strftime('%Y-%m-%d'))

        if not games:
            print(f"  - No MLB games found within the time window.")
            return {'status': 'GAME_NOT_FOUND'}

        # The schedule is chronological, so the first match we find will be the correct one.
        for game in games:
            home_team = game.get('home_name', '')
            away_team = game.get('away_name', '')
            pick_subject_lower = leg_details['subject'].lower()

            if pick_subject_lower in home_team.lower() or pick_subject_lower in away_team.lower():
                game_status = game.get('status')
                print(f"  - Found matching MLB game: {game.get('summary')} (Status: {game_status})")

                if game_status != "Final":
                    return {'status': 'PENDING_RESULT'}

                home_score = game.get('home_score')
                away_score = game.get('away_score')
                winning_team = game.get('winning_team', '')

                if leg_details['bet_type'] == 'Moneyline':
                    if pick_subject_lower in winning_team.lower():
                        return {'status': 'WIN', 'details': f"Final: {away_score}-{home_score}"}
                    else:
                        return {'status': 'LOSS', 'details': f"Final: {away_score}-{home_score}"}
                else:
                    return {'status': 'NEEDS_GRADING_LOGIC'}
                
                # Since we found the first upcoming game, we don't need to check any others.
                break 

        # If we loop through all games in the window and don't find a match
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