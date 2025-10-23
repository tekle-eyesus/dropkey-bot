from aiogram import Router, types
from aiogram.filters import Command
from database.operations import UserOperations

start_router = Router()

@start_router.message(Command("start"))
async def start_command(message: types.Message):
    """Handle /start command"""
    user = await UserOperations.get_or_create_user(message.from_user.id)
    
    welcome_text = """
🤖 **Welcome to DropKey!**

A privacy-focused file sharing bot that lets you receive files anonymously.

**How it works:**
1. Create a Drop ID using /create_id
2. Share your Drop ID with others
3. Receive files/messages without revealing your identity
4. Access your inbox with /inbox

**Available commands:**
/create_id - Generate a new Drop ID
/inbox - Check your received files
/disable_id - Temporarily disable your Drop ID
/enable_id - Reactivate your Drop ID

Your privacy is our priority. No usernames, no phone numbers, just secure sharing.
    """
    
    await message.answer(welcome_text, parse_mode="Markdown")