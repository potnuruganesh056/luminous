from flask import request, jsonify, current_app, session
from functools import wraps
import time
import hashlib
import hmac
import re
from collections import defaultdict
import logging

# Simple in-memory rate limiter (use Redis in production)
rate_limit_store = defaultdict(list)

def setup_security_headers(app):
    """Add security headers to all responses"""
    @app.after_request
    def add_security_headers(response):
        headers = app.config.get('SECURITY_HEADERS', {})
        for header, value in headers.items():
            response.headers[header] = value
        return response

def setup_logging(app):
    """Setup secure logging"""
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename=app.config.get('LOG_FILE') if not app.config.get('DEBUG') else None
    )
    
    # Don't log sensitive data in production
    if not app.config.get('DEBUG'):
        logging.getLogger('werkzeug').setLevel(logging.WARNING)

def rate_limit(max_requests=100, window=3600, key_func=None):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if key_func:
                key = key_func()
            else:
                key = request.remote_addr
            
            now = time.time()
            
            # Clean old entries
            rate_limit_store[key] = [
                timestamp for timestamp in rate_limit_store[key] 
                if now - timestamp < window
            ]
            
            # Check rate limit
            if len(rate_limit_store[key]) >= max_requests:
                current_app.logger.warning(f"Rate limit exceeded for {key}")
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            # Add current request
            rate_limit_store[key].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_password(password):
    """Validate password strength based on config"""
    if len(password) < current_app.config.get('PASSWORD_MIN_LENGTH', 8):
        return False, "Password must be at least 8 characters long"
    
    if current_app.config.get('PASSWORD_REQUIRE_UPPERCASE', True):
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
    
    if current_app.config.get('PASSWORD_REQUIRE_LOWERCASE', True):
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
    
    if current_app.config.get('PASSWORD_REQUIRE_NUMBERS', True):
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
    
    if current_app.config.get('PASSWORD_REQUIRE_SPECIAL_CHARS', False):
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
    
    return True, "Password is valid"

def validate_input_length(value, field_name, max_length):
    """Validate input length"""
    if not value:
        return True, ""
    
    if len(str(value)) > max_length:
        return False, f"{field_name} is too long (maximum {max_length} characters)"
    
    return True, ""

def sanitize_filename(filename):
    """Sanitize uploaded filenames"""
    if not filename:
        return ""
    
    # Remove path components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Remove dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename

def csrf_protect(f):
    """CSRF protection decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            if not token or not validate_csrf_token(token):
                current_app.logger.warning(f"CSRF token validation failed for {request.remote_addr}")
                return jsonify({'error': 'Invalid CSRF token'}), 403
        return f(*args, **kwargs)
    return decorated_function

def generate_csrf_token():
    """Generate CSRF token"""
    if 'csrf_token' not in session:
        session['csrf_token'] = hashlib.sha256(
            str(time.time()).encode() + current_app.secret_key.encode()
        ).hexdigest()
    return session['csrf_token']

def validate_csrf_token(token):
    """Validate CSRF token"""
    return token and session.get('csrf_token') and hmac.compare_digest(
        session['csrf_token'], token
    )

def check_suspicious_activity(user_id=None, ip_address=None, action=None):
    """Check for suspicious activity patterns"""
    key = f"activity_{user_id or ip_address}_{action}"
    now = time.time()
    
    # Clean old entries (last 1 hour)
    rate_limit_store[key] = [
        timestamp for timestamp in rate_limit_store[key] 
        if now - timestamp < 3600
    ]
    
    # Add current activity
    rate_limit_store[key].append(now)
    
    # Check for suspicious patterns
    if len(rate_limit_store[key]) > 50:  # More than 50 actions per hour
        current_app.logger.warning(f"Suspicious activity detected: {key}")
        return True
    
    return False

def secure_headers_only():
    """Decorator to ensure HTTPS and secure headers"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # In production, enforce HTTPS
            if not current_app.config.get('DEBUG') and not request.is_secure:
                return jsonify({'error': 'HTTPS required'}), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_security_event(event_type, details, user_id=None):
    """Log security events"""
    current_app.logger.warning(
        f"SECURITY EVENT: {event_type} - User: {user_id} - IP: {request.remote_addr} - Details: {details}"
    )

def validate_redirect_url(url):
    """Validate redirect URLs to prevent open redirect attacks"""
    if not url:
        return True
    
    # Only allow relative URLs or URLs to the same domain
    if url.startswith('/'):
        return True
    
    if url.startswith(request.host_url):
        return True
    
    # Whitelist specific trusted domains if needed
    trusted_domains = current_app.config.get('TRUSTED_REDIRECT_DOMAINS', [])
    for domain in trusted_domains:
        if url.startswith(f"https://{domain}"):
            return True
    
    return False
