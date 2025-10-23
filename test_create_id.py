import asyncio
import os
from dotenv import load_dotenv
from database.connection import db
from database.operations import DropIDOperations, UserOperations
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

async def test_drop_id_creation():
    """Test Drop ID creation and management"""
    try:
        print("🔗 Connecting to Supabase...")
        await db.connect()
        
        if not db.is_connected:
            print("❌ Failed to connect to Supabase")
            return
        
        test_user_id = 987654321  # Different test ID
        
        # Ensure user exists
        user = await UserOperations.get_or_create_user(test_user_id)
        print(f"✅ User: {user.telegram_id}")
        
        # Test basic Drop ID creation
        print("\n🎯 Testing basic Drop ID creation...")
        drop_id1 = await DropIDOperations.create_drop_id(test_user_id)
        print(f"✅ Basic Drop ID: {drop_id1.id}")
        print(f"   Active: {drop_id1.is_active}")
        print(f"   Single Use: {drop_id1.is_single_use}")
        print(f"   Expires: {drop_id1.expires_at}")
        
        # Test single-use Drop ID
        print("\n🔐 Testing single-use Drop ID...")
        drop_id2 = await DropIDOperations.create_drop_id(test_user_id, is_single_use=True)
        print(f"✅ Single-use Drop ID: {drop_id2.id}")
        print(f"   Single Use: {drop_id2.is_single_use}")
        
        # Test expiring Drop ID
        print("\n⏰ Testing expiring Drop ID...")
        drop_id3 = await DropIDOperations.create_drop_id(test_user_id, expires_hours=1)
        print(f"✅ Expiring Drop ID: {drop_id3.id}")
        print(f"   Expires at: {drop_id3.expires_at}")
        
        # Test listing user's Drop IDs
        print("\n📋 Testing Drop ID listing...")
        user_drop_ids = await DropIDOperations.get_user_drop_ids(test_user_id)
        print(f"✅ User has {len(user_drop_ids)} Drop ID(s)")
        
        for drop_id in user_drop_ids:
            status = "Active" if drop_id.is_active else "Inactive"
            if drop_id.is_expired():
                status = "Expired"
            print(f"   - {drop_id.id}: {status} (Single-use: {drop_id.is_single_use})")
        
        print("\n🎉 All Drop ID tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.disconnect()
        print("🔌 Disconnected from Supabase")

if __name__ == "__main__":
    asyncio.run(test_drop_id_creation())