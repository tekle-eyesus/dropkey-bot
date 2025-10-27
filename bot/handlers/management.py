from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.operations import DropIDOperations, UserOperations
from config import config
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

management_router = Router()

def text_filter(text: str):
    """Custom text filter for callback queries"""
    async def func(callback_query: types.CallbackQuery):
        return callback_query.data == text
    return func

def escape_markdown(text: str) -> str:
    """Escape special Markdown characters"""
    if not text:
        return ""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in str(text))

def safe_truncate(text: str, max_length: int = 50) -> str:
    """Safely truncate text without breaking Markdown"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

@management_router.message(Command("disable_id"))
async def disable_id_command(message: types.Message):
    """Handle /disable_id command - show user's Drop IDs for disabling"""
    logger.info(f"🔴 Disable ID command received from user {message.from_user.id}")
    try:
        user_id = message.from_user.id
        
        # Get user's Drop IDs
        drop_ids = await DropIDOperations.get_user_drop_ids(user_id)
        
        if not drop_ids:
            await message.answer(
                "📭 No Drop IDs Found\n\n"
                "You don't have any active Drop IDs to disable.\n"
                "Use /create_id to create your first Drop ID!",
                parse_mode=None 
            )
            return
        
        # Filter active Drop IDs only
        active_drop_ids = [drop for drop in drop_ids if drop.is_active and not drop.is_expired()]
        
        if not active_drop_ids:
            await message.answer(
                "🔒 All Drop IDs Already Disabled\n\n"
                "All your Drop IDs are currently disabled or expired.\n"
                "Use /enable_id to reactivate them or /create_id to create new ones.",
                parse_mode=None
            )
            return
        
        # Create keyboard with active Drop IDs
        keyboard_buttons = []
        for drop_id in active_drop_ids:
            status = "⏰ Expires soon" if drop_id.expires_at else "🔄 Reusable"
            if drop_id.is_single_use:
                status = "🚫 Single-use"
            
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"🔴 {drop_id.id} ({status})",
                    callback_data=f"disable_{drop_id.id}"
                )
            ])
        
        # Add "Disable All" and "Cancel" buttons
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔴 Disable All", callback_data="disable_all"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_disable")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await message.answer(
            "🔴 Disable Drop IDs\n\n"
            "Select which Drop ID you want to disable:\n\n"
            "What happens when disabled:\n"
            "• No one can send messages to this ID\n"
            "• You can enable it later with /enable_id\n"
            "• Existing messages in inbox remain safe",
            reply_markup=keyboard,
            parse_mode=None  # Disable Markdown
        )
        
    except Exception as e:
        logger.error(f"Error in disable_id command: {e}")
        await message.answer("❌ Failed to load Drop IDs. Please try again.", parse_mode=None)

