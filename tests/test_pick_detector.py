# tests/test_pick_detector.py

from capper_ranks.services.pick_detector import detect_pick

# --- Positive Test Cases (Picks should be found) ---

def test_detect_mlb_moneyline():
    """Tests detection of a Moneyline pick."""
    sample_tweet = "NYY ML is a lock"
    result = detect_pick(sample_tweet)

    # First, assert that the result is NOT None before checking its contents.
    # This is the fix for the Pylance error.
    assert result is not None
    assert len(result) == 1

    pick_leg = result[0]
    assert pick_leg['subject'] == 'nyy'
    assert pick_leg['bet_type'] == 'Moneyline'

def test_detect_mlb_total_over():
    """Tests detection of a full game Over Total pick."""
    sample_tweet = "Love the Over 8.5 in the Dodgers game, seems too low."
    result = detect_pick(sample_tweet)

    # The fix: Check for None first.
    assert result is not None
    assert len(result) == 1
    
    pick_leg = result[0]
    assert pick_leg['bet_type'] == 'Total'
    assert pick_leg['line'] == 8.5
    assert pick_leg['bet_qualifier'] == 'Over Full Game'
    assert pick_leg['subject'] == 'dodgers'

def test_detect_mlb_run_line():
    """Tests detection of a Run Line (Spread) pick."""
    sample_tweet = "Astros -1.5 feels like free money"
    result = detect_pick(sample_tweet)

    # The fix: Check for None first.
    assert result is not None
    assert len(result) == 1

    pick_leg = result[0]
    assert pick_leg['bet_type'] == 'Spread'
    assert pick_leg['line'] == -1.5
    assert pick_leg['subject'] == 'astros'
    assert pick_leg['bet_qualifier'] == 'Full Game'

def test_detect_mlb_total_f5():
    """Tests that F5 (First 5 Innings) bets are correctly identified."""
    sample_tweet = "I like the Yankees/Red Sox F5 Over 4.5"
    result = detect_pick(sample_tweet)

    # The fix: Check for None first.
    assert result is not None
    assert len(result) == 1

    pick_leg = result[0]
    assert pick_leg['bet_type'] == 'Total'
    assert pick_leg['line'] == 4.5
    assert pick_leg['bet_qualifier'] == 'Over First 5'
    assert pick_leg['subject'] == 'yankees' # Verifies it found the first team mentioned for context

# --- Negative Test Cases (Picks should be ignored) ---

def test_ignore_non_mlb_pick():
    """Tests that a pick for a non-MLB team is ignored."""
    # The assertion for negative cases is already correct.
    assert detect_pick("Lakers ML looks good tonight") is None

def test_ignore_non_pick_tweet():
    """Tests that a tweet without a valid pick format is ignored."""
    assert detect_pick("What a great game by the Blue Jays!") is None