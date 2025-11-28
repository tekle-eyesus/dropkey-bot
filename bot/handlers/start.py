from aiogram import Router, types
from aiogram.filters import Command
from database.operations import UserOperations
import html

start_router = Router()

@start_router.message(Command("start"))
async def start_command(message: types.Message):
    await UserOperations.get_or_create_user(message.from_user.id)

    welcome_text = (
    "<b>🤖 Welcome to DropKey</b>\n\n"
    "A privacy-focused bot for receiving files and messages <b>anonymously</b>.\n\n"
    "<b>How it works</b>\n"
    "• Create your Drop ID with /create_id\n"
    "• Share it with anyone\n"
    "• Receive files without revealing your identity\n"
    "• Check everything in /inbox\n\n"
    "<b>Commands</b>\n"
    "/create_id — New Drop ID\n"
    "/inbox — View your inbox\n"
    "/disable_id — Disable your Drop ID\n"
    "/enable_id — Enable your Drop ID\n\n"
    "Your privacy comes first — no usernames, no phone numbers, just secure sharing."
)



    await message.answer(welcome_text, parse_mode="HTML")