@management_router.message(Command("enable_id"))
async def enable_id_command(message: types.Message):
    """Handle /enable_id command - show user's disabled Drop IDs for enabling"""
    try:
        user_id = message.from_user.id
        
        # Get user's Drop IDs
        drop_ids = await DropIDOperations.get_user_drop_ids(user_id)
        
        if not drop_ids:
            await message.answer(
                "📭 No Drop IDs Found\n\n"
                "You don't have any Drop IDs to enable.\n"
                "Use /create_id to create your first Drop ID!",
                parse_mode=None
            )
            return
        
        # Filter disabled but not expired Drop IDs
        disabled_drop_ids = [drop for drop in drop_ids if not drop.is_active and not drop.is_expired()]
        
        if not disabled_drop_ids:
            await message.answer(
                "✅ All Drop IDs Are Active\n\n"
                "All your non-expired Drop IDs are currently active.\n"
                "Use /disable_id to disable them or /create_id to create new ones.",
                parse_mode=None
            )
            return
        
        # Create keyboard with disabled Drop IDs
        keyboard_buttons = []
        for drop_id in disabled_drop_ids:
            status = "⏰ Expiring" if drop_id.expires_at else "🔄 Reusable"
            if drop_id.is_single_use:
                status = "🚫 Single-use"
            
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"🟢 {drop_id.id} ({status})",
                    callback_data=f"enable_{drop_id.id}"
                )
            ])
        
        # Add "Enable All" and "Cancel" buttons
        keyboard_buttons.append([
            InlineKeyboardButton(text="🟢 Enable All", callback_data="enable_all"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_enable")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await message.answer(
            "🟢 Enable Drop IDs\n\n"
            "Select which Drop ID you want to enable:\n\n"
            "Note: Expired Drop IDs cannot be enabled.\n"
            "You'll need to create new ones with /create_id",
            reply_markup=keyboard,
            parse_mode=None
        )
        
    except Exception as e:
        logger.error(f"Error in enable_id command: {e}")
        await message.answer("❌ Failed to load Drop IDs. Please try again.", parse_mode=None)

@management_router.callback_query(text_filter("cancel_disable"))
async def cancel_disable(callback_query: types.CallbackQuery):
    """Cancel disable operation"""
    await callback_query.message.edit_text(
        "❌ Drop ID disable cancelled.\n\n"
        "Your Drop IDs remain active and can receive messages.",
        parse_mode=None
    )
    await callback_query.answer("Cancelled")

@management_router.callback_query(text_filter("cancel_enable"))
async def cancel_enable(callback_query: types.CallbackQuery):
    """Cancel enable operation"""
    await callback_query.message.edit_text(
        "❌ Drop ID enable cancelled.\n\n"
        "No changes were made to your Drop IDs.",
        parse_mode=None
    )
    await callback_query.answer("Cancelled")

@management_router.callback_query(lambda c: c.data.startswith("disable_"))
async def disable_single_drop_id(callback_query: types.CallbackQuery):
    """Disable a single Drop ID"""
    try:
        drop_id = callback_query.data.replace("disable_", "")
        user_id = callback_query.from_user.id
        
        # Verify ownership and disable
        success = await DropIDOperations.disable_drop_id(drop_id, user_id)
        
        if success:
            await callback_query.message.edit_text(
                f"🔴 Drop ID Disabled\n\n"
                f"Drop ID: {drop_id}\n"
                f"Status: ❌ Disabled\n\n"
                f"This ID can no longer receive messages.\n"
                f"Use /enable_id to reactivate it later.",
                parse_mode=None
            )
            await callback_query.answer("Drop ID disabled!")
        else:
            await callback_query.message.edit_text(
                f"❌ Failed to disable Drop ID\n\n"
                f"The Drop ID {drop_id} doesn't exist or you don't own it.",
                parse_mode=None
            )
            await callback_query.answer("Failed to disable", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error disabling Drop ID: {e}")
        await callback_query.answer("❌ Failed to disable Drop ID", show_alert=True)

@management_router.callback_query(lambda c: c.data.startswith("enable_"))
async def enable_single_drop_id(callback_query: types.CallbackQuery):
    """Enable a single Drop ID"""
    try:
        drop_id = callback_query.data.replace("enable_", "")
        user_id = callback_query.from_user.id
        
        # Verify ownership and enable
        success = await DropIDOperations.enable_drop_id(drop_id, user_id)
        
        if success:
            await callback_query.message.edit_text(
                f"🟢 Drop ID Enabled\n\n"
                f"Drop ID: {drop_id}\n"
                f"Status: ✅ Active\n\n"
                f"This ID can now receive messages again!",
                parse_mode=None
            )
            await callback_query.answer("Drop ID enabled!")
        else:
            await callback_query.message.edit_text(
                f"❌ Failed to enable Drop ID\n\n"
                f"The Drop ID {drop_id} doesn't exist, you don't own it, or it has expired.",
                parse_mode=None
            )
            await callback_query.answer("Failed to enable", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error enabling Drop ID: {e}")
        await callback_query.answer("❌ Failed to enable Drop ID", show_alert=True)

@management_router.callback_query(text_filter("disable_all"))
async def disable_all_drop_ids(callback_query: types.CallbackQuery):
    """Disable all user's Drop IDs"""
    try:
        user_id = callback_query.from_user.id
        
        # Get all active Drop IDs
        drop_ids = await DropIDOperations.get_user_drop_ids(user_id)
        active_drop_ids = [drop for drop in drop_ids if drop.is_active and not drop.is_expired()]
        
        if not active_drop_ids:
            await callback_query.message.edit_text(
                "❌ No Active Drop IDs\n\n"
                "You don't have any active Drop IDs to disable.",
                parse_mode=None
            )
            await callback_query.answer("No active IDs found")
            return
        
        # Disable all active Drop IDs
        disabled_count = 0
        for drop in active_drop_ids:
            success = await DropIDOperations.disable_drop_id(drop.id, user_id)
            if success:
                disabled_count += 1
        
        await callback_query.message.edit_text(
            f"🔴 All Drop IDs Disabled\n\n"
            f"Disabled: {disabled_count} Drop ID(s)\n\n"
            f"All your active Drop IDs have been disabled.\n"
            f"They can no longer receive messages.\n\n"
            f"Use /enable_id to reactivate them later.",
            parse_mode=None
        )
        await callback_query.answer(f"Disabled {disabled_count} IDs")
        
    except Exception as e:
        logger.error(f"Error disabling all Drop IDs: {e}")
        await callback_query.answer("❌ Failed to disable all Drop IDs", show_alert=True)

@management_router.callback_query(text_filter("enable_all"))
async def enable_all_drop_ids(callback_query: types.CallbackQuery):
    """Enable all user's disabled Drop IDs"""
    try:
        user_id = callback_query.from_user.id
        
        # Get all disabled but not expired Drop IDs
        drop_ids = await DropIDOperations.get_user_drop_ids(user_id)
        disabled_drop_ids = [drop for drop in drop_ids if not drop.is_active and not drop.is_expired()]
        
        if not disabled_drop_ids:
            await callback_query.message.edit_text(
                "❌ No Disabled Drop IDs\n\n"
                "You don't have any disabled Drop IDs to enable.",
                parse_mode=None
            )
            await callback_query.answer("No disabled IDs found")
            return
        
        # Enable all disabled Drop IDs
        enabled_count = 0
        for drop in disabled_drop_ids:
            success = await DropIDOperations.enable_drop_id(drop.id, user_id)
            if success:
                enabled_count += 1
        
        await callback_query.message.edit_text(
            f"🟢 All Drop IDs Enabled\n\n"
            f"Enabled: {enabled_count} Drop ID(s)\n\n"
            f"All your disabled Drop IDs have been reactivated.\n"
            f"They can now receive messages again!",
            parse_mode=None
        )
        await callback_query.answer(f"Enabled {enabled_count} IDs")
        
    except Exception as e:
        logger.error(f"Error enabling all Drop IDs: {e}")
        await callback_query.answer("❌ Failed to enable all Drop IDs", show_alert=True)

@management_router.message(Command("my_ids"))
async def my_ids_command(message: types.Message):
    """Handle /my_ids command - show all user's Drop IDs with detailed info"""
    try:
        user_id = message.from_user.id
        drop_ids = await DropIDOperations.get_user_drop_ids(user_id)
        
        if not drop_ids:
            await message.answer(
                "📭 No Drop IDs Found\n\n"
                "You haven't created any Drop IDs yet.\n"
                "Use /create_id to create your first one!",
                parse_mode=None
            )
            return
        
        # Sort by creation date (newest first)
        drop_ids.sort(key=lambda x: x.created_at, reverse=True)
        
        # Build response in chunks to avoid message length limits
        chunks = []
        current_chunk = "📋 Your Drop IDs\n\n"
        
        active_count = 0
        disabled_count = 0
        expired_count = 0
        
        for i, drop in enumerate(drop_ids):
            # Determine status
            if drop.is_expired():
                status = "⏰ Expired"
                expired_count += 1
            elif not drop.is_active:
                status = "🔴 Disabled"
                disabled_count += 1
            else:
                status = "🟢 Active"
                active_count += 1
            
            # Determine type
            if drop.is_single_use:
                drop_type = "🚫 Single-use"
            else:
                drop_type = "🔄 Reusable"
            
            # Expiration info
            if drop.expires_at:
                now = datetime.utcnow()
                if drop.expires_at > now:
                    remaining = drop.expires_at - now
                    hours = int(remaining.total_seconds() // 3600)
                    if hours > 24:
                        expires_text = f"{hours//24}d {hours%24}h remaining"
                    else:
                        expires_text = f"{hours}h remaining"
                else:
                    expires_text = "Expired"
            else:
                expires_text = "Never"
            
            # Creation date
            created_str = drop.created_at.strftime("%Y-%m-%d %H:%M")
            
            drop_info = (
                f"ID: {drop.id}\n"
                f"Status: {status} | Type: {drop_type}\n"
                f"Expires: {expires_text}\n"
                f"Created: {created_str}\n"
                f"{'─' * 30}\n"
            )
            
            # Check if adding this drop would exceed reasonable message length
            if len(current_chunk) + len(drop_info) > 3500:  # Leave some buffer
                chunks.append(current_chunk)
                current_chunk = f"📋 Your Drop IDs (continued)\n\n"
            
            current_chunk += drop_info
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        # Send summary as the last message
        summary = (
            f"Summary:\n"
            f"• 🟢 Active: {active_count}\n"
            f"• 🔴 Disabled: {disabled_count}\n"
            f"• ⏰ Expired: {expired_count}\n"
            f"• 📊 Total: {len(drop_ids)}\n\n"
            f"Management:\n"
            f"• Use /disable_id to disable active IDs\n"
            f"• Use /enable_id to enable disabled IDs\n"
            f"• Use /create_id to create new IDs\n"
            f"• Expired IDs cannot be reactivated"
        )
        
        # Send all chunks
        for i, chunk in enumerate(chunks):
            if i == len(chunks) - 1:
                # Last chunk - add summary
                await message.answer(chunk + "\n" + summary, parse_mode=None)
            else:
                await message.answer(chunk, parse_mode=None)
        
    except Exception as e:
        logger.error(f"Error in my_ids command: {e}")
        await message.answer("❌ Failed to load your Drop IDs. Please try again.", parse_mode=None)