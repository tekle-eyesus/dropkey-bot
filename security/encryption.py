import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from config import config

class EncryptionManager:
    def __init__(self):
        # Use the key from environment
        key = config.ENCRYPTION_KEY.encode()
        
        # Ensure the key is proper Fernet key (32 url-safe base64-encoded bytes)
        if len(key) != 44:  # Fernet key length
            # Derive a proper key if needed
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'dropkey_salt',  # In production, use a random salt
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(key))
        
        self.cipher_suite = Fernet(key)
    
    def encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data"""
        return self.cipher_suite.encrypt(data)
    
    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Decrypt data"""
        return self.cipher_suite.decrypt(encrypted_data)
    
    def encrypt_text(self, text: str) -> str:
        """Encrypt text and return base64 string"""
        encrypted = self.encrypt_data(text.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_text(self, encrypted_text: str) -> str:
        """Decrypt base64 encrypted text"""
        encrypted_data = base64.urlsafe_b64decode(encrypted_text.encode())
        decrypted = self.decrypt_data(encrypted_data)
        return decrypted.decode()

# Global instance
encryption_manager = EncryptionManager()