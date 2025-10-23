import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot

load_dotenv()

async def test_bot():
    """Test if the bot token works"""
    bot_token = os.getenv("BOT_TOKEN")
    
    if not bot_token:
        print("❌ BOT_TOKEN not found in .env file")
        return
    
    try:
        bot = Bot(token=bot_token)
        bot_info = await bot.get_me()
        print(f"✅ Bot connected successfully!")
        print(f"🤖 Bot Name: {bot_info.first_name}")
        print(f"🔗 Username: @{bot_info.username}")
        print(f"🆔 Bot ID: {bot_info.id}")
        
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(test_bot())