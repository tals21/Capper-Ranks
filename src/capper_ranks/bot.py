# src/capper_ranks/bot.py

import time
from src.capper_ranks.core import config
from src.capper_ranks.database import models
from src.capper_ranks.services import x_client # Using your file name
from src.capper_ranks.services import pick_detector

def main_loop():
    """The main function to run the bot's core loop."""
    print("--- Capper-Ranks Bot Starting Up ---")

    models.init_db()
    client = x_client.get_x_client()

    if not client:
        print("Could not start bot: X client authentication failed.")
        return

    # --- Capper ID Resolution (Your working code) ---
    capper_ids_to_scan = []
    print("\nResolving capper usernames to IDs...")
    for username in config.TARGET_CAPPER_USERNAMES:
        capper_data = models.get_capper_by_username(username)
        if capper_data:
            capper_ids_to_scan.append(capper_data['capper_id'])
        else:
            print(f"Capper @{username} not found in DB. Looking up via X API...")
            user_obj = x_client.get_user_from_username(client, username)
            if user_obj:
                models.add_capper(user_obj.id, user_obj.username)
                capper_ids_to_scan.append(user_obj.id)
            else:
                print(f"Could not resolve username @{username}. It will be skipped.")
    print(f"\nFinished resolving IDs. Ready to scan {len(capper_ids_to_scan)} cappers.")
    # --- End of Capper ID Resolution ---

    # --- Main Scanning Loop ---
    print("\nPerforming a single scan for new tweets...")
    for capper_id in capper_ids_to_scan:
        
        # 1. Get the last tweet ID we processed for this capper from our database
        last_seen_id = models.get_last_seen_tweet_id(capper_id)
        print(f"--> Fetching new tweets for capper ID: {capper_id} (since_id: {last_seen_id})")
        
        try:
            # 2. Fetch only tweets NEWER than the last one we've seen
            response = client.get_users_tweets(id=capper_id, since_id=last_seen_id)
            
            if not response.data: # type: ignore
                print(f"  - No new tweets found for this capper.")
                continue

            # 3. The API returns newest first. We save the newest ID for our next run.
            latest_tweet_id = response.data[0].id # type: ignore

            # 4. We process the tweets in chronological order (oldest to newest)
            for tweet in reversed(response.data): # type: ignore
                print(f"\n  - Processing Tweet ID: {tweet.id}")
                
                # 5. Try to detect a pick in the tweet's text
                legs = pick_detector.detect_pick(tweet.text)
                
                if legs:
                    print(f"    ✅ PICK DETECTED: {legs}")
                    # 6. If a pick is found, store it in the database
                    models.store_bet_and_legs(capper_id, str(tweet.id), None, legs)
                else:
                    print(f"    -- No valid pick found in this tweet.")

            # 7. After processing all new tweets, update our bot's "memory"
            models.update_last_seen_tweet_id(capper_id, latest_tweet_id)
            print(f"\n  - Updated last_seen_id for {capper_id} to {latest_tweet_id}")

        except Exception as e:
            print(f"  - An error occurred: {e}")
            
        time.sleep(1) # Be polite to the API between fetching from different cappers

    print("\n--- Scan complete. ---")

if __name__ == '__main__':
    main_loop()