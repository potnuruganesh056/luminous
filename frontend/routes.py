from flask import Blueprint, render_template, request
from flask_login import login_required
from utils.helpers import get_current_user_theme, get_user_data

frontend_bp = Blueprint('frontend', __name__)

@frontend_bp.route('/')
@login_required
def home():
    theme = get_current_user_theme()
    return render_template('home.html', theme=theme)

@frontend_bp.route('/control.html')
@login_required
def control():
    theme = get_current_user_theme()
    return render_template('control.html', theme=theme)

@frontend_bp.route('/settings.html')
@login_required
def settings():
    theme = get_current_user_theme()
    return render_template('settings.html', theme=theme)

@frontend_bp.route('/contact.html')
@login_required
def contact():
    theme = get_current_user_theme()
    return render_template('contact.html', theme=theme)

@frontend_bp.route('/analytics.html')
@login_required
def analytics():
    user_data = get_user_data()
    theme = user_data['user_settings']['theme']
    return render_template('analytics.html', theme=theme)

@frontend_bp.route('/error_page')
def error_page():
    # You can pass a specific error message to the template if needed
    return render_template('error.html', error_message="An unexpected error occurred. Please try again later.")
