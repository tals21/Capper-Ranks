import tweepy
from src.capper_ranks.core import config

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

# Add this function to src/capper_ranks/services/twitter_client.py

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


# This allows us to test this single file to verify our keys
if __name__ == '__main__':
    print("Testing X API connection...")
    client = get_x_client()
    if client:
        response = client.get_me()
        print(f"Connection test successful! Authenticated as bot: @{response.data.username}") # type: ignore
    else:
        print("Connection test failed. Check your API keys in the .env file.")