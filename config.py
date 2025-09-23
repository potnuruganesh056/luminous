import os
from datetime import timedelta

class Config:
    # Application Settings
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError("FATAL: SECRET_KEY environment variable not set. Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'")
    
    # Security Headers Configuration
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' https://apis.google.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.github.com https://www.googleapis.com",
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    # Flask-Mail Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    
    # Admin Configuration
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
    ADMIN_GOOGLE_ID = os.getenv('ADMIN_GOOGLE_ID')
    ADMIN_GITHUB_ID = os.getenv('ADMIN_GITHUB_ID')
   
    # Session Configuration - Enhanced Security
    SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to cookies
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    SESSION_PERMANENT = False
    
    # Rate Limiting Configuration
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL')  # Use Redis for rate limiting
    RATELIMIT_DEFAULT = "100 per hour"  # Default rate limit
    RATELIMIT_HEADERS_ENABLED = True
    
    # Password Security
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_SPECIAL_CHARS = False
    
    # OAuth Security Configuration
    OAUTH_SESSION_TIMEOUT = 600  # 10 minutes
    
    # Encryption Configuration
    ENCRYPTION_USER_KEY = os.getenv('ENCRYPTION_USER_KEY')
    ENCRYPTION_SALT = os.getenv('ENCRYPTION_SALT')
    
    if not ENCRYPTION_USER_KEY:
        raise RuntimeError("FATAL: ENCRYPTION_USER_KEY environment variable not set.")
    if not ENCRYPTION_SALT:
        raise RuntimeError("FATAL: ENCRYPTION_SALT environment variable not set.")
    
    # OAuth Configuration with validation
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
    GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
    GITHUB_LINK_CLIENT_ID = os.getenv('GITHUB_LINK_CLIENT_ID')
    GITHUB_LINK_CLIENT_SECRET = os.getenv('GITHUB_LINK_CLIENT_SECRET')
    
    # Validate OAuth credentials are present
    if not all([GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET]):
        raise RuntimeError("FATAL: OAuth credentials not properly configured. Check GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET environment variables.")
    
    # External API Configuration
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key="
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', "")
    
    # MQTT Configuration with security
    MQTT_BROKER = os.getenv('MQTT_BROKER', "mqtt.eclipseprojects.io")
    MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
    MQTT_TOPIC_COMMAND = os.getenv('MQTT_TOPIC_COMMAND', "lumino_us/commands")
    MQTT_TOPIC_STATUS = os.getenv('MQTT_TOPIC_STATUS', "lumino_us/status")
    MQTT_USERNAME = os.getenv('MQTT_USERNAME')  # Optional
    MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')  # Optional
    MQTT_USE_TLS = os.getenv('MQTT_USE_TLS', 'false').lower() in ['true', 'on', '1']
    
    # Application Constants
    ELECTRICITY_RATE = float(os.getenv('ELECTRICITY_RATE', 6.50))
    ANALYTICS_FILE = os.getenv('ANALYTICS_FILE', 'analytics_data.csv')
    
    # Input Validation Limits
    MAX_USERNAME_LENGTH = 50
    MAX_EMAIL_LENGTH = 254
    MAX_NAME_LENGTH = 100
    MAX_FILE_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Redis Configuration
    REDIS_URL = os.getenv('REDIS_URL')
    if not REDIS_URL:
        raise RuntimeError("FATAL: REDIS_URL environment variable not set.")
        
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    
    # Environment Detection
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    DEBUG = FLASK_ENV == 'development'
    
    # Override security settings for development
    if DEBUG:
        SESSION_COOKIE_SECURE = False
        REMEMBER_COOKIE_SECURE = False
