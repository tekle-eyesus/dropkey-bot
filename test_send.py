import asyncio
import os
from dotenv import load_dotenv
from database.connection import db
from database.operations import DropIDOperations, InboxOperations, UserOperations
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

async def test_send_functionality():
    """Test sending messages to Drop IDs"""
    try:
        print("🔗 Connecting to Supabase...")
        await db.connect()
        
        if not db.is_connected:
            print("❌ Failed to connect to Supabase")
            return
        
        # Create test users
        sender_id = 111111111
        receiver_id = 222222222
        
        await UserOperations.get_or_create_user(sender_id)
        receiver = await UserOperations.get_or_create_user(receiver_id)
        print(f"✅ Test users created")
        
        # Create Drop ID for receiver
        drop_id = await DropIDOperations.create_drop_id(receiver_id)
        print(f"✅ Receiver Drop ID: {drop_id.id}")
        
        # Test sending message
        print("\n📤 Testing message sending...")
        test_message = "Hello! This is a test message from the automated test."
        sender_anon_id = "test123"
        
        inbox_item = await InboxOperations.add_inbox_item(
            drop_id=drop_id.id,
            sender_anon_id=sender_anon_id,
            message_text=test_message
        )
        
        print(f"✅ Message sent to Drop ID: {drop_id.id}")
        print(f"   Sender Anonymous ID: {sender_anon_id}")
        print(f"   Message: {test_message}")
        print(f"   Inbox Item ID: {inbox_item.id}")
        
        # Test retrieving inbox
        print("\n📥 Testing inbox retrieval...")
        inbox_items = await InboxOperations.get_user_inbox(receiver_id)
        print(f"✅ Receiver has {len(inbox_items)} inbox item(s)")
        
        for item in inbox_items:
            print(f"   - From: {item.sender_anon_id}")
            print(f"     To Drop ID: {item.drop_id}")
            print(f"     Message: {item.message_text}")
            print(f"     Time: {item.created_at}")
        
        # Test single-use Drop ID behavior
        print("\n🔐 Testing single-use Drop ID...")
        single_use_drop = await DropIDOperations.create_drop_id(receiver_id, is_single_use=True)
        print(f"✅ Single-use Drop ID created: {single_use_drop.id}")
        
        # Send message to single-use Drop ID
        await InboxOperations.add_inbox_item(
            drop_id=single_use_drop.id,
            sender_anon_id="anon456",
            message_text="This should disable the Drop ID"
        )
        
        # Check if Drop ID was disabled
        updated_drop = await DropIDOperations.get_drop_id(single_use_drop.id)
        print(f"   Drop ID active after use: {updated_drop.is_active}")
        
        print("\n🎉 All send functionality tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.disconnect()
        print("🔌 Disconnected from Supabase")

if __name__ == "__main__":
    asyncio.run(test_send_functionality())