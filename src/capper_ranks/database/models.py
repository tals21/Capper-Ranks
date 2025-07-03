# src/capper_ranks/database/models.py

import sqlite3
from ..core import config
from datetime import datetime, timedelta

def connect_db():
    """Establishes a connection to the database."""
    # This is your existing function, which is perfect.
    conn = sqlite3.connect(config.DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database with all necessary tables."""
    print("Initializing database...")
    conn = connect_db()
    cursor = conn.cursor()

    # The `bets` table holds the overall bet
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bets (
            bet_id INTEGER PRIMARY KEY AUTOINCREMENT,
            capper_id TEXT NOT NULL,
            original_tweet_id TEXT NOT NULL UNIQUE,
            our_retweet_id TEXT,
            bet_format TEXT NOT NULL,
            overall_odds INTEGER,
            status TEXT NOT NULL DEFAULT 'PENDING_RESULT',
            timestamp_detected DATETIME DEFAULT CURRENT_TIMESTAMP,
            tweet_timestamp DATETIME NOT NULL -- This line must be present
        )
    ''')

    # The `legs` table holds each individual pick within a bet
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS legs (
            leg_id INTEGER PRIMARY KEY AUTOINCREMENT,
            bet_id INTEGER NOT NULL, 
            sport_league TEXT,
            subject TEXT NOT NULL,
            bet_type TEXT NOT NULL,
            line REAL,
            odds INTEGER,
            bet_qualifier TEXT,
            status TEXT NOT NULL DEFAULT 'PENDING_RESULT',
            FOREIGN KEY (bet_id) REFERENCES bets (bet_id)
        )
    ''')

    # The `cappers` table stores user info
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cappers (
            capper_id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            last_checked DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # --- NEWLY ADDED TABLE ---
    # This table is crucial for tracking which tweets we've already seen.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS last_seen_tweets (
            capper_id TEXT PRIMARY KEY,
            last_tweet_id TEXT NOT NULL,
            FOREIGN KEY (capper_id) REFERENCES cappers (capper_id)
        )
    ''')
    # --- END OF NEW ADDITION ---

    conn.commit()
    conn.close()
    print(f"Database '{config.DATABASE_NAME}' initialized successfully with all tables.")

# --- Capper Management Functions (Your existing code) ---
def get_capper_by_username(username):
    conn = connect_db()
    capper = conn.execute("SELECT * FROM cappers WHERE username = ?", (username,)).fetchone()
    conn.close()
    return capper

def add_capper(capper_id, username):
    conn = connect_db()
    conn.execute("INSERT OR REPLACE INTO cappers (capper_id, username) VALUES (?, ?)", (capper_id, username))
    conn.commit()
    conn.close()
    print(f"Stored/Updated capper: @{username} with ID: {capper_id}")


def get_last_seen_tweet_id(capper_id):
    """Retrieves the most recent tweet ID processed for a given capper."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT last_tweet_id FROM last_seen_tweets WHERE capper_id = ?", (capper_id,))
    result = cursor.fetchone()
    conn.close()
    return result['last_tweet_id'] if result else None

