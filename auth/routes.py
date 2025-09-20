from flask import Blueprint, render_template, redirect, url_for, request, session
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from auth.models import User
from database.redis_db import get_all_users_from_db
from oauth.helpers import find_or_create_oauth_user # Import the centralized helper

auth_bp = Blueprint('auth', __name__)

# The _create_new_user_entry function has been removed as it is no longer needed.

@auth_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('frontend.home'))
    
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            
            all_users = get_all_users_from_db()
            user_data = next((u for u in all_users if u['username'] == username), None)

            if user_data and user_data.get('password_hash') and check_password_hash(user_data['password_hash'], password):
                user_obj = User(user_data['id'], user_data['username'], user_data['password_hash'])
                login_user(user_obj, remember=True)
                return redirect(url_for('frontend.home'))
            
            flash('Invalid username or password.', 'error')
            return redirect(url_for('auth.signin'))

        except Exception as e:
            flash('An unexpected error occurred. Please try again.', 'error')
            return redirect(url_for('auth.signin'))
            
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
        
        # MODIFICATION: Use the centralized creation function from oauth.helpers
        profile = {
            "provider": None, # Indicates a standard signup, not OAuth
            "provider_id": None,
            "name": username,
            "email": "", # Standard signup doesn't require an email upfront
            "picture": None,
            "password_hash": generate_password_hash(password)
        }
        # This one function now handles creating the user and logging them in
        return find_or_create_oauth_user(profile)

    return render_template('signup.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    logout_user()
    flash("You have been successfully logged out.", "success")
    return redirect(url_for('auth.signin'))
