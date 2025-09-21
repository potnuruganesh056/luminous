from flask import Blueprint, redirect, url_for, request, flash
from flask_login import login_required, current_user, login_user
from oauth.helpers import find_or_create_oauth_user
from database.redis_db import get_all_users_from_db, get_all_data_from_db, save_all_users_to_db, save_all_data_to_db

oauth_bp = Blueprint('oauth', __name__)

# We need to import the oauth instance from the current app context
from flask import current_app

@oauth_bp.route('/login/google')
def login_google():
    oauth_client = current_app.extensions['authlib.integrations.flask_client']
    redirect_uri = url_for('oauth.authorize_google', _external=True)
    return oauth_client.google.authorize_redirect(redirect_uri)

@oauth_bp.route('/google/callback')
def authorize_google():
    try:
        oauth_client = current_app.extensions['authlib.integrations.flask_client']
        token = oauth_client.google.authorize_access_token()
        user_info = oauth_client.google.get('userinfo').json()

        # --- TEMPORARY CODE TO GET YOUR GOOGLE ID ---
        print("\n--- GOOGLE USER INFO ---")
        print(user_info)
        print("--------------------------\n")
        # --- END OF TEMPORARY CODE ---

        profile = {
            'provider': 'google',
            'provider_id': user_info.get('sub'),
            'name': user_info.get('name'),
            'email': user_info.get('email'),
            'picture': user_info.get('picture')
        }
        return find_or_create_oauth_user(profile)
    except Exception as e:
        print(f"--- GOOGLE LOGIN ERROR --- \n{e}\n--------------------------")
        return redirect(url_for('frontend.error_page', error_message='Google login failed. Please try again.'))

@oauth_bp.route('/login/github')
def login_github():
    oauth_client = current_app.extensions['authlib.integrations.flask_client']
    redirect_uri = url_for('oauth.authorize_github', _external=True)
    return oauth_client.github.authorize_redirect(redirect_uri)

@oauth_bp.route('/github/callback')
def authorize_github():
    try:
        oauth_client = current_app.extensions['authlib.integrations.flask_client']
        token = oauth_client.github.authorize_access_token()
        user_info = oauth_client.github.get('user').json()
        
        # --- TEMPORARY CODE TO GET YOUR GITHUB ID ---
        print("\n--- GITHUB USER INFO ---")
        print(user_info)
        print("--------------------------\n")
        # --- END OF TEMPORARY CODE ---

        user_emails = oauth_client.github.get('user/emails').json()
        primary_email = next((e['email'] for e in user_emails if e['primary']), None)
        
        if not primary_email:
            flash("Could not retrieve a primary email from GitHub.", "error")
            return redirect(url_for('auth.signin'))
            
        profile = {
            'provider': 'github',
            'provider_id': user_info.get('id'),
            'name': user_info.get('name') or user_info.get('login'),
            'email': primary_email,
            'picture': user_info.get('avatar_url'),
            'profile_url': user_info.get('html_url')
        }
        return find_or_create_oauth_user(profile)
    except Exception as e:
        print(f"--- GITHUB LOGIN ERROR --- \n{e}\n--------------------------")
        return redirect(url_for('frontend.error_page', error_message='GitHub login failed. Please try again.'))


@oauth_bp.route('/link/google')
@login_required
def link_google():
    all_users = get_all_users_from_db()
    user_record = next((u for u in all_users if u['id'] == current_user.id), None)
    
    if user_record and user_record.get('google_id'):
        flash("Your account is already linked to Google.", "info")
        return redirect(url_for('frontend.settings'))
    
    oauth_client = current_app.extensions['authlib.integrations.flask_client']
    redirect_uri = url_for('oauth.link_authorize_google', _external=True)
    return oauth_client.google.authorize_redirect(redirect_uri)

@oauth_bp.route('/link/github')
@login_required
def link_github():
    all_users = get_all_users_from_db()
    user_record = next((u for u in all_users if u['id'] == current_user.id), None)

    if user_record and user_record.get('github_id'):
        flash("Your account is already linked to GitHub.", "info")
        return redirect(url_for('frontend.settings'))
    
    oauth_client = current_app.extensions['authlib.integrations.flask_client']
    redirect_uri = url_for('oauth.link_authorize_github', _external=True)
    return oauth_client.github_link.authorize_redirect(redirect_uri)

@oauth_bp.route('/link/google/callback')
@login_required
def link_authorize_google():
    try:
        oauth_client = current_app.extensions['authlib.integrations.flask_client']
        token = oauth_client.google.authorize_access_token()
        user_info = oauth_client.google.get('userinfo').json()

        all_users = get_all_users_from_db()
        all_data = get_all_data_from_db()

        user_record = next((u for u in all_users if u['id'] == current_user.id), None)
        user_profile_data = all_data.get(current_user.id)
        
        if not user_record or not user_profile_data:
            flash("A data inconsistency was detected. Please contact support.", "error")
            return redirect(url_for('frontend.settings'))

        user_record['google_id'] = user_info.get('sub')
        user_profile_data['user_settings']['google_picture'] = user_info.get('picture')
        if not user_profile_data['user_settings'].get('email'):
            user_profile_data['user_settings']['email'] = user_info.get('email')

        save_all_users_to_db(all_users)
        save_all_data_to_db(all_data)

        flash("Your Google account has been successfully linked.", "success")
        return redirect(url_for('frontend.settings'))
        
    except Exception as e:
        print(f"Error linking Google account: {e}")
        flash("An error occurred while linking your Google account. Please try again.", "error")
        return redirect(url_for('frontend.settings'))

@oauth_bp.route('/link/github/callback')
@login_required
def link_authorize_github():
    try:
        oauth_client = current_app.extensions['authlib.integrations.flask_client']
        token = oauth_client.github_link.authorize_access_token()
        user_info = oauth_client.github_link.get('user').json()
        
        all_users = get_all_users_from_db()
        all_data = get_all_data_from_db()

        user_record = next((u for u in all_users if u['id'] == current_user.id), None)
        user_profile_data = all_data.get(current_user.id)

        if not user_record or not user_profile_data:
            flash("A data inconsistency was detected. Please contact support.", "error")
            return redirect(url_for('frontend.settings'))

        user_record['github_id'] = user_info.get('id')
        user_profile_data['user_settings']['github_picture'] = user_info.get('avatar_url')
        user_profile_data['user_settings']['github_profile_url'] = user_info.get('html_url')
        
        save_all_users_to_db(all_users)
        save_all_data_to_db(all_data)
        
        flash("Your GitHub account has been successfully linked.", "success")
        return redirect(url_for('frontend.settings'))

    except Exception as e:
        print(f"Error linking GitHub account: {e}")
        flash("An error occurred while linking your GitHub account. Please try again.", "error")
        return redirect(url_for('frontend.settings'))

@oauth_bp.route('/oauth-result')
def oauth_result():
    """Displays a branded page after OAuth login (success or error)."""
    status = request.args.get('status', 'success')
    message = request.args.get('message', 'Login successful! Welcome to Luminous Home System.')
    return render_template('oauth_result.html', status=status, message=message)

