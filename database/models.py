from datetime import datetime, timedelta

class User:
    def __init__(self, telegram_id: int, pin_hash: str = None, created_at: datetime = None):
        self.telegram_id = telegram_id
        self.pin_hash = pin_hash
        self.created_at = created_at or datetime.utcnow()

class DropID:
    def __init__(self, id: str, owner_id: int, is_active: bool = True, 
                 is_single_use: bool = False, expires_at: datetime = None,
                 created_at: datetime = None, deleted_at: datetime = None):
        self.id = id
        self.owner_id = owner_id
        self.is_active = is_active
        self.is_single_use = is_single_use
        self.expires_at = expires_at
        self.created_at = created_at or datetime.utcnow()
        self.deleted_at = deleted_at
    
    def is_expired(self) -> bool:
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

class InboxItem:
    def __init__(self, id: int, drop_id: str, sender_anon_id: str, 
                 file_id: str = None, file_type: str = None, 
                 message_text: str = None, is_encrypted: bool = False,
                 file_name: str = None, file_size: int = None, mime_type: str = None,
                 created_at: datetime = None, deleted_at: datetime = None):
        self.id = id
        self.drop_id = drop_id
        self.sender_anon_id = sender_anon_id
        self.file_id = file_id
        self.file_type = file_type
        self.message_text = message_text
        self.is_encrypted = is_encrypted
        self.file_name = file_name
        self.file_size = file_size
        self.mime_type = mime_type
        self.created_at = created_at or datetime.utcnow()
        self.deleted_at = deleted_at
    
    def is_deleted(self) -> bool:
        return self.deleted_at is not None