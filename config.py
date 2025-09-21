import os
from datetime import timedelta

class Config:
    # Application Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'a-fallback-secret-key-for-development')
    
    # Flask-Mail Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
    ADMIN_GOOGLE_ID = os.getenv('ADMIN_GOOGLE_ID')
    ADMIN_GITHUB_ID = os.getenv('ADMIN_GITHUB_ID') # Optional: The numeric ID from a GitHub account
   
    
    # Session Configuration
    REMEMBER_COOKIE_DURATION = timedelta(days=7)

    ENCRYPTION_USER_KEY = os.getenv('ENCRYPTION_USER_KEY', 'default-super-strong-password-for-qr')
    ENCRYPTION_SALT = os.getenv('ENCRYPTION_SALT', 'a_default_fixed_salt_for_qr_keys')
    
    # OAuth Configuration
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
    GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
    GITHUB_LINK_CLIENT_ID = os.getenv('GITHUB_LINK_CLIENT_ID')
    GITHUB_LINK_CLIENT_SECRET = os.getenv('GITHUB_LINK_CLIENT_SECRET')
    
    # External API Configuration
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key="
    GEMINI_API_KEY = ""  # Your API Key will be automatically provided by the Canvas environment
    
    # MQTT Configuration
    MQTT_BROKER = "mqtt.eclipse.org"
    MQTT_PORT = 1883
    MQTT_TOPIC_COMMAND = "lumino_us/commands"
    MQTT_TOPIC_STATUS = "lumino_us/status"
    
    # Application Constants
    ELECTRICITY_RATE = 6.50
    ANALYTICS_FILE = 'analytics_data.csv'
    
    # Redis Configuration
    REDIS_URL = os.getenv('REDIS_URL')
    if not REDIS_URL:
        raise RuntimeError("FATAL: REDIS_URL environment variable not set.")
