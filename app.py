import os
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from authlib.integrations.flask_client import OAuth

from config import Config
from database.redis_db import redis_client, migrate_json_to_redis
from auth.models import User, load_user
from mqtt.client import run_mqtt_thread

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

# Import and register blueprints
from auth.routes import auth_bp
from api.routes import api_bp
from frontend.routes import frontend_bp
from oauth.routes import oauth_bp

app.register_blueprint(auth_bp)
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(frontend_bp)
app.register_blueprint(oauth_bp)

# Configure OAuth providers
from oauth.providers import configure_oauth_providers
configure_oauth_providers(oauth)

if __name__ == '__main__':
    with app.app_context():
        # Run the migration once on startup if needed
        migrate_json_to_redis()
    
    run_mqtt_thread()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
