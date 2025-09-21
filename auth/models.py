from flask_login import UserMixin
from database.redis_db import get_all_users_from_db, get_all_data_from_db

class User(UserMixin):
    # This class remains the same
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password_hash = password

def load_user(user_id):
    """Loads a user for Flask-Login by their ID."""
    all_users = get_all_users_from_db()
    user_data = next((u for u in all_users if u.get('id') == user_id), None)
    if user_data:
        return User(user_data['id'], user_data['username'], user_data.get('password_hash'))
    return None

def get_user_by_email(email):
    """Finds a user's auth record ('users' key) by their email address (from 'data' key)."""
    if not email:
        return None
    all_data = get_all_data_from_db()
    all_users = get_all_users_from_db()
    for user_id, user_data in all_data.items():
        if user_data.get("user_settings", {}).get("email") == email:
            return next((u for u in all_users if u.get('id') == user_id), None)
    return None

def create_default_user_data(name, email, picture=None):
    """Creates the default data structure for a new user."""
    return {
        "user_settings": {
            "name": name,
            "email": email,
            "picture": picture,
            "mobile": "", "channel": "email", "theme": "light", "ai_control_interval": 5
        },
        "rooms": [{
            "id": "1",
            "name": "Hall",
            "ai_control": False,
            "appliances": []
        }]
    }
