#!/usr/bin/env python3
"""
Test script to fetch and process tweets from ParlayScience for image processing.
This script will help test the OCR and pick detection functionality with real data from ParlayScience.
"""

import sys
import os
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from capper_ranks.core import config
from capper_ranks.services import x_client
from capper_ranks.services import pick_detector
from capper_ranks.services.image_processor import image_processor

def test_parlayscience_tweet():
    """Test image processing with tweets from ParlayScience."""
    print("=== Testing Image Processing with ParlayScience Tweet ===\n")
    
    # Initialize X client
    client = x_client.get_x_client()
    if not client:
        print("❌ Failed to initialize X client. Check your API credentials.")
        return False
    
    # Get ParlayScience user info
    print("🔍 Looking up ParlayScience...")
    user = x_client.get_user_from_username(client, "ParlayScience")
    if not user:
        print("❌ Could not find user @ParlayScience")
        return False
    
    print(f"✅ Found user: @{user.username} (ID: {user.id})")
    
    # Fetch recent tweets with media
    print("\n📥 Fetching recent tweets with media...")
    tweets_with_media = x_client.get_tweets_with_media(client, user.id, max_results=10)
    
    if not tweets_with_media:
        print("❌ No tweets with media found from ParlayScience")
        return False
    
    print(f"✅ Found {len(tweets_with_media)} tweets with media")
    
    # Process each tweet
    for i, tweet_data in enumerate(tweets_with_media, 1):
        tweet = tweet_data['tweet']
        media_urls = tweet_data['media_urls']
        
        print(f"\n--- Tweet {i}: {tweet.id} ---")
        print(f"📅 Posted: {tweet.created_at}")
        print(f"📝 Text: {tweet.text[:100]}...")
        print(f"🖼️  Images: {len(media_urls)}")
        
        # Process the tweet for picks
        print("\n🔍 Processing for picks...")
        
        # First, try text-based detection
        if hasattr(tweet, 'text') and tweet.text:
            print("  📝 Analyzing tweet text...")
            text_result = pick_detector.detect_pick(tweet.text)
            
            if text_result:
                print(f"  ✅ TEXT PICK DETECTED: {text_result['legs']}")
                print(f"  📊 Bet Type: {'Parlay' if text_result['is_parlay'] else 'Single(s)'}")
                for j, leg in enumerate(text_result['legs'], 1):
                    print(f"    Leg {j}: {leg['subject']} {leg['bet_qualifier']}")
                    if 'line' in leg and leg['line']:
                        print(f"      Line: {leg['line']}")
            else:
                print("  -- No picks found in text")
        
        # Then, try image-based detection
        if media_urls:
            print(f"  🖼️  Processing {len(media_urls)} image(s)...")
            
            for j, image_url in enumerate(media_urls, 1):
                print(f"    🖼️  Image {j}: {image_url}")
                
                # Extract text from image
                extracted_text = image_processor.process_image_url(image_url)
                
                if extracted_text:
                    print(f"    📝 OCR extracted: {extracted_text[:200]}...")
                    
                    # Detect picks from extracted text
                    image_result = pick_detector.detect_pick(extracted_text)
                    
                    if image_result:
                        print(f"    ✅ IMAGE PICK DETECTED: {image_result['legs']}")
                        print(f"    📊 Bet Type: {'Parlay' if image_result['is_parlay'] else 'Single(s)'}")
                        
                        # Show detailed leg information
                        for k, leg in enumerate(image_result['legs'], 1):
                            print(f"      Leg {k}: {leg['subject']} {leg['bet_qualifier']}")
                            if 'line' in leg and leg['line']:
                                print(f"        Line: {leg['line']}")
                    else:
                        print("    -- No picks found in image text")
                else:
                    print("    -- Failed to extract text from image")
        
        print("-" * 60)
        
        # Ask user if they want to continue
        if i < len(tweets_with_media):
            response = input(f"\nProcess next tweet? (y/n): ").lower().strip()
            if response != 'y':
                break
    
    print("\n✅ Image processing test completed!")
    return True

