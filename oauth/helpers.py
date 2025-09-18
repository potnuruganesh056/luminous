from flask import redirect, url_for
from flask_login import login_user
from auth.models import User, create_default_user_data, get_user_by_email
from database.redis_db import get_all_users_from_db, get_all_data_from_db, save_all_users_to_db, save_all_data_to_db

def find_or_create_oauth_user(profile):
    """
    The single source of truth for creating or updating a user from an OAuth profile.
    """
    all_data = get_all_data_from_db()
    all_users = get_all_users_from_db()
    
    # Find an existing user by their email address
    user_record = get_user_by_email(profile['email'])
    
    # --- Case 1: User with this email already exists ---
    if user_record:
        user_to_update = next((u for u in all_users if u['id'] == user_record['id']), None)
        user_data_to_update = all_data.get(user_record['id'])

        # MODIFICATION: Update the user's details on every login
        user_to_update['username'] = profile['name']
        user_data_to_update['user_settings']['name'] = profile['name']
        user_data_to_update['user_settings']['picture'] = profile.get('picture')

        # Link the new provider
        if profile['provider'] == 'google':
            user_to_update['google_id'] = profile['provider_id']
            user_data_to_update['user_settings']['google_picture'] = profile['picture']
        elif profile['provider'] == 'github':
            user_to_update['github_id'] = profile['provider_id']
            user_data_to_update['user_settings']['github_picture'] = profile.get('picture')
            user_data_to_update['user_settings']['github_profile_url'] = profile.get('profile_url')

    # --- Case 2: No user with this email, create a new one ---
    else:
        new_user_id = str(int(all_users[-1]['id']) + 1) if all_users else "1"
        user_record = {
            'id': new_user_id, 'username': profile['name'], 'password_hash': None,
            'google_id': profile['provider_id'] if profile['provider'] == 'google' else None,
            'github_id': profile['provider_id'] if profile['provider'] == 'github' else None,
        }
        all_users.append(user_record)
        
        # Create and add the new user's data
        user_data_to_update = create_default_user_data(name=profile['name'], email=profile['email'])
        user_data_to_update['user_settings']['picture'] = profile.get('picture')
        if profile['provider'] == 'google':
            user_data_to_update['user_settings']['google_picture'] = profile['picture']
        elif profile['provider'] == 'github':
            user_data_to_update['user_settings']['github_picture'] = profile['picture']
            user_data_to_update['user_settings']['github_profile_url'] = profile.get('profile_url')
        all_data[new_user_id] = user_data_to_update

    # Save all changes back to the database
    save_all_users_to_db(all_users)
    save_all_data_to_db(all_data)
    
    # Log the user in with the "remember me" functionality
    user_obj = User(user_record['id'], user_record['username'], user_record.get('password_hash'))
    login_user(user_obj, remember=True)
    
    return redirect(url_for('frontend.home'))
