from aiogram import Router, types
from aiogram.filters import Command
import logging

logger = logging.getLogger(__name__)

fallback_router = Router()

@fallback_router.message()
async def fallback_handler(message: types.Message):
    """Handle unprocessed messages"""
    logger.info(f"Fallback handler: User {message.from_user.id} sent: {message.text}")
    
    if message.text and message.text.startswith('/'):
        await message.answer(
            "❌ Unknown command or command not processed.\n\n"
            "Available commands:\n"
            "/start - Start the bot\n"
            "/create_id - Create a Drop ID\n"
            "/send - Send message/file\n"
            "/inbox - Check your inbox\n"
            "/disable_id - Disable Drop IDs\n"
            "/enable_id - Enable Drop IDs\n"
            "/my_ids - View your Drop IDs",
            parse_mode=None
        )