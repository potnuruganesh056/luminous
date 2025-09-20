from flask import redirect, url_for
from flask_login import login_user
from auth.models import User, create_default_user_data, get_user_by_email
from database.redis_db import get_all_users_from_db, get_all_data_from_db, save_all_users_to_db, save_all_data_to_db

def find_or_create_oauth_user(profile):
    """
    A centralized function to find, create, or update a user from any source
    (standard signup, Google, or GitHub) and log them in.
    """
    all_data = get_all_data_from_db()
    all_users = get_all_users_from_db()
    
    # --- Robust User Finding Logic ---
    provider = profile.get('provider')
    provider_id = profile.get('provider_id')
    user_record = None

    # Priority 1: Find user by their unique OAuth provider ID.
    if provider and provider_id:
        user_record = next((u for u in all_users if u.get(f"{provider}_id") == provider_id), None)

    # Priority 2: If not found, find by email address.
    if not user_record and profile.get('email'):
        user_record = get_user_by_email(profile['email'])
    
    # --- Case 1: User Exists ---
    if user_record:
        # Get a direct reference to the user's dictionary in the list to update it
        user_to_update = next((u for u in all_users if u['id'] == user_record['id']), None)
        user_data_to_update = all_data.get(user_record['id'])

        # Always update name and picture on login
        user_to_update['username'] = profile['name']
        user_data_to_update['user_settings']['name'] = profile['name']
        
        # Only update the main picture if a new one is provided
        if profile.get('picture'):
            user_data_to_update['user_settings']['picture'] = profile.get('picture')

        # Link the new OAuth provider if it's an OAuth login
        if provider and provider_id:
            user_to_update[f"{provider}_id"] = provider_id
            if provider == 'google':
                 user_data_to_update['user_settings']['google_picture'] = profile.get('picture')
            elif provider == 'github':
                 user_data_to_update['user_settings']['github_picture'] = profile.get('picture')
                 user_data_to_update['user_settings']['github_profile_url'] = profile.get('profile_url')
        
        final_user_record = user_to_update

    # --- Case 2: New User ---
    else:
        new_user_id = str(int(all_users[-1]['id']) + 1) if all_users else "1"
        final_user_record = {
            'id': new_user_id, 
            'username': profile['name'], 
            'password_hash': profile.get('password_hash'), # Used for standard signup
            'google_id': provider_id if provider == 'google' else None,
            'github_id': provider_id if provider == 'github' else None,
        }
        all_users.append(final_user_record)
        
        # Create and add the new user's application data
        user_data_to_update = create_default_user_data(name=profile['name'], email=profile.get('email', ''))
        if profile.get('picture'):
             user_data_to_update['user_settings']['picture'] = profile.get('picture')
        if provider == 'google':
             user_data_to_update['user_settings']['google_picture'] = profile.get('picture')
        elif provider == 'github':
             user_data_to_update['user_settings']['github_picture'] = profile.get('picture')
             user_data_to_update['user_settings']['github_profile_url'] = profile.get('profile_url')
        all_data[new_user_id] = user_data_to_update

    # Save all changes back to the database
    save_all_users_to_db(all_users)
    save_all_data_to_db(all_data)
    
    # Log the user in with the final, updated record
    user_obj = User(final_user_record['id'], final_user_record['username'], final_user_record.get('password_hash'))
    login_user(user_obj, remember=True)
    
    return redirect(url_for('frontend.home'))
