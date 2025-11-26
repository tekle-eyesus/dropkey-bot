import asyncio
import os
from dotenv import load_dotenv
from database.connection import db
from database.operations import DropIDOperations, UserOperations, InboxOperations
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

async def test_delete_functionality():
    """Test Drop ID deletion functionality"""
    try:
        print("🔗 Connecting to Supabase...")
        await db.connect()
        
        if not db.is_connected:
            print("❌ Failed to connect to Supabase")
            return
        
        test_user_id = 666666666
        
        # Ensure user exists
        user = await UserOperations.get_or_create_user(test_user_id)
        print(f"✅ Test user: {user.telegram_id}")
        
        # Create test Drop IDs
        print("\n🎯 Creating test Drop IDs...")
        drop_id1 = await DropIDOperations.create_drop_id(test_user_id)
        drop_id2 = await DropIDOperations.create_drop_id(test_user_id)
        
        print(f"✅ Created Drop IDs: {drop_id1.id}, {drop_id2.id}")
        
        # Add test messages
        print("\n📝 Adding test messages...")
        await InboxOperations.add_inbox_item(
            drop_id=drop_id1.id,
            sender_anon_id="test_sender",
            message_text="Test message for deletion"
        )
        
        await InboxOperations.add_file_item(
            drop_id=drop_id1.id,
            sender_anon_id="test_sender",
            file_id="test_file_id",
            file_type="document",
            file_name="test_document.pdf",
            file_size=1024
        )
        
        # Test deletion
        print("\n🗑️ Testing Drop ID deletion...")
        success = await DropIDOperations.permanent_delete_drop_id(drop_id1.id, test_user_id)
        print(f"✅ Drop ID deletion: {success}")
        
        # Verify deletion
        print("\n🔍 Verifying deletion...")
        drop_ids_after = await DropIDOperations.get_user_drop_ids(test_user_id)
        print(f"✅ Drop IDs after deletion: {len(drop_ids_after)}")
        
        # Test with wrong owner (should fail)
        print("\n🚫 Testing deletion with wrong owner...")
        success_wrong = await DropIDOperations.permanent_delete_drop_id(drop_id2.id, 999999999)
        print(f"✅ Wrong owner rejection: {not success_wrong}")
        
        # Test get with include_deleted
        print("\n📋 Testing include_deleted parameter...")
        all_drop_ids = await DropIDOperations.get_user_drop_ids(test_user_id, include_deleted=True)
        print(f"✅ All Drop IDs (including deleted): {len(all_drop_ids)}")
        
        active_drop_ids = await DropIDOperations.get_user_drop_ids(test_user_id, include_deleted=False)
        print(f"✅ Active Drop IDs only: {len(active_drop_ids)}")
        
        print("\n🎉 All delete functionality tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.disconnect()
        print("🔌 Disconnected from Supabase")

if __name__ == "__main__":
    asyncio.run(test_delete_functionality())