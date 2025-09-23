import os
from flask import Flask, jsonify, request
from flask_login import LoginManager
from flask_mail import Mail
from authlib.integrations.flask_client import OAuth

# 1. Import local modules
from config import Config
from database.redis_db import migrate_json_to_redis
from auth.models import User, load_user
from mqtt.client import run_mqtt_thread
from admin.init_admin import init_admin
from oauth.providers import configure_oauth_providers
from security import setup_security_headers, setup_logging, generate_csrf_token

def create_app():
    """
    Application factory function to create and configure the Flask app.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # --- Initialize Security ---
    setup_security_headers(app)
    setup_logging(app)

    # --- Initialize Extensions ---
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.signin'
    login_manager.user_loader(load_user)

    mail = Mail(app)
    oauth = OAuth(app)

    # --- Add CSRF Token to Template Context ---
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf_token)

    # --- Add Global Security Checks Before Each Request ---
    @app.before_request
    def security_checks():
        # Block requests with suspicious User-Agent headers
        user_agent = request.headers.get('User-Agent', '')
        if len(user_agent) > 500 or not user_agent:
            return jsonify({'error': 'Invalid request header'}), 400
            
        # Validate content length to prevent large, malicious uploads
        if request.content_length and request.content_length > app.config.get('MAX_FILE_UPLOAD_SIZE', 10485760):
            return jsonify({'error': 'Request entity too large'}), 413

    # --- Import and Register Blueprints ---
    # We import here to avoid circular dependency issues
    from auth.routes import auth_bp
    from api.routes import api_bp
    from api.ai_routes import ai_api_bp
    from frontend.routes import frontend_bp
    from oauth.routes import oauth_bp
    from analytics.routes import analytics_bp
    from admin.routes import admin_bp
    from admin.api_routes import admin_api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(ai_api_bp, url_prefix='/api')
    app.register_blueprint(frontend_bp)
    app.register_blueprint(oauth_bp)
    app.register_blueprint(analytics_bp, url_prefix='/api')
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_api_bp, url_prefix='/api/admin')

    # --- Final Configurations ---
    configure_oauth_providers(oauth)

    # --- One-time Startup Logic ---
    # This block will run every time the app starts
    with app.app_context():
        migrate_json_to_redis()
        init_admin(app)

    return app

# --- Create App Instance for Gunicorn/Development ---
app = create_app()

# --- Run Application (This part is ONLY for local development) ---
if __name__ == '__main__':
    run_mqtt_thread()
    port = int(os.environ.get('PORT', 5000))
    # Use the created app instance to run
    app.run(host='0.0.0.0', port=port, debug=app.config.get('DEBUG', False))

