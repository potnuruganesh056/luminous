import os
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from authlib.integrations.flask_client import OAuth

from config import Config
from database.redis_db import redis_client, migrate_json_to_redis
from auth.models import User, load_user
from mqtt.client import run_mqtt_thread

# Import and register blueprints
from admin.init_admin import init_admin
from auth.routes import auth_bp
from api.routes import api_bp
from api.ai_routes import ai_api_bp
from frontend.routes import frontend_bp
from oauth.routes import oauth_bp
from analytics.routes import analytics_bp
from admin.routes import admin_bp             # <-- IMPORT ADMIN FRONTEND
from admin.api_routes import admin_api_bp     # <-- IMPORT ADMIN API

# Configure OAuth providers
from oauth.providers import configure_oauth_providers

# --- Application Setup ---
app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.signin'
login_manager.user_loader(load_user)

mail = Mail(app)

# OAuth Configuration
oauth = OAuth(app)

app.register_blueprint(auth_bp)
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(ai_api_bp, url_prefix='/api')
app.register_blueprint(frontend_bp)
app.register_blueprint(oauth_bp)
app.register_blueprint(analytics_bp, url_prefix='/api')
app.register_blueprint(admin_bp)              # <-- REGISTER ADMIN FRONTEND
app.register_blueprint(admin_api_bp, url_prefix='/api') # <-- REGISTER ADMIN API

configure_oauth_providers(oauth)

if __name__ == '__main__':
    with app.app_context():
        # Run the migration once on startup if needed
        migrate_json_to_redis()
    
    run_mqtt_thread()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
