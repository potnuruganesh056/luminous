from functools import wraps
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash
from auth.models import User
from database.redis_db import get_all_users_from_db, get_all_data_from_db

admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin', url_prefix='/secret-admin-panel')

def admin_required(f):
    """Decorator to ensure a user is an authenticated admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('admin.login'))
        
        # Fetch the user's full record to check the admin flag
        users = get_all_users_from_db()
        admin_user_data = next((u for u in users if u.get('id') == current_user.id), None)
        
        if not admin_user_data or not admin_user_data.get('is_admin'):
            abort(403) # Forbidden
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Bug Fix: Correctly check if the currently logged-in user is an admin
        users = get_all_users_from_db()
        user_record = next((u for u in users if u.get('id') == current_user.id), None)
        if user_record and user_record.get('is_admin'):
            return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        login_identifier = request.form['username'] # This can be a username OR an email
        password = request.form['password']
        
        all_users = get_all_users_from_db()
        all_data = get_all_data_from_db()
        user_data = None

        # --- Find user by username OR email ---
        user_data = next((u for u in all_users if u.get('username') == login_identifier), None)

        if not user_data:
            for user_id, data_record in all_data.items():
                if data_record.get("user_settings", {}).get("email") == login_identifier:
                    user_data = next((u for u in all_users if u.get('id') == user_id), None)
                    break
        
        # --- NEW: Improved Validation Logic ---
        if not user_data:
            flash('Account not found with that username or email.', 'error')
            return redirect(url_for('admin.login'))

        if not user_data.get('is_admin'):
            flash('This account does not have admin privileges.', 'error')
            return redirect(url_for('admin.login'))

        if not check_password_hash(user_data.get('password_hash', ''), password):
            flash('Invalid password. Please try again.', 'error')
            return redirect(url_for('admin.login'))

        # If all checks pass, log the user in
        user_obj = User(user_data['id'], user_data['username'], user_data['password_hash'])
        login_user(user_obj, remember=True)
        return redirect(url_for('admin.dashboard'))

    return render_template('admin_login.html')

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    return render_template('dashboard.html')

@admin_bp.route('/logout')
@admin_required
def logout():
    logout_user()
    flash('You have been logged out of the admin panel.', 'success')
    return redirect(url_for('admin.login'))
