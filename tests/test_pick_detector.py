# tests/test_pick_detector.py

# The import now starts directly from your package name, not from 'src'
from capper_ranks.services.pick_detector import detect_pick

# IMPORTANT: Every test function MUST start with the prefix "test_"
def test_detect_simple_moneyline_pick():
    """
    Tests that the detector can find a simple moneyline pick in a clean sentence.
    """
    sample_tweet = "I'm taking the Yankees ML tonight, great value."
    
    # Call the function with our sample data
    result = detect_pick(sample_tweet)
    
    # Use "assert" to check if the result is what we expect
    assert result is not None  # Assert that a pick was found
    assert len(result) == 1    # Assert that it found exactly one leg
    
    pick_leg = result[0]
    assert pick_leg['subject'] == 'yankees'
    assert pick_leg['bet_type'] == 'Moneyline'
    assert pick_leg['sport_league'] == 'MLB'

def test_ignore_tweet_without_pick():
    """
    Tests that the detector correctly ignores a tweet that does not contain a valid pick.
    """
    sample_tweet = "The Yankees are playing a great game, but I'm not betting on it."
    
    # Call the function with our sample data
    result = detect_pick(sample_tweet)
    
    # Assert that the function correctly returned None
    assert result is None