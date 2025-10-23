import asyncio
import os
from dotenv import load_dotenv
from database.connection import db
from database.operations import UserOperations

load_dotenv()

async def test_supabase():
    """Test Supabase connection and basic operations"""
    try:
        # Connect to Supabase
        await db.connect()
        
        # Test user creation
        test_user_id = 123456789  # Test Telegram ID
        user = await UserOperations.get_or_create_user(test_user_id)
        print(f"✅ User created/retrieved: {user.telegram_id}")
        
        # Test Drop ID creation
        from database.operations import DropIDOperations
        drop_id = await DropIDOperations.create_drop_id(test_user_id)
        print(f"✅ Drop ID created: {drop_id.id}")
        
        # Test retrieving Drop ID
        retrieved_drop = await DropIDOperations.get_drop_id(drop_id.id)
        print(f"✅ Drop ID retrieved: {retrieved_drop.id}")
        
        print("🎉 All Supabase tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(test_supabase())