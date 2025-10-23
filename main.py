import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config import config
from database.connection import db
from bot.handlers.start import start_router
from bot.handlers.dropid import dropid_router
from bot.handlers.send import send_router
from bot.handlers.inbox import inbox_router
from bot.handlers.management import management_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_bot_commands(bot: Bot):
    """Set up bot commands menu"""
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="create_id", description="Create a new Drop ID"),
        BotCommand(command="send", description="Send message to Drop ID"),
        BotCommand(command="inbox", description="Check your inbox"),
        BotCommand(command="disable_id", description="Disable your Drop ID"),
        BotCommand(command="enable_id", description="Enable your Drop ID"),
        BotCommand(command="my_ids", description="View all your Drop IDs"),  # ← Add this
    ]
    await bot.set_my_commands(commands)

async def main():
    """Main function to start the bot"""
    try:
        # Validate environment variables
        config.validate()
        logger.info("✅ Environment variables validated")
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        return
    
    # Initialize bot and dispatcher
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    
    # Include routers
    dp.include_router(start_router)
    dp.include_router(dropid_router)
    dp.include_router(send_router)
    dp.include_router(inbox_router)
    dp.include_router(management_router)


    # Set up bot commands
    await setup_bot_commands(bot)
    
    try:
        # Connect to Supabase
        if config.SUPABASE_URL and config.SUPABASE_KEY:
            await db.connect()
        else:
            logger.warning("⚠️  Supabase credentials not configured - database features disabled")
        
        # Start polling
        logger.info("🤖 Bot is starting...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Bot stopped with error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())