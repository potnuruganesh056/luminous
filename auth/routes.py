from flask import Blueprint, render_template, redirect, url_for, request, session, flash, current_app
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from auth.models import User
from database.redis_db import get_all_users_from_db
from oauth.helpers import find_or_create_oauth_user
from security import rate_limit, validate_password, validate_input_length, check_suspicious_activity, log_security_event

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signin', methods=['GET', 'POST'])
@rate_limit(max_requests=10, window=900)  # 10 attempts per 15 minutes
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('frontend.home'))
    
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            
            # Input validation
            if not username or not password:
                flash('Username and password are required.', 'error')
                return redirect(url_for('auth.signin'))
            
            # Validate input lengths
            valid, message = validate_input_length(username, 'Username', current_app.config.get('MAX_USERNAME_LENGTH', 50))
            if not valid:
                flash(message, 'error')
                return redirect(url_for('auth.signin'))
            
            # Check for suspicious activity
            if check_suspicious_activity(ip_address=request.remote_addr, action='login_attempt'):
                log_security_event('SUSPICIOUS_LOGIN_ACTIVITY', f'Multiple login attempts from {request.remote_addr}')
                flash('Too many login attempts. Please try again later.', 'error')
                return redirect(url_for('auth.signin'))
            
            all_users = get_all_users_from_db()
            user_data = next((u for u in all_users if u['username'] == username), None)
            
            if user_data and user_data.get('password_hash') and check_password_hash(user_data['password_hash'], password):
                # Successful login
                user_obj = User(user_data['id'], user_data['username'], user_data['password_hash'])
                login_user(user_obj, remember=request.form.get('remember_me') == 'on')
                
                # Log successful login
                current_app.logger.info(f"Successful login for user {username} from {request.remote_addr}")
                
                # Check for next parameter but validate it
                next_page = request.args.get('next')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                
                return redirect(url_for('frontend.home'))
            else:
                # Failed login attempt
                log_security_event('FAILED_LOGIN', f'Failed login attempt for username: {username}')
                flash('Invalid username or password.', 'error')
                return redirect(url_for('auth.signin'))
                
        except Exception as e:
            current_app.logger.error(f"Signin error: {e}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return redirect(url_for('auth.signin'))
            
    return render_template('signin.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
@rate_limit(max_requests=5, window=3600)  # 5 signups per hour
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('frontend.home'))
    
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Input validation
            if not username or not password or not confirm_password:
                flash('All fields are required.', 'error')
                return redirect(url_for('auth.signup'))
            
            if password != confirm_password:
                flash('Passwords do not match.', 'error')
                return redirect(url_for('auth.signup'))
            
            # Validate input lengths
            valid, message = validate_input_length(username, 'Username', current_app.config.get('MAX_USERNAME_LENGTH', 50))
            if not valid:
                flash(message, 'error')
                return redirect(url_for('auth.signup'))
            
            # Validate password strength
            valid, message = validate_password(password)
            if not valid:
                flash(message, 'error')
                return redirect(url_for('auth.signup'))
            
            # Check for suspicious activity
            if check_suspicious_activity(ip_address=request.remote_addr, action='signup_attempt'):
                log_security_event('SUSPICIOUS_SIGNUP_ACTIVITY', f'Multiple signup attempts from {request.remote_addr}')
                flash('Too many signup attempts. Please try again later.', 'error')
                return redirect(url_for('auth.signup'))
            
            # Check if username already exists
            all_users = get_all_users_from_db()
            if any(u['username'].lower() == username.lower() for u in all_users):
                flash('Username already exists. Please choose a different one.', 'error')
                return redirect(url_for('auth.signup'))
            
            # Validate username format (alphanumeric and basic special chars only)
            if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
                flash('Username can only contain letters, numbers, underscores, dots, and hyphens.', 'error')
                return redirect(url_for('auth.signup'))
            
            # Create user profile
            profile = {
                "provider": None,  # Indicates a standard signup, not OAuth
                "provider_id": None,
                "name": username,
                "email": "",  # Standard signup doesn't require an email upfront
                "picture": None,
                "password_hash": generate_password_hash(password, method='pbkdf2:sha256:600000')  # Strong hashing
            }
            
            # Log successful signup
            current_app.logger.info(f"New user signup: {username} from {request.remote_addr}")
            
            # Use centralized creation function
            return find_or_create_oauth_user(profile)
            
        except Exception as e:
            current_app.logger.error(f"Signup error: {e}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return redirect(url_for('auth.signup'))
            
    return render_template('signup.html')

@auth_bp.route('/logout')
def logout():
    user_id = current_user.id if current_user.is_authenticated else None
    
    # Clear all session data
    session.clear()
    logout_user()
    
    # Log logout
    if user_id:
        current_app.logger.info(f"User {user_id} logged out from {request.remote_addr}")
    
    flash("You have been successfully logged out.", "success")
    return redirect(url_for('auth.signin'))
