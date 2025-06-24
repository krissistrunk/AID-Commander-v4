#!/usr/bin/env python3
"""
Encryption utilities for AID Commander v4.0
"""

import os
import base64
import logging
from typing import Union, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class EncryptionManager:
    """Manages encryption operations for sensitive data"""
    
    def __init__(self, password: Optional[str] = None):
        self.password = password or os.getenv('SECRET_KEY', 'default_secret_key')
        self._fernet = None
    
    def _get_fernet(self) -> Fernet:
        """Get or create Fernet instance for encryption"""
        if self._fernet is None:
            # Generate salt (in production, this should be stored securely)
            salt = b'salt_for_aid_commander_v4'  # Fixed salt for consistency
            
            # Derive key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
            self._fernet = Fernet(key)
        
        return self._fernet
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        try:
            fernet = self._get_fernet()
            encrypted_data = fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        try:
            fernet = self._get_fernet()
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

# Global encryption manager instance
_encryption_manager = None

def get_encryption_manager() -> EncryptionManager:
    """Get global encryption manager instance"""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager

def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data using global encryption manager"""
    return get_encryption_manager().encrypt(data)

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data using global encryption manager"""
    return get_encryption_manager().decrypt(encrypted_data)

def generate_encryption_key() -> str:
    """Generate a new encryption key"""
    return Fernet.generate_key().decode()