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
        """Set user PIN hash"""
        try:
            response = db.table('users').update({'pin_hash': pin_hash}).eq('telegram_id', telegram_id).execute()
            
            if not response.data:
                raise Exception("User not found")
                
        except Exception as e:
            logger.error(f"Error setting user PIN: {e}")
            raise

    @staticmethod
    async def get_user_pin_hash(telegram_id: int) -> str:
        """Get user's PIN hash"""
        try:
            response = db.table('users').select('pin_hash').eq('telegram_id', telegram_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]['pin_hash']
            return None
            
        except Exception as e:
            logger.error(f"Error getting user PIN hash: {e}")
            return None

    @staticmethod
    async def user_has_pin(telegram_id: int) -> bool:
        """Check if user has a PIN set"""
        pin_hash = await UserOperations.get_user_pin_hash(telegram_id)
        return pin_hash is not None

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
            response = db.table('drop_ids')\
                .select('*')\
                .eq('owner_id', owner_id)\
                .order('created_at', desc=True)\
                .execute()
            
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

    @staticmethod
    async def disable_drop_id(drop_id: str, owner_id: int) -> bool:
        """Disable a Drop ID (verify ownership)"""
        try:
            # First verify ownership
            response = db.table('drop_ids')\
                .select('*')\
                .eq('id', drop_id)\
                .eq('owner_id', owner_id)\
                .execute()
            
            if not response.data or len(response.data) == 0:
                return False
            
            # Disable the Drop ID
            update_response = db.table('drop_ids')\
                .update({'is_active': False})\
                .eq('id', drop_id)\
                .eq('owner_id', owner_id)\
                .execute()
            
            return update_response.data is not None
            
        except Exception as e:
            logger.error(f"Error disabling Drop ID: {e}")
            return False

    @staticmethod
    async def enable_drop_id(drop_id: str, owner_id: int) -> bool:
        """Enable a Drop ID (verify ownership and check expiration)"""
        try:
            # First verify ownership and check if expired
            response = db.table('drop_ids')\
                .select('*')\
                .eq('id', drop_id)\
                .eq('owner_id', owner_id)\
                .execute()
            
            if not response.data or len(response.data) == 0:
                return False
            
            drop_data = response.data[0]
            
            # Check if expired
            if drop_data['expires_at']:
                from datetime import datetime
                expires_at = datetime.fromisoformat(drop_data['expires_at'].replace('Z', '+00:00'))
                if datetime.utcnow() > expires_at:
                    return False  # Cannot enable expired Drop IDs
            
            # Enable the Drop ID
            update_response = db.table('drop_ids')\
                .update({'is_active': True})\
                .eq('id', drop_id)\
                .eq('owner_id', owner_id)\
                .execute()
            
            return update_response.data is not None
            
        except Exception as e:
            logger.error(f"Error enabling Drop ID: {e}")
            return False

    @staticmethod
    async def delete_drop_id(drop_id: str, owner_id: int) -> bool:
        """Delete a Drop ID and its associated inbox items (soft delete)"""
        try:
            # First verify ownership
            response = db.table('drop_ids')\
                .select('*')\
                .eq('id', drop_id)\
                .eq('owner_id', owner_id)\
                .execute()
            
            if not response.data or len(response.data) == 0:
                return False
            
            # Soft delete the Drop ID
            update_response = db.table('drop_ids')\
                .update({'deleted_at': datetime.utcnow().isoformat()})\
                .eq('id', drop_id)\
                .eq('owner_id', owner_id)\
                .execute()
            
            # Also soft delete associated inbox items
            if update_response.data:
                await db.table('inbox_items')\
                    .update({'deleted_at': datetime.utcnow().isoformat()})\
                    .eq('drop_id', drop_id)\
                    .execute()
            
            return update_response.data is not None
            
        except Exception as e:
            logger.error(f"Error deleting Drop ID: {e}")
            return False

    @staticmethod
    async def permanent_delete_drop_id(drop_id: str, owner_id: int) -> bool:
        """Permanently delete a Drop ID and its associated inbox items"""
        try:
            # First verify ownership
            response = db.table('drop_ids')\
                .select('*')\
                .eq('id', drop_id)\
                .eq('owner_id', owner_id)\
                .execute()
            
            if not response.data or len(response.data) == 0:
                return False
            
            # Delete associated inbox items first (due to foreign key constraint)
            delete_inbox_response = db.table('inbox_items')\
                .delete()\
                .eq('drop_id', drop_id)\
                .execute()
            
            # Then delete the Drop ID
            delete_response = db.table('drop_ids')\
                .delete()\
                .eq('id', drop_id)\
                .eq('owner_id', owner_id)\
                .execute()
            
            return delete_response.data is not None
            
        except Exception as e:
            logger.error(f"Error permanently deleting Drop ID: {e}")
            return False

    @staticmethod
    async def get_user_drop_ids(owner_id: int, include_deleted: bool = False) -> list[DropID]:
        """Get all Drop IDs for a user, optionally including deleted ones"""
        try:
            query = db.table('drop_ids')\
                .select('*')\
                .eq('owner_id', owner_id)\
                .order('created_at', desc=True)
            
            if not include_deleted:
                query = query.is_('deleted_at', 'null')
            
            response = query.execute()
            
            drop_ids = []
            for drop_data in response.data:
                drop_ids.append(DropID(
                    id=drop_data['id'],
                    owner_id=drop_data['owner_id'],
                    is_active=drop_data['is_active'],
                    is_single_use=drop_data['is_single_use'],
                    expires_at=datetime.fromisoformat(drop_data['expires_at'].replace('Z', '+00:00')) if drop_data['expires_at'] else None,
                    created_at=datetime.fromisoformat(drop_data['created_at'].replace('Z', '+00:00')),
                    deleted_at=datetime.fromisoformat(drop_data['deleted_at'].replace('Z', '+00:00')) if drop_data['deleted_at'] else None
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
            # First get user's active Drop IDs
            user_drop_ids = await DropIDOperations.get_user_drop_ids(owner_id)
            drop_id_list = [drop.id for drop in user_drop_ids]
            
            if not drop_id_list:
                return []
            
            # Get inbox items for these Drop IDs
            response = db.table('inbox_items')\
                .select('*')\
                .in_('drop_id', drop_id_list)\
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
    
    @staticmethod
    async def clear_user_inbox(owner_id: int):
        """Clear all inbox items for a user"""
        try:
            # Get user's Drop IDs
            user_drop_ids = await DropIDOperations.get_user_drop_ids(owner_id)
            drop_id_list = [drop.id for drop in user_drop_ids]
            
            if drop_id_list:
                # Delete inbox items for these Drop IDs
                await db.table('inbox_items')\
                    .delete()\
                    .in_('drop_id', drop_id_list)\
                    .execute()
                    
        except Exception as e:
            logger.error(f"Error clearing user inbox: {e}")
            raise

    @staticmethod
    async def add_file_item(drop_id: str, sender_anon_id: str, file_id: str, 
                        file_type: str, file_name: str = None, 
                        file_size: int = None, mime_type: str = None,
                        message_text: str = None) -> InboxItem:
        """Add a file item to inbox with metadata"""
        try:
            item_data = {
                'drop_id': drop_id,
                'sender_anon_id': sender_anon_id,
                'file_id': file_id,
                'file_type': file_type,
                'file_name': file_name,
                'file_size': file_size,
                'mime_type': mime_type,
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
                    file_name=item_data['file_name'],
                    file_size=item_data['file_size'],
                    mime_type=item_data['mime_type'],
                    created_at=datetime.fromisoformat(item_data['created_at'].replace('Z', '+00:00'))
                )
            else:
                raise Exception("Failed to add file item")
                
        except Exception as e:
            logger.error(f"Error adding file item: {e}")
            raise