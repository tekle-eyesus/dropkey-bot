from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandObject 

from database.operations import UserOperations, InboxOperations
from security.pin import PINManager
from config import config
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

inbox_router = Router()

class InboxStates(StatesGroup):
    """States for inbox PIN verification"""
    waiting_for_pin = State()
    setting_new_pin = State()
    confirming_new_pin = State()

def text_filter(text: str):
    """Custom text filter for callback queries"""
    async def func(callback_query: types.CallbackQuery):
        return callback_query.data == text
    return func

@inbox_router.message(Command("inbox"))
async def inbox_command(message: types.Message, state: FSMContext):
    """Handle /inbox command - check if PIN is set and verify"""
    try:
        user_id = message.from_user.id
        
        # Check if user has PIN set
        has_pin = await UserOperations.user_has_pin(user_id)
        
        if not has_pin:
            # No PIN set - prompt to create one
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🛡️ Set PIN Now", callback_data="set_pin")],
                    [InlineKeyboardButton(text="🚫 Skip for Now", callback_data="skip_pin")]
                ]
            )
            
            await message.answer(
                "🔒 **PIN Protection**\n\n"
                "You haven't set a PIN yet. For security, we recommend setting a PIN "
                "to protect your inbox from unauthorized access.\n\n"
                "**PIN Features:**\n"
                "• 4-6 digits only\n"
                "• Required to view your inbox\n"
                "• Change anytime with /inbox",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return
        
        # PIN is set - prompt for verification
        await message.answer(
            "🔐 **PIN Required**\n\n"
            "Please enter your 4-6 digit PIN to access your inbox:",
            parse_mode="Markdown"
        )
        await state.set_state(InboxStates.waiting_for_pin)
        await state.update_data(user_id=user_id)
        
    except Exception as e:
        logger.error(f"Error in inbox command: {e}")
        await message.answer("❌ Failed to access inbox. Please try again.")

@inbox_router.callback_query(text_filter("set_pin"))
async def start_set_pin(callback_query: types.CallbackQuery, state: FSMContext):
    """Start PIN setup process"""
    await callback_query.message.edit_text(
        "🛡️ **Set Your PIN**\n\n"
        "Please enter a 4-6 digit PIN for inbox protection:",
        parse_mode="Markdown"
    )
    await state.set_state(InboxStates.setting_new_pin)
    await state.update_data(user_id=callback_query.from_user.id)
    await callback_query.answer()

@inbox_router.callback_query(text_filter("skip_pin"))
async def skip_pin_setup(callback_query: types.CallbackQuery):
    """Skip PIN setup and show inbox directly"""
    try:
        user_id = callback_query.from_user.id
        await show_inbox_contents(callback_query.message, user_id)
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error showing inbox without PIN: {e}")
        await callback_query.message.edit_text("❌ Failed to access inbox.")

@inbox_router.message(InboxStates.waiting_for_pin)
async def verify_pin_and_show_inbox(message: types.Message, state: FSMContext):
    """Verify PIN and show inbox if correct"""
    try:
        user_id = message.from_user.id
        pin_attempt = message.text.strip()
        
        # Get stored PIN hash
        pin_hash = await UserOperations.get_user_pin_hash(user_id)
        
        if not pin_hash:
            await message.answer("❌ PIN not found. Please set a new PIN using /inbox")
            await state.clear()
            return
        
        # Verify PIN
        if PINManager.verify_pin(pin_attempt, pin_hash):
            await message.answer("✅ PIN verified! Accessing your inbox...")
            await show_inbox_contents(message, user_id)
            await state.clear()
        else:
            # Wrong PIN
            data = await state.get_data()
            wrong_attempts = data.get('wrong_attempts', 0) + 1
            await state.update_data(wrong_attempts=wrong_attempts)
            
            if wrong_attempts >= 3:
                await message.answer(
                    "🚫 **Too many failed attempts!**\n\n"
                    "For security reasons, please wait a few minutes before trying again.",
                    parse_mode="Markdown"
                )
                await state.clear()
            else:
                remaining_attempts = 3 - wrong_attempts
                await message.answer(
                    f"❌ **Incorrect PIN!**\n\n"
                    f"You have {remaining_attempts} attempt{'s' if remaining_attempts > 1 else ''} remaining.\n"
                    f"Please enter your PIN again:",
                    parse_mode="Markdown"
                )
                
    except Exception as e:
        logger.error(f"Error verifying PIN: {e}")
        await message.answer("❌ Failed to verify PIN. Please try again.")
        await state.clear()

@inbox_router.message(InboxStates.setting_new_pin)
async def set_new_pin(message: types.Message, state: FSMContext):
    """Set new PIN - first step"""
    try:
        pin = message.text.strip()
        
        # Validate PIN format
        if not PINManager.validate_pin_format(pin):
            await message.answer(
                "❌ **Invalid PIN format!**\n\n"
                "PIN must be 4-6 digits only.\n"
                "Please enter a valid PIN:",
                parse_mode="Markdown"
            )
            return
        
        # Store PIN in state and ask for confirmation
        await state.update_data(new_pin=pin)
        await message.answer(
            "🔐 **Confirm Your PIN**\n\n"
            "Please enter the same PIN again to confirm:",
            parse_mode="Markdown"
        )
        await state.set_state(InboxStates.confirming_new_pin)
        
    except Exception as e:
        logger.error(f"Error setting new PIN: {e}")
        await message.answer("❌ Failed to set PIN. Please try again.")
        await state.clear()

@inbox_router.message(InboxStates.confirming_new_pin)
async def confirm_new_pin(message: types.Message, state: FSMContext):
    """Confirm and save new PIN"""
    try:
        data = await state.get_data()
        user_id = data.get('user_id')
        original_pin = data.get('new_pin')
        confirmation_pin = message.text.strip()
        
        if not user_id:
            await message.answer("❌ Session expired. Please start over with /inbox")
            await state.clear()
            return
        
        # Check if PINs match
        if original_pin != confirmation_pin:
            await message.answer(
                "❌ **PINs don't match!**\n\n"
                "Please start over with /inbox to set a new PIN.",
                parse_mode="Markdown"
            )
            await state.clear()
            return
        
        # Hash and save PIN
        pin_hash = PINManager.hash_pin(original_pin)
        await UserOperations.set_user_pin(user_id, pin_hash)
        
        await message.answer(
            "✅ **PIN set successfully!**\n\n"
            "Your inbox is now protected. Use /inbox to access your messages.",
            parse_mode="Markdown"
        )
        await state.clear()
        
        # Show inbox after PIN setup
        await show_inbox_contents(message, user_id)
        
    except Exception as e:
        logger.error(f"Error confirming PIN: {e}")
        await message.answer("❌ Failed to set PIN. Please try again.")
        await state.clear()

async def show_inbox_contents(message: types.Message, user_id: int):
    """Display user's inbox contents"""
    try:
        inbox_items = await InboxOperations.get_user_inbox(user_id)
        
        if not inbox_items:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🆕 Create Drop ID", callback_data="create_from_inbox")],
                    [InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh_inbox")]
                ]
            )
            
            await message.answer(
                "📭 **Your Inbox is Empty**\n\n"
                "You haven't received any messages yet.\n\n"
                "**To receive messages:**\n"
                "1. Create a Drop ID with /create_id\n"
                "2. Share it with others\n"
                "3. They can send you messages with /send YOUR_DROP_ID",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return
        
        # Group items by date
        from collections import defaultdict
        items_by_date = defaultdict(list)
        
        for item in inbox_items:
            date_str = item.created_at.strftime("%Y-%m-%d")
            items_by_date[date_str].append(item)
        
        # Create inbox message
        response_text = "📬 **Your Inbox**\n\n"
        
        for date_str, items in sorted(items_by_date.items(), reverse=True):
            response_text += f"**📅 {date_str}**\n"
            
            for item in items:
                time_str = item.created_at.strftime("%H:%M")
                
                if item.message_text:
                    # Truncate long messages
                    message_preview = item.message_text[:50] + "..." if len(item.message_text) > 50 else item.message_text
                    response_text += f"• `{time_str}` 👤 `{item.sender_anon_id}` → `{item.drop_id}`: {message_preview}\n"
                elif item.file_type:
                    response_text += f"• `{time_str}` 👤 `{item.sender_anon_id}` → `{item.drop_id}`: 📎 {item.file_type} file\n"
            
            response_text += "\n"
        
        # Add management options
        response_text += f"**Total Messages:** {len(inbox_items)}\n\n"
        response_text += "💡 Use /create_id to generate new Drop IDs\n"
        response_text += "🔧 Use /disable_id to manage your Drop IDs"
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🆕 Create Drop ID", callback_data="create_from_inbox")],
                [
                    InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh_inbox"),
                    InlineKeyboardButton(text="🗑️ Clear All", callback_data="clear_inbox")
                ]
            ]
        )
        
        await message.answer(response_text, reply_markup=keyboard, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error showing inbox contents: {e}")
        await message.answer("❌ Failed to load inbox contents. Please try again.")

@inbox_router.callback_query(text_filter("refresh_inbox"))
async def refresh_inbox(callback_query: types.CallbackQuery):
    """Refresh inbox contents"""
    try:
        user_id = callback_query.from_user.id
        await callback_query.message.edit_text("🔄 Refreshing inbox...")
        await show_inbox_contents(callback_query.message, user_id)
        await callback_query.answer("Inbox refreshed!")
    except Exception as e:
        logger.error(f"Error refreshing inbox: {e}")
        await callback_query.answer("❌ Failed to refresh inbox", show_alert=True)

@inbox_router.callback_query(text_filter("create_from_inbox"))
async def create_from_inbox(callback_query: types.CallbackQuery):
    """Create Drop ID from inbox"""
    from database.operations import DropIDOperations
    try:
        user_id = callback_query.from_user.id
        drop_id = await DropIDOperations.create_drop_id(user_id)
        
        await callback_query.message.edit_text(
            f"🎯 **Drop ID Created from Inbox!**\n\n"
            f"**Your new Drop ID:** `{drop_id.id}`\n\n"
            f"Share this ID to start receiving messages!",
            parse_mode="Markdown"
        )
        await callback_query.answer("Drop ID created!")
    except Exception as e:
        logger.error(f"Error creating Drop ID from inbox: {e}")
        await callback_query.answer("❌ Failed to create Drop ID", show_alert=True)

@inbox_router.callback_query(text_filter("clear_inbox"))
async def clear_inbox_prompt(callback_query: types.CallbackQuery):
    """Prompt for inbox clearance confirmation"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Yes, Clear Everything", callback_data="confirm_clear_inbox")],
            [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_clear_inbox")]
        ]
    )
    
    await callback_query.message.edit_text(
        "🚨 **Clear Entire Inbox?**\n\n"
        "This will permanently delete all your received messages.\n"
        "**This action cannot be undone!**\n\n"
        "Are you sure you want to clear your entire inbox?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback_query.answer()

@inbox_router.callback_query(text_filter("confirm_clear_inbox"))
async def confirm_clear_inbox(callback_query: types.CallbackQuery):
    """Clear user's entire inbox"""
    try:
        user_id = callback_query.from_user.id
        await InboxOperations.clear_user_inbox(user_id)
        
        await callback_query.message.edit_text(
            "✅ **Inbox Cleared!**\n\n"
            "All your messages have been permanently deleted.",
            parse_mode="Markdown"
        )
        await callback_query.answer("Inbox cleared!")
    except Exception as e:
        logger.error(f"Error clearing inbox: {e}")
        await callback_query.answer("❌ Failed to clear inbox", show_alert=True)

@inbox_router.callback_query(text_filter("cancel_clear_inbox"))
async def cancel_clear_inbox(callback_query: types.CallbackQuery):
    """Cancel inbox clearance"""
    await callback_query.message.edit_text(
        "❌ **Inbox clearance cancelled.**\n\n"
        "Your messages are safe and unchanged."
    )
    await callback_query.answer("Cancelled")