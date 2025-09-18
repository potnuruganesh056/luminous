# make_admin.py
import json
import redis
from config import Config # Your app's config

# --- IMPORTANT: CHANGE THIS ---
ADMIN_USER_ID = "luminous@admin" # Change this to your actual user ID

try:
    redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True)
    
    users_json = redis_client.get('users')
    users = json.loads(users_json) if users_json else []
    
    admin_found = False
    for user in users:
        if user.get('id') == ADMIN_USER_ID:
            user['is_admin'] = True
            admin_found = True
            break
            
    if admin_found:
        redis_client.set('users', json.dumps(users))
        print(f"Success! User with ID '{ADMIN_USER_ID}' is now an admin.")
    else:
        print(f"Error: User with ID '{ADMIN_USER_ID}' not found.")

except Exception as e:
    print(f"An error occurred: {e}")
