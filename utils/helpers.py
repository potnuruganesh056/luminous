from flask_login import current_user
from database.redis_db import get_all_data_from_db, save_all_data_to_db

def get_user_data():
    """Gets the current user's data from Redis."""
    all_data = get_all_data_from_db()
    return all_data.get(current_user.id, {})

def save_user_data(user_data):
    """Saves the current user's data to Redis."""
    all_data = get_all_data_from_db()
    all_data[current_user.id] = user_data
    save_all_data_to_db(all_data)

def get_current_user_theme():
    """Gets the theme for the currently logged-in user from Redis."""
    all_data = get_all_data_from_db()
    user_data = all_data.get(current_user.id, {})
    return user_data.get("user_settings", {}).get("theme", "light")
