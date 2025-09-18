import os
import json
import redis
from config import Config

# --- Redis Database Connection ---
try:
    redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True) # decode_responses=True is important
    redis_client.ping()
    print("Successfully connected to Redis database.")
except Exception as e:
    print(f"FATAL: Could not connect to Redis. Error: {e}")

# --- DATABASE HELPER FUNCTIONS (Low-Level) ---

def get_all_users_from_db():
    """Fetches and decodes the 'users' list from Redis."""
    users_json = redis_client.get('users')
    return json.loads(users_json) if users_json else []

def save_all_users_to_db(users_list):
    """Encodes and saves the 'users' list to Redis."""
    redis_client.set('users', json.dumps(users_list))

def get_all_data_from_db():
    """Fetches and decodes the 'data' dictionary from Redis."""
    data_json = redis_client.get('data')
    return json.loads(data_json) if data_json else {}

def save_all_data_to_db(data_dict):
    """Encodes and saves the 'data' dictionary to Redis."""
    redis_client.set('data', json.dumps(data_dict))

def save_users(users):
    """MODIFIED: Saves the list of users to the Redis database."""
    redis_client.set('users', json.dumps(users))

# MODIFICATION: Add a one-time data migration function
def migrate_json_to_redis():
    """One-time script to migrate existing JSON data to Redis."""
    print("Checking for data to migrate...")
    # Check if Redis is empty but JSON files exist
    if not redis_client.exists('users') and os.path.exists('users.json'):
        with open('users.json', 'r') as f:
            users_data = json.load(f)
        save_all_users_to_db(users_data)
        print(f"Migrated {len(users_data)} users from users.json to Redis.")

    if not redis_client.exists('data') and os.path.exists('data.json'):
        with open('data.json', 'r') as f:
            app_data = json.load(f)
        save_all_data_to_db(app_data)
        print(f"Migrated data for {len(app_data)} users from data.json to Redis.")
