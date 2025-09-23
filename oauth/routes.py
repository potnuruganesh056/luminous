from flask import Blueprint, redirect, url_for, request, flash, render_template, session
from flask_login import login_required, current_user, login_user
from oauth.helpers import find_or_create_oauth_user
from database.redis_db import get_all_users_from_db, get_all_data_from_db, save_all_users_to_db, save_all_data_to_db
import secrets
import hashlib
import hmac
import time

oauth_bp = Blueprint('oauth', __name__)

# We need to import the oauth instance from the current app context
from flask import current_app

def generate_state_token():
    """Generate a secure state token for OAuth CSRF protection"""
    return secrets.token_urlsafe(32)

def verify_state_token(provided_state):
    """Verify the state token to prevent CSRF attacks"""
    session_state = session.get('oauth_state')
    if not session_state or not provided_state:
        return False
    return hmac.compare_digest(session_state, provided_state)

@oauth_bp.route('/login/google')
def login_google():
    try:
        oauth_client = current_app.extensions['authlib.integrations.flask_client']
        
        # Generate and store state token for CSRF protection
        state = generate_state_token()
        session['oauth_state'] = state
        session['oauth_provider'] = 'google'
        session['oauth_timestamp'] = time.time()
        
        redirect_uri = url_for('oauth.authorize_google', _external=True, _scheme='https')
        return oauth_client.google.authorize_redirect(redirect_uri, state=state)
    except Exception as e:
        current_app.logger.error(f"Google OAuth initiation error: {e}")
        flash("OAuth initialization failed. Please try again.", "error")
        return redirect(url_for('auth.signin'))

@oauth_bp.route('/google/callback')
def authorize_google():
    try:
        # Verify state token
        state = request.args.get('state')
        if not verify_state_token(state):
            flash("Invalid OAuth state. Please try again.", "error")
            return redirect(url_for('auth.signin'))
        
        # Check timestamp (expire after 10 minutes)
        oauth_timestamp = session.get('oauth_timestamp', 0)
        if time.time() - oauth_timestamp > 600:
            flash("OAuth session expired. Please try again.", "error")
            return redirect(url_for('auth.signin'))
        
        # Verify provider matches
        if session.get('oauth_provider') != 'google':
            flash("OAuth provider mismatch. Please try again.", "error")
            return redirect(url_for('auth.signin'))
        
        oauth_client = current_app.extensions['authlib.integrations.flask_client']
        token = oauth_client.google.authorize_access_token()
        
        if not token:
            flash("Failed to obtain OAuth token. Please try again.", "error")
            return redirect(url_for('auth.signin'))
        
        user_info = oauth_client.google.get('userinfo').json()
        
        # Validate required fields
        if not user_info.get('sub') or not user_info.get('email'):
            flash("Incomplete user information from Google. Please try again.", "error")
            return redirect(url_for('auth.signin'))

        profile = {
            'provider': 'google',
            'provider_id': str(user_info.get('sub')),  # Ensure string
            'name': user_info.get('name', '').strip(),
            'email': user_info.get('email', '').lower().strip(),
            'picture': user_info.get('picture')
        }
        
        # Clear OAuth session data
        session.pop('oauth_state', None)
        session.pop('oauth_provider', None)
        session.pop('oauth_timestamp', None)
        
        return find_or_create_oauth_user(profile)
        
    except Exception as e:
        current_app.logger.error(f"Google OAuth callback error: {e}")
        # Clear OAuth session data on error
        session.pop('oauth_state', None)
        session.pop('oauth_provider', None)
        session.pop('oauth_timestamp', None)
        return redirect(url_for('frontend.error_page', error_message='Google login failed. Please try again.'))

@oauth_bp.route('/login/github')
def login_github():
    try:
        oauth_client = current_app.extensions['authlib.integrations.flask_client']
        
        # Generate and store state token for CSRF protection
        state = generate_state_token()
        session['oauth_state'] = state
        session['oauth_provider'] = 'github'
        session['oauth_timestamp'] = time.time()
        
        redirect_uri = url_for('oauth.authorize_github', _external=True, _scheme='https')
        return oauth_client.github.authorize_redirect(redirect_uri, state=state)
    except Exception as e:
        current_app.logger.error(f"GitHub OAuth initiation error: {e}")
        flash("OAuth initialization failed. Please try again.", "error")
        return redirect(url_for('auth.signin'))

