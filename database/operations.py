from .connection import db
from .models import User, DropID, InboxItem
from datetime import datetime, timedelta
import secrets
import string
import logging

logger = logging.getLogger(__name__)

class UserOperations:
    @staticmethod
    async def get_or_create_user(telegram_id: int) -> User:
        """Get user or create if doesn't exist"""
        try:
            # Try to get existing user
            response = db.table('users').select('*').eq('telegram_id', telegram_id).execute()
            
            if response.data and len(response.data) > 0:
                # User exists
                user_data = response.data[0]
                return User(
                    telegram_id=user_data['telegram_id'],
                    pin_hash=user_data['pin_hash'],
                    created_at=datetime.fromisoformat(user_data['created_at'].replace('Z', '+00:00'))
                )
            else:
                # Create new user
                user_data = {
                    'telegram_id': telegram_id,
                    'created_at': datetime.utcnow().isoformat()
                }
                
                response = db.table('users').insert(user_data).execute()
                
                if response.data and len(response.data) > 0:
                    new_user = response.data[0]
                    return User(
                        telegram_id=new_user['telegram_id'],
                        pin_hash=new_user['pin_hash'],
                        created_at=datetime.fromisoformat(new_user['created_at'].replace('Z', '+00:00'))
                    )
                else:
                    raise Exception("Failed to create user")
                    
        except Exception as e:
            logger.error(f"Error in get_or_create_user: {e}")
            raise
    
    @staticmethod
    async def set_user_pin(telegram_id: int, pin_hash: str):
        """Set user PIN"""
        try:
            response = db.table('users').update({'pin_hash': pin_hash}).eq('telegram_id', telegram_id).execute()
            
            if not response.data:
                raise Exception("User not found")
                
        except Exception as e:
            logger.error(f"Error setting user PIN: {e}")
            raise

class DropIDOperations:
    @staticmethod
    def generate_drop_id(length: int = 8) -> str:
        """Generate a random Drop ID"""
        alphabet = string.ascii_lowercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    async def create_drop_id(owner_id: int, is_single_use: bool = False, 
                           expires_hours: int = None) -> DropID:
        """Create a new Drop ID"""
        try:
            drop_id = DropIDOperations.generate_drop_id()
            expires_at = None
            
            if expires_hours:
                expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
            
            drop_data = {
                'id': drop_id,
                'owner_id': owner_id,
                'is_single_use': is_single_use,
                'is_active': True,
                'expires_at': expires_at.isoformat() if expires_at else None,
                'created_at': datetime.utcnow().isoformat()
            }
            
            response = db.table('drop_ids').insert(drop_data).execute()
            
            if response.data and len(response.data) > 0:
                drop_data = response.data[0]
                return DropID(
                    id=drop_data['id'],
                    owner_id=drop_data['owner_id'],
                    is_active=drop_data['is_active'],
                    is_single_use=drop_data['is_single_use'],
                    expires_at=datetime.fromisoformat(drop_data['expires_at'].replace('Z', '+00:00')) if drop_data['expires_at'] else None,
                    created_at=datetime.fromisoformat(drop_data['created_at'].replace('Z', '+00:00'))
                )
            else:
                raise Exception("Failed to create Drop ID")
                
        except Exception as e:
            logger.error(f"Error creating Drop ID: {e}")
            raise
    
    @staticmethod
    async def get_drop_id(drop_id: str) -> DropID:
        """Get Drop ID by ID"""
        try:
            response = db.table('drop_ids').select('*').eq('id', drop_id).execute()
            
            if response.data and len(response.data) > 0:
                drop_data = response.data[0]
                return DropID(
                    id=drop_data['id'],
                    owner_id=drop_data['owner_id'],
                    is_active=drop_data['is_active'],
                    is_single_use=drop_data['is_single_use'],
                    expires_at=datetime.fromisoformat(drop_data['expires_at'].replace('Z', '+00:00')) if drop_data['expires_at'] else None,
                    created_at=datetime.fromisoformat(drop_data['created_at'].replace('Z', '+00:00'))
                )
            return None
            
        except Exception as e:
            logger.error(f"Error getting Drop ID: {e}")
            return None
    
    @staticmethod
    async def get_user_drop_ids(owner_id: int) -> list[DropID]:
        """Get all Drop IDs for a user"""
        try:
            response = db.table('drop_ids').select('*').eq('owner_id', owner_id).execute()
            
            drop_ids = []
            for drop_data in response.data:
                drop_ids.append(DropID(
                    id=drop_data['id'],
                    owner_id=drop_data['owner_id'],
                    is_active=drop_data['is_active'],
                    is_single_use=drop_data['is_single_use'],
                    expires_at=datetime.fromisoformat(drop_data['expires_at'].replace('Z', '+00:00')) if drop_data['expires_at'] else None,
                    created_at=datetime.fromisoformat(drop_data['created_at'].replace('Z', '+00:00'))
                ))
            
            return drop_ids
            
        except Exception as e:
            logger.error(f"Error getting user Drop IDs: {e}")
            return []

class InboxOperations:
    @staticmethod
    async def add_inbox_item(drop_id: str, sender_anon_id: str, file_id: str = None, 
                           file_type: str = None, message_text: str = None) -> InboxItem:
        """Add an item to inbox"""
        try:
            item_data = {
                'drop_id': drop_id,
                'sender_anon_id': sender_anon_id,
                'file_id': file_id,
                'file_type': file_type,
                'message_text': message_text,
                'created_at': datetime.utcnow().isoformat()
            }
            
            response = db.table('inbox_items').insert(item_data).execute()
            
            if response.data and len(response.data) > 0:
                item_data = response.data[0]
                return InboxItem(
                    id=item_data['id'],
                    drop_id=item_data['drop_id'],
                    sender_anon_id=item_data['sender_anon_id'],
                    file_id=item_data['file_id'],
                    file_type=item_data['file_type'],
                    message_text=item_data['message_text'],
                    created_at=datetime.fromisoformat(item_data['created_at'].replace('Z', '+00:00'))
                )
            else:
                raise Exception("Failed to add inbox item")
                
        except Exception as e:
            logger.error(f"Error adding inbox item: {e}")
            raise
    
    @staticmethod
    async def get_user_inbox(owner_id: int) -> list[InboxItem]:
        """Get all inbox items for a user"""
        try:
            # Join with drop_ids to get items for user's Drop IDs
            response = db.table('inbox_items')\
                .select('*, drop_ids!inner(owner_id)')\
                .eq('drop_ids.owner_id', owner_id)\
                .order('created_at', desc=True)\
                .execute()
            
            inbox_items = []
            for item_data in response.data:
                inbox_items.append(InboxItem(
                    id=item_data['id'],
                    drop_id=item_data['drop_id'],
                    sender_anon_id=item_data['sender_anon_id'],
                    file_id=item_data['file_id'],
                    file_type=item_data['file_type'],
                    message_text=item_data['message_text'],
                    created_at=datetime.fromisoformat(item_data['created_at'].replace('Z', '+00:00'))
                ))
            
            return inbox_items
            
        except Exception as e:
            logger.error(f"Error getting user inbox: {e}")
            return []