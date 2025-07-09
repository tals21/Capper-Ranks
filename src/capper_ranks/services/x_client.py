import tweepy
from capper_ranks.core import config

def get_x_client():
    """Authenticates with the X API using credentials from config."""
    try:
        client = tweepy.Client(
            bearer_token=config.X_BEARER_TOKEN,
            consumer_key=config.X_API_KEY,
            consumer_secret=config.X_API_SECRET_KEY,
            access_token=config.X_ACCESS_TOKEN,
            access_token_secret=config.X_ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True
        )
        print("Successfully authenticated with X API.")
        return client
    except Exception as e:
        print(f"Error authenticating with X API: {e}")
        return None

def get_user_from_username(client, username):
    """Looks up a user by their username and returns their data."""
    try:
        # The get_user function can find users by their handle
        response = client.get_user(username=username)
        if response.data:
            return response.data
        else:
            print(f"Could not find user with username: {username}")
            return None
    except Exception as e:
        print(f"An error occurred looking up user {username}: {e}")
        return None

def get_tweets_with_media(client, user_id, since_id=None, max_results=100):
    """
    Fetches tweets with media attachments for a given user.
    
    Args:
        client: Authenticated X client
        user_id: User ID to fetch tweets from
        since_id: Tweet ID to start from (for pagination)
        max_results: Maximum number of tweets to fetch
        
    Returns:
        List of tweets with media attachments
    """
    try:
        # Fetch tweets with media attachments
        response = client.get_users_tweets(
            id=user_id,
            since_id=since_id,
            max_results=max_results,
            tweet_fields=["created_at", "attachments"],
            media_fields=["url", "preview_image_url", "type"],
            expansions=["attachments.media_keys"]
        )
        
        if not response.data:
            return []
        
        # Process tweets to extract media URLs
        tweets_with_media = []
        media_lookup = {}
        
        # Build media lookup dictionary
        if response.includes and 'media' in response.includes:
            for media in response.includes['media']:
                media_lookup[media.media_key] = media
        
        # Process each tweet
        for tweet in response.data:
            media_urls = []
            
            # Check if tweet has media attachments
            if hasattr(tweet, 'attachments') and tweet.attachments and 'media_keys' in tweet.attachments:
                for media_key in tweet.attachments['media_keys']:
                    if media_key in media_lookup:
                        media = media_lookup[media_key]
                        # Get the best available URL
                        if hasattr(media, 'url') and media.url:
                            media_urls.append(media.url)
                        elif hasattr(media, 'preview_image_url') and media.preview_image_url:
                            media_urls.append(media.preview_image_url)
            
            if media_urls:
                tweets_with_media.append({
                    'tweet': tweet,
                    'media_urls': media_urls
                })
        
        return tweets_with_media
        
    except Exception as e:
        print(f"Error fetching tweets with media for user {user_id}: {e}")
        return []

# This allows us to test this single file to verify our keys
if __name__ == '__main__':
    print("Testing X API connection...")
    client = get_x_client()
    if client:
        response = client.get_me()
        print(f"Connection test successful! Authenticated as bot: @{response.data.username}") # type: ignore
    else:
        print("Connection test failed. Check your API keys in the .env file.")