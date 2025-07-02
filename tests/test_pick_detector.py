# tests/test_pick_detector.py
from capper_ranks.services.pick_detector import detect_pick

# We keep the tests that were already passing
def test_detect_mlb_moneyline():
    result = detect_pick("NYY ML is a lock")
    assert result is not None
    assert result[0]['subject'] == 'nyy'
    assert result[0]['bet_type'] == 'Moneyline'
    
def test_detect_mlb_total_over():
    result = detect_pick("Love the Over 8.5 in the Dodgers game")
    assert result is not None
    assert result[0]['bet_qualifier'] == 'Over Full Game'

def test_detect_mlb_run_line():
    result = detect_pick("Astros -1.5 tonight")
    assert result is not None
    assert result[0]['line'] == -1.5

def test_detect_mlb_total_f5():
    result = detect_pick("Yankees/Red Sox F5 Over 4.5")
    assert result is not None
    assert result[0]['bet_qualifier'] == 'Over First 5'

def test_ignore_non_mlb_pick():
    result = detect_pick("Lakers ML looks good tonight")
    assert result is None

def test_ignore_non_pick_tweet():
    assert detect_pick("What a great game by the Blue Jays!") is None

# --- Here are the corrected tests ---

def test_detect_valid_mlb_player_prop(mocker):
    """Tests that a valid player prop is detected with a realistic mock."""
    # THIS MOCK IS NOW SMARTER. It will only return "MLB" for the correct name.
    def mock_get_league(player_name):
        if player_name == "Shohei Ohtani":
            return "MLB"
        return None # Return None for "betting on Shohei Ohtani", etc.

    mocker.patch('capper_ranks.services.sports_api.get_player_league', side_effect=mock_get_league)
    
    sample_tweet = "I am betting on Shohei Ohtani Over 1.5 Total Bases"
    result = detect_pick(sample_tweet)

    assert result is not None
    assert result[0]['subject'] == 'Shohei Ohtani'
    assert result[0]['bet_qualifier'] == 'Over Total Bases'


def test_ignore_player_prop_for_unsupported_league(mocker):
    """Tests that a non-MLB player prop is correctly ignored."""
    def mock_get_league(player_name):
        if player_name == "LeBron James":
            return "NBA" # The mock correctly finds the player
        return None

    mocker.patch('capper_ranks.services.sports_api.get_player_league', side_effect=mock_get_league)
    
    sample_tweet = "Taking LeBron James Over 29.5 Points"
    result = detect_pick(sample_tweet)

    # Our main `detect_pick` function's filtering will now correctly return None
    assert result is None


def test_detect_player_prop_with_suffix(mocker):
    """Tests that a player name with 'Jr.' is correctly parsed."""
    def mock_get_league(player_name):
        if player_name == "Vladimir Guerrero Jr.":
            return "MLB"
        return None

    mocker.patch('capper_ranks.services.sports_api.get_player_league', side_effect=mock_get_league)
    
    sample_tweet = "Fading Vladimir Guerrero Jr. Under 0.5 Hits today"
    result = detect_pick(sample_tweet)

    assert result is not None
    assert len(result) == 1
    pick_leg = result[0]
    assert pick_leg['subject'] == 'Vladimir Guerrero Jr.'
    assert pick_leg['bet_qualifier'] == 'Under Hits'


def test_ignore_prop_for_nonexistent_player(mocker):
    """Tests that a prop is ignored if the API cannot find the player."""
    # This mock always returns None, simulating a failed API lookup
    mocker.patch('capper_ranks.services.sports_api.get_player_league', return_value=None)
    
    sample_tweet = "Let's see if John Doe Over 0.5 Hits"
    result = detect_pick(sample_tweet)
    
    assert result is None

def test_detect_mlb_player_prop_total_bases(mocker):
    def mock_get_league(player_name):
        if player_name == "Shohei Ohtani":
            return "MLB"
        return None
    mocker.patch('capper_ranks.services.sports_api.get_player_league', side_effect=mock_get_league)
    sample_tweet = "Shohei Ohtani Over 1.5 Total Bases"
    result = detect_pick(sample_tweet)
    assert result is not None
    assert result[0]['subject'] == 'Shohei Ohtani'
    assert result[0]['bet_qualifier'] == 'Over Total Bases'

def test_detect_mlb_player_prop_home_runs(mocker):
    def mock_get_league(player_name):
        if player_name == "Aaron Judge":
            return "MLB"
        return None
    mocker.patch('capper_ranks.services.sports_api.get_player_league', side_effect=mock_get_league)
    sample_tweet = "Aaron Judge Over 0.5 Home Runs"
    result = detect_pick(sample_tweet)
    assert result is not None
    assert result[0]['subject'] == 'Aaron Judge'
    assert result[0]['bet_qualifier'] == 'Over Home Runs'

def test_detect_mlb_player_prop_rbis(mocker):
    def mock_get_league(player_name):
        if player_name == "Juan Soto":
            return "MLB"
        return None
    mocker.patch('capper_ranks.services.sports_api.get_player_league', side_effect=mock_get_league)
    sample_tweet = "Juan Soto Under 1.5 RBIs"
    result = detect_pick(sample_tweet)
    assert result is not None
    assert result[0]['subject'] == 'Juan Soto'
    assert result[0]['bet_qualifier'] == 'Under RBIs'

def test_detect_mlb_player_prop_stolen_bases(mocker):
    def mock_get_league(player_name):
        if player_name == "Ronald Acuna Jr.":
            return "MLB"
        return None
    mocker.patch('capper_ranks.services.sports_api.get_player_league', side_effect=mock_get_league)
    sample_tweet = "Ronald Acuna Jr. Over 0.5 Stolen Bases"
    result = detect_pick(sample_tweet)
    assert result is not None
    assert result[0]['subject'] == 'Ronald Acuna Jr.'
    assert result[0]['bet_qualifier'] == 'Over Stolen Bases'