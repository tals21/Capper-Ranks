import os
from dotenv import load_dotenv

load_dotenv()

# --- Load Configuration from Environment ---
X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET_KEY = os.getenv("X_API_SECRET_KEY")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
DATABASE_NAME = os.getenv("DATABASE_NAME", "capper_ranks.db")

capper_usernames_str = os.getenv("TARGET_CAPPER_USERNAMES", "")
TARGET_CAPPER_USERNAMES = [uname.strip() for uname in capper_usernames_str.split(',') if uname.strip()]

if not all([X_API_KEY, X_BEARER_TOKEN]):
    raise ValueError("One or more required environment variables are missing! Check your .env file.")