def test_specific_tweet(tweet_id):
    """Test processing a specific tweet by ID."""
    print(f"=== Testing Specific Tweet: {tweet_id} ===\n")
    
    # Initialize X client
    client = x_client.get_x_client()
    if not client:
        print("❌ Failed to initialize X client. Check your API credentials.")
        return False
    
    try:
        # Fetch the specific tweet
        print(f"📥 Fetching tweet {tweet_id}...")
        response = client.get_tweet(
            id=tweet_id,
            tweet_fields=["created_at", "attachments"],
            media_fields=["url", "preview_image_url", "type"],
            expansions=["attachments.media_keys"]
        )
        
        if not response.data:  # type: ignore
            print("❌ Tweet not found or not accessible")
            return False
        
        tweet = response.data  # type: ignore
        
        # Process media attachments
        media_urls = []
        if hasattr(tweet, 'attachments') and tweet.attachments and 'media_keys' in tweet.attachments:
            if response.includes and 'media' in response.includes:  # type: ignore
                for media in response.includes['media']:  # type: ignore
                    if hasattr(media, 'url') and media.url:
                        media_urls.append(media.url)
                    elif hasattr(media, 'preview_image_url') and media.preview_image_url:
                        media_urls.append(media.preview_image_url)
        
        print(f"📅 Posted: {tweet.created_at}")
        print(f"📝 Text: {tweet.text}")
        print(f"🖼️  Images: {len(media_urls)}")
        
        # Process for picks
        print("\n🔍 Processing for picks...")
        
        # Text-based detection
        if hasattr(tweet, 'text') and tweet.text:
            print("  📝 Analyzing tweet text...")
            text_result = pick_detector.detect_pick(tweet.text)
            
            if text_result:
                print(f"  ✅ TEXT PICK DETECTED: {text_result['legs']}")
                print(f"  📊 Bet Type: {'Parlay' if text_result['is_parlay'] else 'Single(s)'}")
                for j, leg in enumerate(text_result['legs'], 1):
                    print(f"    Leg {j}: {leg['subject']} {leg['bet_qualifier']}")
                    if 'line' in leg and leg['line']:
                        print(f"      Line: {leg['line']}")
            else:
                print("  -- No picks found in text")
        
        # Image-based detection
        if media_urls:
            print(f"  🖼️  Processing {len(media_urls)} image(s)...")
            
            for j, image_url in enumerate(media_urls, 1):
                print(f"    🖼️  Image {j}: {image_url}")
                
                extracted_text = image_processor.process_image_url(image_url)
                
                if extracted_text:
                    print(f"    📝 OCR extracted: {extracted_text}")
                    
                    image_result = pick_detector.detect_pick(extracted_text)
                    
                    if image_result:
                        print(f"    ✅ IMAGE PICK DETECTED: {image_result['legs']}")
                        print(f"    📊 Bet Type: {'Parlay' if image_result['is_parlay'] else 'Single(s)'}")
                        
                        for k, leg in enumerate(image_result['legs'], 1):
                            print(f"      Leg {k}: {leg['subject']} {leg['bet_qualifier']}")
                            if 'line' in leg and leg['line']:
                                print(f"        Line: {leg['line']}")
                    else:
                        print("    -- No picks found in image text")
                else:
                    print("    -- Failed to extract text from image")
        
        print("\n✅ Specific tweet test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error processing tweet: {e}")
        return False

def main():
    """Main function to run the test."""
    print("=== ParlayScience Image Processing Test ===\n")
    
    # Check if user wants to test a specific tweet
    if len(sys.argv) > 1:
        tweet_id = sys.argv[1]
        return test_specific_tweet(tweet_id)
    else:
        return test_parlayscience_tweet()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 