def update_last_seen_tweet_id(capper_id, last_tweet_id):
    """Saves or updates the last seen tweet ID for a capper."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO last_seen_tweets (capper_id, last_tweet_id) VALUES (?, ?)",
                   (capper_id, str(last_tweet_id)))
    conn.commit()
    conn.close()

# Replace your existing store_bet_and_legs function with this one.
# It uses the NULL-safe 'IS' operator and checks the date of the original tweet.

def store_bet_and_legs(capper_id, tweet_id, retweet_id, tweet_timestamp, detection_result):
    """
    Stores a parent bet and its legs, but first checks for duplicates
    from the same capper for the day the tweet was posted.
    
    Args:
        detection_result: Dictionary with 'legs' and 'is_parlay' keys from detect_pick
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    legs_data = detection_result['legs']
    is_parlay = detection_result['is_parlay']
    
    try:
        # We only run the duplicate check for single-leg bets for now.
        if len(legs_data) == 1:
            first_leg = legs_data[0]
            
            # Use the tweet's date for the duplicate check to handle past games correctly.
            pick_date = datetime.fromisoformat(str(tweet_timestamp)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT 1 FROM legs l
                JOIN bets b ON l.bet_id = b.bet_id
                WHERE b.capper_id = ?
                  AND l.subject IS ?
                  AND l.bet_type IS ?
                  AND l.line IS ?
                  AND l.bet_qualifier IS ?
                  AND DATE(b.tweet_timestamp) = ?
                LIMIT 1
            ''', (capper_id, first_leg['subject'], first_leg['bet_type'], first_leg['line'], first_leg['bet_qualifier'], pick_date))
            
            existing_pick = cursor.fetchone()
            
            if existing_pick:
                print(f"  --> Duplicate pick detected for {first_leg['subject']} on {pick_date}. Skipping storage.")
                conn.close()
                return None

        # Determine bet format based on is_parlay flag and number of legs
        if is_parlay and len(legs_data) > 1:
            bet_format = 'Parlay'
        else:
            bet_format = 'Single'

        cursor.execute('''
            INSERT INTO bets (capper_id, original_tweet_id, our_retweet_id, bet_format, tweet_timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (capper_id, tweet_id, retweet_id, bet_format, tweet_timestamp))
        
        bet_id = cursor.lastrowid
        
        for leg in legs_data:
            cursor.execute('''
                INSERT INTO legs (bet_id, sport_league, subject, bet_type, line, odds, bet_qualifier)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (bet_id, leg['sport_league'], leg['subject'], leg['bet_type'], leg['line'], leg['odds'], leg['bet_qualifier']))
        
        conn.commit()
        print(f"    --> Successfully stored Bet ID {bet_id} with {len(legs_data)} leg(s) as {bet_format}.")
        return bet_id

    except sqlite3.IntegrityError:
        print(f"    --> Bet with original_tweet_id {tweet_id} already exists in DB. Skipping.")
        conn.rollback()
        return None
    except Exception as e:
        print(f"    --> An error occurred storing the bet: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_pending_legs():
    """Fetches all pending legs, now including the bet's original tweet timestamp."""
    conn = connect_db()
    # Add b.tweet_timestamp to the SELECT statement so we can use it for lookups
    legs = conn.execute('''
        SELECT l.*, b.tweet_timestamp FROM legs l
        JOIN bets b ON l.bet_id = b.bet_id
        WHERE l.status = 'PENDING_RESULT'
    ''').fetchall()
    conn.close()
    return legs

def update_leg_status(leg_id, status):
    """Updates the status of a specific leg (e.g., to WIN or LOSS)."""
    conn = connect_db()
    conn.execute("UPDATE legs SET status = ? WHERE leg_id = ?", (status, leg_id))
    conn.commit()
    conn.close()
    print(f"Updated leg {leg_id} to status {status}")
    
    # After updating a leg, check if we need to update the parent bet status
    update_bet_status_from_legs(leg_id)

def update_bet_status_from_legs(leg_id):
    """
    Updates the parent bet's status based on all its legs' statuses.
    For parlays: WIN if all legs WIN, LOSS if any leg LOSS, PUSH if all legs PUSH.
    For singles: No change to bet status (each leg is independent).
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Get the bet_id and bet_format for this leg
        cursor.execute('''
            SELECT b.bet_id, b.bet_format, b.status as bet_status
            FROM bets b
            JOIN legs l ON b.bet_id = l.bet_id
            WHERE l.leg_id = ?
        ''', (leg_id,))
        
        bet_info = cursor.fetchone()
        if not bet_info:
            return
            
        bet_id, bet_format, current_bet_status = bet_info['bet_id'], bet_info['bet_format'], bet_info['bet_status']
        
        # Only update bet status for parlays
        if bet_format != 'Parlay':
            return
            
        # Get all legs for this bet
        cursor.execute('''
            SELECT status FROM legs WHERE bet_id = ?
        ''', (bet_id,))
        
        leg_statuses = [row['status'] for row in cursor.fetchall()]
        
        # Check if all legs have been graded
        if 'PENDING_RESULT' in leg_statuses:
            return  # Not all legs are graded yet
            
        # Determine bet status based on leg statuses
        if all(status == 'WIN' for status in leg_statuses):
            new_bet_status = 'WIN'
        elif any(status == 'LOSS' for status in leg_statuses):
            new_bet_status = 'LOSS'
        elif all(status == 'PUSH' for status in leg_statuses):
            new_bet_status = 'PUSH'
        else:
            # Mixed results (some WIN, some PUSH) - this shouldn't happen in practice
            new_bet_status = 'LOSS'
            
        # Update bet status if it changed
        if new_bet_status != current_bet_status:
            cursor.execute('UPDATE bets SET status = ? WHERE bet_id = ?', (new_bet_status, bet_id))
            conn.commit()
            print(f"Updated bet {bet_id} status from {current_bet_status} to {new_bet_status}")
            
    except Exception as e:
        print(f"Error updating bet status: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_all_cappers():
    """Retrieves all cappers from the database."""
    conn = connect_db()
    cappers = conn.execute("SELECT * FROM cappers ORDER BY username").fetchall()
    conn.close()
    return cappers

def remove_capper_by_username(username: str) -> bool:
    """Removes a capper and their 'last_seen' record by username."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        # First, get the ID for the username
        capper = get_capper_by_username(username)
        if not capper:
            return False

        capper_id = capper['capper_id']
        
        # Delete from all related tables
        cursor.execute("DELETE FROM last_seen_tweets WHERE capper_id = ?", (capper_id,))
        cursor.execute("DELETE FROM cappers WHERE capper_id = ?", (capper_id,))
        # Note: We are NOT deleting their old bets, so their history is preserved.
        
        conn.commit()
        # rowcount will be > 0 if a row was deleted
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error removing capper @{username}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()