@oauth_bp.route('/github/callback')
def authorize_github():
    try:
        # Verify state token
        state = request.args.get('state')
        if not verify_state_token(state):
            flash("Invalid OAuth state. Please try again.", "error")
            return redirect(url_for('auth.signin'))
        
        # Check timestamp (expire after 10 minutes)
        oauth_timestamp = session.get('oauth_timestamp', 0)
        if time.time() - oauth_timestamp > 600:
            flash("OAuth session expired. Please try again.", "error")
            return redirect(url_for('auth.signin'))
        
        # Verify provider matches
        if session.get('oauth_provider') != 'github':
            flash("OAuth provider mismatch. Please try again.", "error")
            return redirect(url_for('auth.signin'))
        
        oauth_client = current_app.extensions['authlib.integrations.flask_client']
        token = oauth_client.github.authorize_access_token()
        
        if not token:
            flash("Failed to obtain OAuth token. Please try again.", "error")
            return redirect(url_for('auth.signin'))
            
        user_info = oauth_client.github.get('user').json()
        
        # Validate required fields
        if not user_info.get('id'):
            flash("Incomplete user information from GitHub. Please try again.", "error")
            return redirect(url_for('auth.signin'))
        
        user_emails = oauth_client.github.get('user/emails').json()
        primary_email = next((e['email'] for e in user_emails if e['primary']), None)
        
        if not primary_email:
            flash("Could not retrieve a primary email from GitHub.", "error")
            return redirect(url_for('auth.signin'))
            
        profile = {
            'provider': 'github',
            'provider_id': str(user_info.get('id')),  # Ensure string
            'name': (user_info.get('name') or user_info.get('login', '')).strip(),
            'email': primary_email.lower().strip(),
            'picture': user_info.get('avatar_url'),
            'profile_url': user_info.get('html_url')
        }
        
        # Clear OAuth session data
        session.pop('oauth_state', None)
        session.pop('oauth_provider', None)
        session.pop('oauth_timestamp', None)
        
        return find_or_create_oauth_user(profile)
        
    except Exception as e:
        current_app.logger.error(f"GitHub OAuth callback error: {e}")
        # Clear OAuth session data on error
        session.pop('oauth_state', None)
        session.pop('oauth_provider', None)
        session.pop('oauth_timestamp', None)
        return redirect(url_for('frontend.error_page', error_message='GitHub login failed. Please try again.'))

@oauth_bp.route('/link/google')
@login_required
def link_google():
    try:
        all_users = get_all_users_from_db()
        user_record = next((u for u in all_users if u['id'] == current_user.id), None)
        
        if user_record and user_record.get('google_id'):
            flash("Your account is already linked to Google.", "info")
            return redirect(url_for('frontend.settings'))
        
        # Generate and store state token for CSRF protection
        state = generate_state_token()
        session['oauth_state'] = state
        session['oauth_provider'] = 'google_link'
        session['oauth_timestamp'] = time.time()
        
        oauth_client = current_app.extensions['authlib.integrations.flask_client']
        redirect_uri = url_for('oauth.link_authorize_google', _external=True, _scheme='https')
        return oauth_client.google.authorize_redirect(redirect_uri, state=state)
    except Exception as e:
        current_app.logger.error(f"Google link initiation error: {e}")
        flash("Failed to initiate Google linking. Please try again.", "error")
        return redirect(url_for('frontend.settings'))

@oauth_bp.route('/link/github')
@login_required
def link_github():
    try:
        all_users = get_all_users_from_db()
        user_record = next((u for u in all_users if u['id'] == current_user.id), None)

        if user_record and user_record.get('github_id'):
            flash("Your account is already linked to GitHub.", "info")
            return redirect(url_for('frontend.settings'))
        
        # Generate and store state token for CSRF protection
        state = generate_state_token()
        session['oauth_state'] = state
        session['oauth_provider'] = 'github_link'
        session['oauth_timestamp'] = time.time()
        
        oauth_client = current_app.extensions['authlib.integrations.flask_client']
        redirect_uri = url_for('oauth.link_authorize_github', _external=True, _scheme='https')
        return oauth_client.github_link.authorize_redirect(redirect_uri, state=state)
    except Exception as e:
        current_app.logger.error(f"GitHub link initiation error: {e}")
        flash("Failed to initiate GitHub linking. Please try again.", "error")
        return redirect(url_for('frontend.settings'))

