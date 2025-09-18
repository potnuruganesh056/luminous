import base64
import json
from hashlib import pbkdf2_hmac
from cryptography.fernet import Fernet, InvalidToken
from config import Config

# --- SETUP ENCRYPTION ENGINE ---
# This derives a strong, 32-byte encryption key from your user key and salt.
kdf = pbkdf2_hmac(
    'sha256',
    Config.ENCRYPTION_USER_KEY.encode('utf-8'),
    Config.ENCRYPTION_SALT.encode('utf-8'),
    100000,  # Recommended number of iterations
    dklen=32 # Get a 32-byte key
)
# The key must be URL-safe base64 encoded for Fernet
key = base64.urlsafe_b64encode(kdf)
f = Fernet(key)

def encrypt_data(data_dict):
    """
    Takes a Python dictionary, converts it to a JSON string, and encrypts it.
    Returns a URL-safe encrypted string.
    """
    try:
        json_string = json.dumps(data_dict, separators=(',', ':'))
        encrypted_bytes = f.encrypt(json_string.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')
    except Exception as e:
        print(f"Encryption failed: {e}")
        return None

def decrypt_data(encrypted_string):
    """
    Takes an encrypted string, decrypts it, and returns a Python dictionary.
    Returns None if decryption fails (e.g., invalid token, tampered data).
    """
    try:
        decrypted_bytes = f.decrypt(encrypted_string.encode('utf-8'))
        return json.loads(decrypted_bytes.decode('utf-8'))
    except (InvalidToken, json.JSONDecodeError, TypeError):
        # Return None for any decryption or parsing error
        return None
      
