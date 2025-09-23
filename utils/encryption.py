import base64
import json
from hashlib import pbkdf2_hmac
from cryptography.fernet import Fernet, InvalidToken
from config import Config

# --- SETUP ENCRYPTION ENGINE ---
# This derives a strong, 32-byte encryption key from your user key and salt.
derived_key = pbkdf2_hmac(
    'sha256',
    Config.ENCRYPTION_USER_KEY.encode('utf-8'),
    Config.ENCRYPTION_SALT.encode('utf-8'),
    100000,
    dklen=32  # Get a 32-byte key for AES-256
)
# The key must be URL-safe base64 encoded for Fernet
key = base64.urlsafe_b64encode(kdf)
f = Fernet(key)

def encrypt_data(data_dict):
    """
    Encrypts a dictionary using AES-GCM, providing confidentiality and integrity.
    Returns a base64-encoded string containing nonce, tag, and ciphertext.
    """
    try:
        json_string = json.dumps(data_dict, separators=(',', ':'))
        header = b'Luminous Encrypted Data' # Optional header for context
        plaintext = json_string.encode('utf-8')

        # Create a new AES cipher object in GCM mode
        cipher = AES.new(derived_key, AES.MODE_GCM)
        cipher.update(header)
        
        # Encrypt the data
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)
        
        # Combine the nonce, tag, and ciphertext for storage/transmission
        # We need all three parts to decrypt successfully
        combined_data = cipher.nonce + tag + ciphertext
        
        return base64.b64encode(combined_data).decode('utf-8')
    except Exception as e:
        print(f"Encryption failed: {e}")
        return None

def decrypt_data(encrypted_b64_string):
    """
    Decrypts a base64-encoded string that was encrypted with AES-GCM.
    Verifies the integrity of the data before returning the dictionary.
    """
    try:
        combined_data = base64.b64decode(encrypted_b64_string)
        header = b'Luminous Encrypted Data'

        # Extract the nonce, tag, and ciphertext from the combined data
        nonce = combined_data[:16]  # GCM nonce is typically 16 bytes
        tag = combined_data[16:32] # GCM tag is 16 bytes
        ciphertext = combined_data[32:]

        # Create a new AES cipher object with the same key and nonce
        cipher = AES.new(derived_key, AES.MODE_GCM, nonce=nonce)
        cipher.update(header)
        
        # Decrypt and verify. This will raise a ValueError if the tag is incorrect.
        decrypted_bytes = cipher.decrypt_and_verify(ciphertext, tag)
        
        return json.loads(decrypted_bytes.decode('utf-8'))
    except (ValueError, KeyError, IndexError, json.JSONDecodeError):
        # ValueError is raised by decrypt_and_verify on failure
        return None
      
