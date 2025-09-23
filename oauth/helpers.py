from flask import redirect, url_for, current_app
from flask_login import login_user
from auth.models import User, create_default_user_data, get_user_by_email
from database.redis_db import get_all_users_from_db, get_all_data_from_db, save_all_users_to_db, save_all_data_to_db
import re

def validate_email(email):
    """Validate email format"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email.strip()) is not None

def sanitize_string(value, max_length=255):
    """Sanitize string input"""
    if not value:
        return ""
    # Remove null bytes and control characters except newlines/tabs
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', str(value))
    return sanitized.strip()[:max_length]

def validate_provider_id(provider, provider_id):
    """Validate provider ID format"""
    if not provider_id:
        return False
    
    # Convert to string and sanitize
    provider_id = sanitize_string(str(provider_id), 100)
    
    if provider == 'google':
        # Google IDs are typically 21 digit numbers
        return provider_id.isdigit() and 15 <= len(provider_id) <= 25
    elif provider == 'github':
        # GitHub IDs are typically 7-9 digit numbers
        return provider_id.isdigit() and 1 <= len(provider_id) <= 15
    
    return False

def find_or_create_oauth_user(profile):
    """
    A centralized function to find, create, or update a user from any source
    (standard signup, Google, or GitHub) and log them in.
    """
    try:
        # Input validation and sanitization
        provider = profile.get('provider')
        provider_id = profile.get('provider_id')
        name = sanitize_string(profile.get('name', ''), 100)
        email = sanitize_string(profile.get('email', ''), 254).lower()
        picture = sanitize_string(profile.get('picture', ''), 500)
        profile_url = sanitize_string(profile.get('profile_url', ''), 500)
        password_hash = profile.get('password_hash')  # Already hashed, don't sanitize
        
        # Validate inputs
        if not name:
            current_app.logger.error("Invalid name provided in profile")
            return redirect(url_for('frontend.error_page', error_message='Invalid user information provided.'))
        
        if email and not validate_email(email):
            current_app.logger.error(f"Invalid email format: {email}")
            return redirect(url_for('frontend.error_page', error_message='Invalid email format provided.'))
        
        if provider and not validate_provider_id(provider, provider_id):
            current_app.logger.error(f"Invalid provider ID for {provider}: {provider_id}")
            return redirect(url_for('frontend.error_page', error_message='Invalid provider information.'))
        
        all_data = get_all_data_from_db()
        all_users = get_all_users_from_db()
        
        # --- Robust User Finding Logic ---
        user_record = None
        
        # Priority 1: Find user by their unique OAuth provider ID.
        if provider and provider_id:
            provider_id_str = str(provider_id)
            user_record = next((u for u in all_users if u.get(f"{provider}_id") == provider_id_str), None)
        
        # Priority 2: If not found, find by email address.
        if not user_record and email:
            user_record = get_user_by_email(email)
        
        # --- Case 1: User Exists ---
        if user_record:
            # Get a direct reference to the user's dictionary in the list to update it
            user_to_update = next((u for u in all_users if u['id'] == user_record['id']), None)
            user_data_to_update = all_data.get(user_record['id'])
            
            if not user_to_update or not user_data_to_update:
                current_app.logger.error(f"Data inconsistency for user ID: {user_record['id']}")
                return redirect(url_for('frontend.error_page', error_message='Data inconsistency detected.'))
            
            # Always update name on login (but validate first)
            user_to_update['username'] = name
            user_data_to_update['user_settings']['name'] = name
            
            # Update email if provided and valid
            if email and not user_data_to_update['user_settings'].get('email'):
                user_data_to_update['user_settings']['email'] = email
            
            # Only update the main picture if a new one is provided
            if picture:
                user_data_to_update['user_settings']['picture'] = picture
            
            # Link the new OAuth provider if it's an OAuth login
            if provider and provider_id:
                # Check if this provider ID is already linked to another user
                existing_user = next((u for u in all_users if u.get(f"{provider}_id") == str(provider_id) and u['id'] != user_record['id']), None)
                if existing_user:
                    current_app.logger.warning(f"Attempted to link {provider} ID {provider_id} to user {user_record['id']}, but it's already linked to user {existing_user['id']}")
                    return redirect(url_for('frontend.error_page', error_message=f'This {provider.title()} account is already linked to another user.'))
                
                user_to_update[f"{provider}_id"] = str(provider_id)
                
                if provider == 'google' and picture:
                    user_data_to_update['user_settings']['google_picture'] = picture
                elif provider == 'github':
                    if picture:
                        user_data_to_update['user_settings']['github_picture'] = picture
                    if profile_url:
                        user_data_to_update['user_settings']['github_profile_url'] = profile_url
            
            final_user_record = user_to_update
            
        # --- Case 2: New User ---
        else:
            # Check if provider ID already exists for new user creation
            if provider and provider_id:
                existing_user = next((u for u in all_users if u.get(f"{provider}_id") == str(provider_id)), None)
                if existing_user:
                    current_app.logger.warning(f"Attempted to create new user with existing {provider} ID {provider_id}")
                    return redirect(url_for('frontend.error_page', error_message=f'This {provider.title()} account is already registered.'))
            
            # Check if email already exists for new user creation
            if email:
                existing_user = get_user_by_email(email)
                if existing_user:
                    current_app.logger.warning(f"Attempted to create new user with existing email {email}")
                    return redirect(url_for('frontend.error_page', error_message='An account with this email already exists.'))
            
            # Generate new user ID safely
            try:
                new_user_id = str(max(int(u['id']) for u in all_users) + 1) if all_users else "1"
            except (ValueError, TypeError):
                current_app.logger.error("Error generating new user ID")
                return redirect(url_for('frontend.error_page', error_message='System error. Please try again.'))
            
            final_user_record = {
                'id': new_user_id, 
                'username': name, 
                'password_hash': password_hash,  # Used for standard signup
                'google_id': str(provider_id) if provider == 'google' else None,
                'github_id': str(provider_id) if provider == 'github' else None,
            }
            all_users.append(final_user_record)
            
            # Create and add the new user's application data
            user_data_to_update = create_default_user_data(name=name, email=email)
            
            if picture:
                user_data_to_update['user_settings']['picture'] = picture
                
            if provider == 'google' and picture:
                user_data_to_update['user_settings']['google_picture'] = picture
            elif provider == 'github':
                if picture:
                    user_data_to_update['user_settings']['github_picture'] = picture
                if profile_url:
                    user_data_to_update['user_settings']['github_profile_url'] = profile_url
                    
            all_data[new_user_id] = user_data_to_update
        
        # Save all changes back to the database
        try:
            save_all_users_to_db(all_users)
            save_all_data_to_db(all_data)
        except Exception as e:
            current_app.logger.error(f"Database save error: {e}")
            return redirect(url_for('frontend.error_page', error_message='Failed to save user data. Please try again.'))
        
        # Log the user in with the final, updated record
        user_obj = User(final_user_record['id'], final_user_record['username'], final_user_record.get('password_hash'))
        login_user(user_obj, remember=True)
        
        current_app.logger.info(f"User {final_user_record['id']} logged in successfully")
        return redirect(url_for('frontend.home'))
        
    except Exception as e:
        current_app.logger.error(f"Unexpected error in find_or_create_oauth_user: {e}")
        return redirect(url_for('frontend.error_page', error_message='An unexpected error occurred. Please try again.'))