@oauth_bp.route('/link/google/callback')
@login_required
def link_authorize_google():
    try:
        # Verify state token
        state = request.args.get('state')
        if not verify_state_token(state):
            flash("Invalid OAuth state. Please try again.", "error")
            return redirect(url_for('frontend.settings'))
        
        # Check timestamp and provider
        oauth_timestamp = session.get('oauth_timestamp', 0)
        if time.time() - oauth_timestamp > 600:
            flash("OAuth session expired. Please try again.", "error")
            return redirect(url_for('frontend.settings'))
        
        if session.get('oauth_provider') != 'google_link':
            flash("OAuth provider mismatch. Please try again.", "error")
            return redirect(url_for('frontend.settings'))
        
        oauth_client = current_app.extensions['authlib.integrations.flask_client']
        token = oauth_client.google.authorize_access_token()
        
        if not token:
            flash("Failed to obtain OAuth token. Please try again.", "error")
            return redirect(url_for('frontend.settings'))
            
        user_info = oauth_client.google.get('userinfo').json()

        all_users = get_all_users_from_db()
        all_data = get_all_data_from_db()

        user_record = next((u for u in all_users if u['id'] == current_user.id), None)
        user_profile_data = all_data.get(current_user.id)
        
        if not user_record or not user_profile_data:
            flash("A data inconsistency was detected. Please contact support.", "error")
            return redirect(url_for('frontend.settings'))

        # Check if this Google account is already linked to another user
        google_id = str(user_info.get('sub'))
        existing_user = next((u for u in all_users if u.get('google_id') == google_id and u['id'] != current_user.id), None)
        if existing_user:
            flash("This Google account is already linked to another user.", "error")
            return redirect(url_for('frontend.settings'))

        user_record['google_id'] = google_id
        user_profile_data['user_settings']['google_picture'] = user_info.get('picture')
        if not user_profile_data['user_settings'].get('email'):
            user_profile_data['user_settings']['email'] = user_info.get('email', '').lower().strip()

        save_all_users_to_db(all_users)
        save_all_data_to_db(all_data)

        # Clear OAuth session data
        session.pop('oauth_state', None)
        session.pop('oauth_provider', None)
        session.pop('oauth_timestamp', None)

        flash("Your Google account has been successfully linked.", "success")
        return redirect(url_for('frontend.settings'))
        
    except Exception as e:
        current_app.logger.error(f"Error linking Google account: {e}")
        # Clear OAuth session data on error
        session.pop('oauth_state', None)
        session.pop('oauth_provider', None)
        session.pop('oauth_timestamp', None)
        flash("An error occurred while linking your Google account. Please try again.", "error")
        return redirect(url_for('frontend.settings'))

@oauth_bp.route('/link/github/callback')
@login_required
def link_authorize_github():
    try:
        # Verify state token
        state = request.args.get('state')
        if not verify_state_token(state):
            flash("Invalid OAuth state. Please try again.", "error")
            return redirect(url_for('frontend.settings'))
        
        # Check timestamp and provider
        oauth_timestamp = session.get('oauth_timestamp', 0)
        if time.time() - oauth_timestamp > 600:
            flash("OAuth session expired. Please try again.", "error")
            return redirect(url_for('frontend.settings'))
        
        if session.get('oauth_provider') != 'github_link':
            flash("OAuth provider mismatch. Please try again.", "error")
            return redirect(url_for('frontend.settings'))
        
        oauth_client = current_app.extensions['authlib.integrations.flask_client']
        token = oauth_client.github_link.authorize_access_token()
        
        if not token:
            flash("Failed to obtain OAuth token. Please try again.", "error")
            return redirect(url_for('frontend.settings'))
            
        user_info = oauth_client.github_link.get('user').json()
        
        all_users = get_all_users_from_db()
        all_data = get_all_data_from_db()

        user_record = next((u for u in all_users if u['id'] == current_user.id), None)
        user_profile_data = all_data.get(current_user.id)

        if not user_record or not user_profile_data:
            flash("A data inconsistency was detected. Please contact support.", "error")
            return redirect(url_for('frontend.settings'))

        # Check if this GitHub account is already linked to another user
        github_id = str(user_info.get('id'))
        existing_user = next((u for u in all_users if u.get('github_id') == github_id and u['id'] != current_user.id), None)
        if existing_user:
            flash("This GitHub account is already linked to another user.", "error")
            return redirect(url_for('frontend.settings'))

        user_record['github_id'] = github_id
        user_profile_data['user_settings']['github_picture'] = user_info.get('avatar_url')
        user_profile_data['user_settings']['github_profile_url'] = user_info.get('html_url')
        
        save_all_users_to_db(all_users)
        save_all_data_to_db(all_data)
        
        # Clear OAuth session data
        session.pop('oauth_state', None)
        session.pop('oauth_provider', None)
        session.pop('oauth_timestamp', None)
        
        flash("Your GitHub account has been successfully linked.", "success")
        return redirect(url_for('frontend.settings'))

    except Exception as e:
        current_app.logger.error(f"Error linking GitHub account: {e}")
        # Clear OAuth session data on error
        session.pop('oauth_state', None)
        session.pop('oauth_provider', None)
        session.pop('oauth_timestamp', None)
        flash("An error occurred while linking your GitHub account. Please try again.", "error")
        return redirect(url_for('frontend.settings'))

@oauth_bp.route('/oauth-result')
def oauth_result():
    """Displays a branded page after OAuth login (success or error)."""
    status = request.args.get('status', 'success')
    message = request.args.get('message', 'Login successful! Welcome to Luminous Home System.')
    
    # Sanitize the message to prevent XSS
    if status not in ['success', 'error']:
        status = 'success'
    
    # Limit message length and sanitize
    message = str(message)[:200] if message else 'Operation completed.'
    
    return render_template('oauth_result.html', status=status, message=message)
