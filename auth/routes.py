from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from auth.models import User, create_default_user_data
from database.redis_db import get_all_users_from_db, get_all_data_from_db, save_all_users_to_db, save_all_data_to_db

auth_bp = Blueprint('auth', __name__)

def _create_new_user_entry(profile):
    """Helper to create new user records in both 'users' and 'data' stores."""
    all_users = get_all_users_from_db()
    all_data = get_all_data_from_db()

    new_user_id = str(int(all_users[-1]['id']) + 1) if all_users else "1"
    
    # Create the authentication record for the 'users' key
    new_user_record = {
        'id': new_user_id,
        'username': profile['name'],
        'password_hash': profile.get('password_hash'), # Will be None for OAuth
        'google_id': profile['provider_id'] if profile.get('provider') == 'google' else None,
        'github_id': profile['provider_id'] if profile.get('provider') == 'github' else None,
    }
    all_users.append(new_user_record)

    # Create the application data record for the 'data' key
    all_data[new_user_id] = create_default_user_data(
        name=profile['name'],
        email=profile['email'],
        picture=profile.get('picture')
    )
    
    # Save everything back to the database
    save_all_users_to_db(all_users)
    save_all_data_to_db(all_data)

    return new_user_record

@auth_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('frontend.home'))
    
    if request.method == 'POST':
        # ... (try block and form reading) ...
        
        all_users = get_all_users_from_db()
        user_data = next((u for u in all_users if u['username'] == username), None)

        if user_data and user_data.get('password_hash') and check_password_hash(user_data['password_hash'], password):
            # --- NEW: Check if user is suspended ---
            if user_data.get('is_suspended'):
                flash('This account has been suspended.', 'error')
                return redirect(url_for('auth.signin'))
            # --- END NEW ---
                
            user_obj = User(user_data['id'], user_data['username'], user_data['password_hash'])
            login_user(user_obj, remember=True)
            return redirect(url_for('frontend.home'))
        
        flash('Invalid username or password.', 'error')
        return redirect(url_for('auth.signin'))
        
    # ... (rest of the function) ...
    return render_template('signin.html')


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('frontend.home'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if any(u['username'] == username for u in get_all_users_from_db()):
            flash('Username already exists.', 'error')
            return redirect(url_for('auth.signup'))
        
        # Use the centralized creation function
        profile = {
            "name": username,
            "email": "", # Standard signup doesn't have an email
            "password_hash": generate_password_hash(password)
        }
        new_user_record = _create_new_user_entry(profile)
        
        user_obj = User(new_user_record['id'], new_user_record['username'], new_user_record['password_hash'])
        login_user(user_obj)
        return redirect(url_for('frontend.home'))

    return render_template('signup.html')

@auth_bp.route('/logout')
def logout():
    # MODIFICATION: Clear the entire session dictionary
    session.clear()
    logout_user()
    flash("You have been successfully logged out.", "success")
    return redirect(url_for('auth.signin'))
