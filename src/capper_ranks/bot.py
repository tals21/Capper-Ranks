import time
from datetime import datetime 
from capper_ranks.core import config
from capper_ranks.database import models
from capper_ranks.services import x_client
from capper_ranks.services import pick_detector
from capper_ranks.services import sports_api
from capper_ranks.services.image_processor import image_processor

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

def process_tweet_for_picks(tweet, capper_id):
    """
    Processes a single tweet for picks, checking both text and images.
    
    Args:
        tweet: Tweet object from X API
        capper_id: ID of the capper who posted the tweet
        
    Returns:
        True if picks were found and stored, False otherwise
    """
    print(f"\n  - Processing Tweet ID: {tweet.id} from {tweet.created_at}")
    
    # First, try to detect picks from the tweet text
    if hasattr(tweet, 'text') and tweet.text:
        print(f"    📝 Analyzing tweet text...")
        detection_result = pick_detector.detect_pick(tweet.text)
        
        if detection_result:
            print(f"    ✅ TEXT PICK DETECTED: {detection_result['legs']}")
            print(f"    📊 Bet Type: {'Parlay' if detection_result['is_parlay'] else 'Single(s)'}")
            models.store_bet_and_legs(capper_id, str(tweet.id), None, tweet.created_at, detection_result)
            return True
    
    # If no picks found in text, check for images
    if hasattr(tweet, 'attachments') and tweet.attachments and 'media_keys' in tweet.attachments:
        print(f"    🖼️  Tweet contains media attachments, checking for images...")
        
        # Get media URLs from the tweet
        media_urls = []
        if hasattr(tweet, '_includes') and tweet._includes and 'media' in tweet._includes:
            for media in tweet._includes['media']:
                if hasattr(media, 'url') and media.url:
                    media_urls.append(media.url)
                elif hasattr(media, 'preview_image_url') and media.preview_image_url:
                    media_urls.append(media.preview_image_url)
        
        # Process each image
        for i, image_url in enumerate(media_urls):
            print(f"    🖼️  Processing image {i+1}/{len(media_urls)}: {image_url}")
            
            # Extract text from image using OCR
            extracted_text = image_processor.process_image_url(image_url)
            
            if extracted_text:
                print(f"    📝 OCR extracted text: {extracted_text[:100]}...")
                
                # Try to detect picks from the extracted text
                detection_result = pick_detector.detect_pick(extracted_text)
                
                if detection_result:
                    print(f"    ✅ IMAGE PICK DETECTED: {detection_result['legs']}")
                    print(f"    📊 Bet Type: {'Parlay' if detection_result['is_parlay'] else 'Single(s)'}")
                    models.store_bet_and_legs(capper_id, str(tweet.id), None, tweet.created_at, detection_result)
                    return True
                else:
                    print(f"    -- No valid picks found in image text.")
            else:
                print(f"    -- Failed to extract text from image.")
    
    print(f"    -- No valid picks found in tweet text or images.")
    return False

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
            # Fetch tweets with media attachments
            tweets_with_media = x_client.get_tweets_with_media(client, capper_id, since_id=last_seen_id)
            
            if not tweets_with_media:
                print(f"  - No new tweets found.")
                continue

            latest_tweet_id = tweets_with_media[0]['tweet'].id

            # Process tweets in reverse chronological order
            for tweet_data in reversed(tweets_with_media):
                tweet = tweet_data['tweet']
                process_tweet_for_picks(tweet, capper_id)

            models.update_last_seen_tweet_id(capper_id, latest_tweet_id)
            print(f"\n  - Updated last_seen_id for {capper_id} to {latest_tweet_id}")
        except Exception as e:
            print(f"  - An error occurred during tweet scan: {e}")
            
        time.sleep(1)

    # --- Result Checking ---
    process_pending_results()
    print("\n--- Bot has finished its run. ---")

def test_live_tweet_processing():
    """
    Test function to process a sample tweet and demonstrate the new parlay detection.
    This can be used to test the system with live tweets.
    """
    print("=== Testing Live Tweet Processing ===")
    
    # Sample tweets for testing
    test_tweets = [
        {
            "text": "Shohei Ohtani Over 1.5 Total Bases\nAaron Judge Over 0.5 Home Runs",
            "description": "Multiple picks without parlay keywords (should be singles)"
        },
        {
            "text": "Parlay:\nShohei Ohtani Over 1.5 Total Bases\nAaron Judge Over 0.5 Home Runs",
            "description": "Multiple picks with parlay keyword (should be parlay)"
        },
        {
            "text": "NYY ML is a lock",
            "description": "Single pick (should be single)"
        },
        {
            "text": "Combination bet:\nJuan Soto Under 1.5 RBIs\nMookie Betts Over 2.5 H+R+RBI",
            "description": "Multiple picks with combination keyword (should be parlay)"
        }
    ]
    
    for i, tweet_data in enumerate(test_tweets, 1):
        print(f"\n--- Test {i}: {tweet_data['description']} ---")
        print(f"Tweet: {tweet_data['text']}")
        
        detection_result = pick_detector.detect_pick(tweet_data['text'])
        
        if detection_result:
            print(f"✅ Detected {len(detection_result['legs'])} leg(s)")
            print(f"📊 Bet Type: {'Parlay' if detection_result['is_parlay'] else 'Single(s)'}")
            for j, leg in enumerate(detection_result['legs'], 1):
                print(f"   Leg {j}: {leg['subject']} {leg['bet_qualifier']}")
        else:
            print("❌ No picks detected")
        
        print("-" * 50)

def test_image_processing():
    """
    Test function to demonstrate image processing capabilities.
    """
    print("=== Testing Image Processing ===")
    
    # Sample image URLs for testing (these would be real bet slip images)
    test_images = [
        {
            "url": "https://example.com/bet_slip_1.jpg",
            "description": "Sample bet slip with player props"
        }
    ]
    
    for i, image_data in enumerate(test_images, 1):
        print(f"\n--- Test {i}: {image_data['description']} ---")
        print(f"Image URL: {image_data['url']}")
        
        # Extract text from image
        extracted_text = image_processor.process_image_url(image_data['url'])
        
        if extracted_text:
            print(f"✅ OCR extracted text: {extracted_text}")
            
            # Try to detect picks from extracted text
            detection_result = pick_detector.detect_pick(extracted_text)
            
            if detection_result:
                print(f"✅ PICK DETECTED: {detection_result['legs']}")
                print(f"📊 Bet Type: {'Parlay' if detection_result['is_parlay'] else 'Single(s)'}")
            else:
                print("❌ No picks detected in image text")
        else:
            print("❌ Failed to extract text from image")
        
        print("-" * 50)

if __name__ == '__main__':
    # Uncomment the line below to test live tweet processing
    # test_live_tweet_processing()
    
    # Uncomment the line below to test image processing
    # test_image_processing()
    
    main_loop()