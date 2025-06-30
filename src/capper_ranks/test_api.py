# test_api.py

import statsapi
import traceback

# This is a real, final game from June 29, 2025 (PHI @ ATL)
# We will use its ID to test the API call directly.
TEST_GAME_PK = 748586

print(f"--- Attempting to fetch detailed data for gamePk: {TEST_GAME_PK} ---")

try:
    # This is the single API call we suspect is failing in your main code.
    game_data = statsapi.get('game', {'gamePk': TEST_GAME_PK})
    
    # If the API call doesn't crash, let's see what it returned.
    print("\n--- API Call Succeeded without crashing ---")
    print(f"Type of returned data: {type(game_data)}")
    
    # Check if we got a dictionary as expected
    if isinstance(game_data, dict):
        print("RESULT: The API returned a dictionary as expected.")
        # Let's print a few key pieces of data to confirm it's valid
        game_date = game_data.get('gameData', {}).get('datetime', {}).get('officialDate')
        status = game_data.get('gameData', {}).get('status', {}).get('detailedState')
        print(f"Game Date from data: {game_date}")
        print(f"Status from data: {status}")
    else:
        print(f"WARNING: API returned something other than a dictionary: {game_data}")

except Exception as e:
    # If the API call crashes, this block will run.
    print("\n--- AN EXCEPTION OCCURRED ---")
    print(f"The error is: {e}")
    print("\n--- FULL TRACEBACK ---")
    traceback.print_exc()

print("\n--- Test script finished. ---")