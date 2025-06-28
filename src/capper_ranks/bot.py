# src/capper_ranks/bot.py

import time
from datetime import datetime 
from capper_ranks.core import config
from capper_ranks.database import models
from capper_ranks.services import x_client
from capper_ranks.services import pick_detector
from capper_ranks.services import sports_api

def process_pending_results():
    """Gets all pending picks and tries to update their status."""
    print("\n--- Checking for pending results ---")
    pending_legs = models.get_pending_legs()
    
    if not pending_legs:
        print("No pending picks to check.")
        return

    for leg in pending_legs:
        leg_dict = dict(leg) # Convert the database row to a dictionary
        result = sports_api.fetch_pick_result(leg_dict)

        # If we get a definitive result, update the database
        if result and result.get('status') in ['WIN', 'LOSS', 'PUSH']:
            models.update_leg_status(leg_dict['leg_id'], result['status'])
        else:
            status = result.get('status') if result else 'ERROR'
            print(f"  - Result for leg {leg_dict['leg_id']} is still {status}.")
        
        time.sleep(1) # Be polite to the sports API between checks

def main_loop():
    """The main function to run the bot's core loop."""
    print("--- Capper-Ranks Bot Starting Up ---")

    models.init_db()
    client = x_client.get_x_client()

    if not client:
        print("Could not start bot: X client authentication failed.")
        return

    # --- Capper ID Resolution ---
    capper_ids_to_scan = []
    print("\nResolving capper usernames to IDs...")
    for username in config.TARGET_CAPPER_USERNAMES:
        capper_data = models.get_capper_by_username(username)
        if capper_data:
            capper_ids_to_scan.append(capper_data['capper_id'])
        else:
            user_obj = x_client.get_user_from_username(client, username)
            if user_obj:
                models.add_capper(user_obj.id, user_obj.username)
                capper_ids_to_scan.append(user_obj.id)
            else:
                print(f"Could not resolve username @{username}. It will be skipped.")
    print(f"\nFinished resolving IDs. Ready to scan {len(capper_ids_to_scan)} cappers.")

    # --- Main Tweet Scanning Loop ---
    print("\n--- Performing a scan for new tweets... ---")
    for capper_id in capper_ids_to_scan:
        last_seen_id = models.get_last_seen_tweet_id(capper_id)
        print(f"--> Fetching new tweets for capper ID: {capper_id} (since_id: {last_seen_id})")
        
        try:
            # We must ask the API to give us the 'created_at' field for each tweet
            response = client.get_users_tweets(id=capper_id, since_id=last_seen_id, tweet_fields=["created_at"])
            
            if not response.data: # type: ignore
                print(f"  - No new tweets found.")
                continue

            latest_tweet_id = response.data[0].id # type: ignore

            for tweet in reversed(response.data): # type: ignore
                print(f"\n  - Processing Tweet ID: {tweet.id} from {tweet.created_at}")
                legs = pick_detector.detect_pick(tweet.text)
                
                if legs:
                    print(f"    ✅ PICK DETECTED: {legs}")
                    models.store_bet_and_legs(capper_id, str(tweet.id), None, tweet.created_at, legs)
                else:
                    print(f"    -- No valid pick found in this tweet.")

            models.update_last_seen_tweet_id(capper_id, latest_tweet_id)
            print(f"\n  - Updated last_seen_id for {capper_id} to {latest_tweet_id}")
        except Exception as e:
            print(f"  - An error occurred during tweet scan: {e}")
            
        time.sleep(1)

    # --- Result Checking ---
    process_pending_results()
    print("\n--- Bot has finished its run. ---")

if __name__ == '__main__':
    main_loop()