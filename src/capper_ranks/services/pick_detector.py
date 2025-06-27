# In src/capper_ranks/services/pick_detector.py
import re
from capper_ranks.core.mappings import TEAM_LEAGUE_MAP

def detect_pick(tweet_text: str):
    """
    Analyzes tweet text to find picks. This new version is less greedy and more accurate.
    """
    print(f"----- Analyzing: '{tweet_text}' -----")

    # We use a regex just to find the "ML" keyword with word boundaries
    ml_keyword_match = re.search(r"\bML\b", tweet_text, re.IGNORECASE)

    if not ml_keyword_match:
        print("  DEBUG: Step 1 FAILED. Keyword 'ML' not found.")
        return None
    
    # Take the part of the string BEFORE the "ML" keyword
    text_before_ml = tweet_text[:ml_keyword_match.start()].strip()
    print(f"  DEBUG: Text before 'ML' is: '{text_before_ml}'")

    # Now, check if this text chunk ends with one of our known team names or acronyms
    found_subject = None
    for team_alias in TEAM_LEAGUE_MAP.keys():
        if text_before_ml.lower().endswith(team_alias):
            # We check for the longest possible match to handle cases like "New York" vs "New York Yankees"
            if found_subject is None or len(team_alias) > len(found_subject):
                found_subject = team_alias

    if not found_subject:
        print(f"  DEBUG: Step 2 FAILED. No known team alias found at the end of '{text_before_ml}'.")
        return None

    sport_league = TEAM_LEAGUE_MAP.get(found_subject)
    print(f"  DEBUG: Step 2 PASSED. Found subject '{found_subject}' which maps to league '{sport_league}'.")

    if sport_league != 'MLB':
        print(f"  DEBUG: Step 3 FAILED. League is '{sport_league}', not 'MLB'.")
        return None
        
    print("  DEBUG: Step 3 PASSED. This is a valid MLB pick!")

    pick_leg = {
        'sport_league': sport_league,
        'subject': found_subject, # Use the alias we found as the subject
        'bet_type': 'Moneyline',
        'line': None, 'odds': None, 'bet_qualifier': None
    }
    
    return [pick_leg]

if __name__ == '__main__':
    # Create a list of sample tweets to test your function
    sample_tweets = [
        "I'm taking the Yankees ML tonight, great value.", # Should detect
        "Let's go BOS ML all the way!",                     # Should detect (acronym)
        "The Cubs are looking good, but I'm passing.",      # Should NOT detect (no "ML")
        "Parlay time: Chiefs -7.5 and Lakers ML",           # Should NOT detect (not MLB)
        "This is just a random tweet about baseball.",        # Should NOT detect
        "Hammering STL ML",                                 # Should detect (acronym)
    ]

    print("--- Testing Pick Detector ---")
    for i, text in enumerate(sample_tweets):
        detected_legs = detect_pick(text)
        print(f"Test Tweet #{i+1}: '{text}'")
        if detected_legs:
            print(f"  --> SUCCESS: Detected {len(detected_legs)} leg(s): {detected_legs}")
        else:
            print(f"  --> CORRECTLY IGNORED")
        print("-" * 20)