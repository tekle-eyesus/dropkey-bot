from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.operations import DropIDOperations, UserOperations
from config import config
import logging

logger = logging.getLogger(__name__)

dropid_router = Router()

class CreateDropIDStates(StatesGroup):
    """States for creating Drop ID with options"""
    waiting_for_expiration = State()

@dropid_router.message(Command("create_id"))
async def create_drop_id_command(message: types.Message):
    """Handle /create_id command - create a basic Drop ID"""
    try:
        user_id = message.from_user.id
        
        # Ensure user exists in database
        await UserOperations.get_or_create_user(user_id)
        
        # Create a basic Drop ID (no expiration, not single-use)
        drop_id = await DropIDOperations.create_drop_id(user_id)
        
        response_text = f"""
<b>Your Drop ID has been created!</b>

<b>Drop ID:</b> <code>{drop_id.id}</code>
<b>Status:</b> ✅ Active
<b>Type:</b> 🔄 Reusable
<b>Expires:</b> Never

<b>How to Use</b>
• Share your Drop ID with anyone  
• They can send you files using <code>/send {drop_id.id}</code>  
• Check received files with <code>/inbox</code>

<b>Security Tips</b>
• Use <code>/disable_id</code> to temporarily disable this ID  
• Create different IDs for different purposes  
• Never share your inbox PIN with anyone
"""


        
        # Create inline keyboard with options
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔄 Create Another", callback_data="create_another"),
                    InlineKeyboardButton(text="⚡ Create Single-Use", callback_data="create_single_use")
                ],
                [
                    InlineKeyboardButton(text="⏰ Create Expiring", callback_data="create_expiring"),
                    InlineKeyboardButton(text="📋 My Drop IDs", callback_data="list_drop_ids")
                ]
            ]
        )
        
        await message.answer(response_text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error creating Drop ID: {e}")
        await message.answer("❌ Failed to create Drop ID. Please try again.")

@dropid_router.callback_query(lambda c: c.data == "create_another")
async def create_another_drop_id(callback_query: types.CallbackQuery):
    """Create another basic Drop ID"""
    try:
        user_id = callback_query.from_user.id
        drop_id = await DropIDOperations.create_drop_id(user_id)
        
        response_text = f"""
<b>Another Drop ID Created!</b>

<b>New Drop ID:</b> <code>{drop_id.id}</code>
<b>Status:</b> ✅ Active
<b>Type:</b> 🔄 Reusable
<b>Expires:</b> Never

You now have multiple Drop IDs that you can use for different purposes.
"""

        
        await callback_query.message.edit_text(response_text, parse_mode="HTML")
        await callback_query.answer("New Drop ID created!")
        
    except Exception as e:
        logger.error(f"Error creating another Drop ID: {e}")
        await callback_query.answer("❌ Failed to create Drop ID", show_alert=True)

@dropid_router.callback_query(lambda c: c.data == "create_single_use")
async def create_single_use_drop_id(callback_query: types.CallbackQuery):
    """Create a single-use Drop ID"""
    try:
        user_id = callback_query.from_user.id
        drop_id = await DropIDOperations.create_drop_id(
            user_id, 
            is_single_use=True
        )
        
        response_text = f"""
<b>Single-Use Drop ID Created!</b>

<b>Drop ID:</b> <code>{drop_id.id}</code>
<b>Status:</b> ✅ Active
<b>Type:</b> 🚫 Single-Use
<b>Expires:</b> Never

⚠️ <b>This ID will be automatically disabled after the first use.</b>
Perfect for one-time transfers or sensitive sharing.
"""

        await callback_query.message.edit_text(response_text, parse_mode="HTML")
        await callback_query.answer("Single-use Drop ID created!")
        
    except Exception as e:
        logger.error(f"Error creating single-use Drop ID: {e}")
        await callback_query.answer("❌ Failed to create Drop ID", show_alert=True)

@dropid_router.callback_query(lambda c: c.data == "create_expiring")
async def create_expiring_drop_id_prompt(callback_query: types.CallbackQuery, state: FSMContext):
    """Prompt user for expiration time"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1 Hour", callback_data="expire_1"),
                InlineKeyboardButton(text="6 Hours", callback_data="expire_6"),
                InlineKeyboardButton(text="24 Hours", callback_data="expire_24"),
            ],
            [
                InlineKeyboardButton(text="3 Days", callback_data="expire_72"),
                InlineKeyboardButton(text="7 Days", callback_data="expire_168"),
                InlineKeyboardButton(text="Cancel", callback_data="cancel_expire"),
            ]
        ]
    )
    
    await callback_query.message.edit_text(
        "⏰ <b>Select expiration time for your Drop ID:</b>\n\n"
        "The Drop ID will automatically become inactive after the selected time.",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback_query.answer()

@dropid_router.callback_query(lambda c: c.data.startswith("expire_"))
async def create_expiring_drop_id(callback_query: types.CallbackQuery):
    """Create Drop ID with expiration"""
    try:
        user_id = callback_query.from_user.id
        hours = int(callback_query.data.split("_")[1])
        
        drop_id = await DropIDOperations.create_drop_id(
            user_id,
            expires_hours=hours
        )
        
        # Format expiration time display
        if hours < 24:
            expires_text = f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            days = hours // 24
            expires_text = f"{days} day{'s' if days > 1 else ''}"
        
        response_text = f"""
⏰ <b>Expiring Drop ID Created!</b>

<b>Drop ID:</b> <code>{drop_id.id}</code>
<b>Status:</b> ✅ Active
<b>Type:</b> 🔄 Reusable
<b>Expires:</b> In {expires_text}

⚠️ <b>This ID will automatically expire in {expires_text}.</b>
Perfect for temporary sharing needs.
"""

        
        await callback_query.message.edit_text(response_text, parse_mode="HTML")
        await callback_query.answer(f"Expiring Drop ID created! (expires in {expires_text})")
        
    except Exception as e:
        logger.error(f"Error creating expiring Drop ID: {e}")
        await callback_query.answer("❌ Failed to create Drop ID", show_alert=True)

@dropid_router.callback_query(lambda c: c.data == "list_drop_ids")
async def list_user_drop_ids(callback_query: types.CallbackQuery):
    """List all user's Drop IDs"""
    try:
        user_id = callback_query.from_user.id
        drop_ids = await DropIDOperations.get_user_drop_ids(user_id)
        
        if not drop_ids:
            response_text = "📭 You don't have any Drop IDs yet.\nUse /create_id to create your first one!"
        else:
            response_text = "<b>Your Drop IDs:</b>\n\n"
            
            for drop_id in drop_ids:
                status = "✅ Active" if drop_id.is_active else "❌ Disabled"
                id_type = "🚫 Single-Use" if drop_id.is_single_use else "🔄 Reusable"
                
                if drop_id.is_expired():
                    status = "⏰ Expired"
                elif drop_id.expires_at:
                    # Calculate time remaining
                    from datetime import datetime
                    now = datetime.utcnow()
                    remaining = drop_id.expires_at - now
                    hours = int(remaining.total_seconds() // 3600)
                    if hours > 24:
                        expires_text = f"{hours//24}d {hours%24}h"
                    else:
                        expires_text = f"{hours}h"
                    status = f"⏰ Expires in {expires_text}"
                
                response_text += f"• `{drop_id.id}` - {status} - {id_type}\n"
            
            response_text += "\n💡 Use `/disable_id` or `/enable_id` to manage your Drop IDs."
        
        await callback_query.message.edit_text(response_text, parse_mode="HTML")
        await callback_query.answer("Your Drop IDs")
        
    except Exception as e:
        logger.error(f"Error listing Drop IDs: {e}")
        await callback_query.answer("❌ Failed to load Drop IDs", show_alert=True)

@dropid_router.callback_query(lambda c: c.data == "cancel_expire")
async def cancel_expiring_drop_id(callback_query: types.CallbackQuery):
    """Cancel expiring Drop ID creation"""
    await callback_query.message.edit_text(
        "❌ Expiring Drop ID creation cancelled.\n"
        "Use /create_id to create a regular Drop ID."
    )
    await callback_query.answer("Cancelled")