# scripts/manage_cappers.py

import argparse
import sys
import os

# This is a bit of a trick to allow this script to import from your src directory
# It adds the project's root directory to the Python path.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.capper_ranks.database import models
from src.capper_ranks.services import x_client
from src.capper_ranks.core import config

def list_cappers():
    """Prints a list of all cappers currently in the database."""
    print("--- Current Cappers in Database ---")
    all_cappers = models.get_all_cappers()
    if not all_cappers:
        print("No cappers found.")
        return
    
    for capper in all_cappers:
        print(f"- @{capper['username']} (ID: {capper['capper_id']})")

def add_new_capper(username: str):
    """Finds a capper by username via the X API and adds them to the database."""
    print(f"Attempting to add @{username}...")
    client = x_client.get_x_client()
    if not client:
        print("Could not connect to X API. Check credentials.")
        return

    user_obj = x_client.get_user_from_username(client, username)
    if user_obj:
        models.add_capper(user_obj.id, user_obj.username)
    else:
        print(f"Could not find user @{username} on X.")

def remove_capper(username: str):
    """Removes a capper and their associated data from the database."""
    print(f"Attempting to remove @{username}...")
    # We pass the username with and without the '@' to be safe
    was_removed = models.remove_capper_by_username(username.replace('@', ''))
    if was_removed:
        print(f"Successfully removed @{username} from the database.")
    else:
        print(f"Could not find @{username} in the database to remove.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Manage the cappers in the Capper-Ranks database.")
    parser.add_argument('--list', action='store_true', help='List all current cappers.')
    parser.add_argument('--add', type=str, help='The username of the capper to add (without @).')
    parser.add_argument('--remove', type=str, help='The username of the capper to remove (without @).')
    
    args = parser.parse_args()

    if args.list:
        list_cappers()
    elif args.add:
        add_new_capper(args.add)
    elif args.remove:
        remove_capper(args.remove)
    else:
        print("No action specified. Use --list, --add, or --remove. Use -h for help.")