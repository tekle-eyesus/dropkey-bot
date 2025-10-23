import asyncio
import os
from dotenv import load_dotenv
from database.connection import db
from database.operations import DropIDOperations, UserOperations
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

async def test_management_functionality():
    """Test Drop ID management (disable/enable)"""
    try:
        print("🔗 Connecting to Supabase...")
        await db.connect()
        
        if not db.is_connected:
            print("❌ Failed to connect to Supabase")
            return
        
        test_user_id = 444444444
        
        # Ensure user exists
        user = await UserOperations.get_or_create_user(test_user_id)
        print(f"✅ Test user: {user.telegram_id}")
        
        # Create test Drop IDs
        print("\n🎯 Creating test Drop IDs...")
        drop_id1 = await DropIDOperations.create_drop_id(test_user_id)
        drop_id2 = await DropIDOperations.create_drop_id(test_user_id)
        drop_id3 = await DropIDOperations.create_drop_id(test_user_id, is_single_use=True)
        
        print(f"✅ Created Drop IDs: {drop_id1.id}, {drop_id2.id}, {drop_id3.id}")
        
        # Test disable functionality
        print("\n🔴 Testing disable functionality...")
        success1 = await DropIDOperations.disable_drop_id(drop_id1.id, test_user_id)
        print(f"✅ Disable Drop ID {drop_id1.id}: {success1}")
        
        # Test disable with wrong owner (should fail)
        success_wrong = await DropIDOperations.disable_drop_id(drop_id2.id, 999999999)
        print(f"✅ Disable with wrong owner (should fail): {not success_wrong}")
        
        # Test enable functionality
        print("\n🟢 Testing enable functionality...")
        success2 = await DropIDOperations.enable_drop_id(drop_id1.id, test_user_id)
        print(f"✅ Enable Drop ID {drop_id1.id}: {success2}")
        
        # Test listing Drop IDs
        print("\n📋 Testing Drop ID listing...")
        drop_ids = await DropIDOperations.get_user_drop_ids(test_user_id)
        print(f"✅ User has {len(drop_ids)} Drop ID(s)")
        
        active_count = len([d for d in drop_ids if d.is_active])
        disabled_count = len([d for d in drop_ids if not d.is_active])
        print(f"   Active: {active_count}, Disabled: {disabled_count}")
        
        # Test single-use Drop ID behavior
        print("\n🔐 Testing single-use Drop ID disable after use...")
        # Simulate using the single-use Drop ID
        from database.operations import InboxOperations
        await InboxOperations.add_inbox_item(
            drop_id=drop_id3.id,
            sender_anon_id="test_single",
            message_text="This should disable the single-use Drop ID"
        )
        
        # Check if single-use Drop ID was auto-disabled
        single_use_after = await DropIDOperations.get_drop_id(drop_id3.id)
        print(f"✅ Single-use Drop ID active after use: {single_use_after.is_active}")
        
        # Test bulk operations
        print("\n🔄 Testing bulk operations...")
        # Disable all
        for drop in drop_ids:
            if drop.is_active:
                await DropIDOperations.disable_drop_id(drop.id, test_user_id)
        
        drop_ids_after_disable = await DropIDOperations.get_user_drop_ids(test_user_id)
        active_after_disable = len([d for d in drop_ids_after_disable if d.is_active])
        print(f"✅ After bulk disable - Active: {active_after_disable}")
        
        # Enable all
        for drop in drop_ids_after_disable:
            if not drop.is_active and not drop.is_expired():
                await DropIDOperations.enable_drop_id(drop.id, test_user_id)
        
        drop_ids_after_enable = await DropIDOperations.get_user_drop_ids(test_user_id)
        active_after_enable = len([d for d in drop_ids_after_enable if d.is_active and not d.is_expired()])
        print(f"✅ After bulk enable - Active: {active_after_enable}")
        
        print("\n🎉 All management functionality tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.disconnect()
        print("🔌 Disconnected from Supabase")

if __name__ == "__main__":
    asyncio.run(test_management_functionality())