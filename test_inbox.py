import asyncio
import os
from dotenv import load_dotenv
from database.connection import db
from database.operations import UserOperations, InboxOperations, DropIDOperations
from security.pin import PINManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

async def test_inbox_functionality():
    """Test inbox with PIN protection"""
    try:
        print("🔗 Connecting to Supabase...")
        await db.connect()
        
        if not db.is_connected:
            print("❌ Failed to connect to Supabase")
            return
        
        test_user_id = 333333333
        
        # Ensure user exists
        user = await UserOperations.get_or_create_user(test_user_id)
        print(f"✅ Test user: {user.telegram_id}")
        
        # Test PIN operations
        print("\n🛡️ Testing PIN operations...")
        
        # Test PIN hashing and verification
        test_pin = "1234"
        pin_hash = PINManager.hash_pin(test_pin)
        print(f"✅ PIN hashed successfully")
        
        verify_result = PINManager.verify_pin(test_pin, pin_hash)
        print(f"✅ PIN verification: {verify_result}")
        
        verify_wrong = PINManager.verify_pin("9999", pin_hash)
        print(f"✅ Wrong PIN rejection: {not verify_wrong}")
        
        # Test PIN format validation
        valid_pins = ["1234", "12345", "123456"]
        invalid_pins = ["123", "1234567", "abcd", "12a4"]
        
        for pin in valid_pins:
            is_valid = PINManager.validate_pin_format(pin)
            print(f"✅ Valid PIN '{pin}': {is_valid}")
        
        for pin in invalid_pins:
            is_valid = PINManager.validate_pin_format(pin)
            print(f"✅ Invalid PIN '{pin}' rejected: {not is_valid}")
        
        # Test setting user PIN
        await UserOperations.set_user_pin(test_user_id, pin_hash)
        print("✅ User PIN set in database")
        
        # Test checking if user has PIN
        has_pin = await UserOperations.user_has_pin(test_user_id)
        print(f"✅ User has PIN: {has_pin}")
        
        # Test getting PIN hash
        stored_hash = await UserOperations.get_user_pin_hash(test_user_id)
        print(f"✅ PIN hash retrieved: {stored_hash is not None}")
        
        # Create test Drop ID and messages
        print("\n📬 Testing inbox operations...")
        drop_id = await DropIDOperations.create_drop_id(test_user_id)
        
        # Add test messages to inbox
        test_messages = [
            "Hello! This is the first test message.",
            "Second message with some content.",
            "Third message for testing inbox display."
        ]
        
        for i, msg in enumerate(test_messages):
            await InboxOperations.add_inbox_item(
                drop_id=drop_id.id,
                sender_anon_id=f"test{i}",
                message_text=msg
            )
        
        print("✅ Test messages added to inbox")
        
        # Test retrieving inbox
        inbox_items = await InboxOperations.get_user_inbox(test_user_id)
        print(f"✅ Inbox items retrieved: {len(inbox_items)}")
        
        for item in inbox_items:
            print(f"   - From: {item.sender_anon_id}, Message: {item.message_text[:30]}...")
        
        # Test clearing inbox
        await InboxOperations.clear_user_inbox(test_user_id)
        inbox_after_clear = await InboxOperations.get_user_inbox(test_user_id)
        print(f"✅ Inbox cleared: {len(inbox_after_clear)} items remaining")
        
        print("\n🎉 All inbox functionality tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.disconnect()
        print("🔌 Disconnected from Supabase")

if __name__ == "__main__":
    asyncio.run(test_inbox_functionality())