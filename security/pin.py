import bcrypt
import logging

logger = logging.getLogger(__name__)

class PINManager:
    @staticmethod
    def hash_pin(pin: str) -> str:
        """Hash a PIN using bcrypt"""
        try:
            # Validate PIN format (4-6 digits)
            if not pin.isdigit() or not (4 <= len(pin) <= 6):
                raise ValueError("PIN must be 4-6 digits")
            
            salt = bcrypt.gensalt()
            pin_hash = bcrypt.hashpw(pin.encode('utf-8'), salt)
            return pin_hash.decode('utf-8')
        except Exception as e:
            logger.error(f"Error hashing PIN: {e}")
            raise
    
    @staticmethod
    def verify_pin(pin: str, pin_hash: str) -> bool:
        """Verify a PIN against its hash"""
        try:
            if not pin or not pin_hash:
                return False
            return bcrypt.checkpw(pin.encode('utf-8'), pin_hash.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error verifying PIN: {e}")
            return False
    
    @staticmethod
    def validate_pin_format(pin: str) -> bool:
        """Validate PIN format (4-6 digits)"""
        return pin.isdigit() and 4 <= len(pin) <= 6