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
                "🔒 PIN Protection\n\n"
                "You haven't set a PIN yet. For security, we recommend setting a PIN "
                "to protect your inbox from unauthorized access.\n\n"
                "PIN Features:\n"
                "• 4-6 digits only\n"
                "• Required to view your inbox\n"
                "• Change anytime with /inbox",
                reply_markup=keyboard,
                parse_mode=None
            )
            return
        
        # PIN is set - prompt for verification
        await message.answer(
            "🔐 PIN Required\n\n"
            "Please enter your 4-6 digit PIN to access your inbox:",
            parse_mode=None
        )
        await state.set_state(InboxStates.waiting_for_pin)
        await state.update_data(user_id=user_id)
        
    except Exception as e:
        logger.error(f"Error in inbox command: {e}")
        await message.answer("❌ Failed to access inbox. Please try again.", parse_mode=None)

@inbox_router.callback_query(text_filter("set_pin"))
async def start_set_pin(callback_query: types.CallbackQuery, state: FSMContext):
    """Start PIN setup process"""
    await callback_query.message.edit_text(
        "🛡️ Set Your PIN\n\n"
        "Please enter a 4-6 digit PIN for inbox protection:",
        parse_mode=None
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
                    "🚫 Too many failed attempts!\n\n"
                    "For security reasons, please wait a few minutes before trying again.",
                    parse_mode=None
                )
                await state.clear()
            else:
                remaining_attempts = 3 - wrong_attempts
                await message.answer(
                    f"❌ Incorrect PIN!\n\n"
                    f"You have {remaining_attempts} attempt{'s' if remaining_attempts > 1 else ''} remaining.\n"
                    f"Please enter your PIN again:",
                    parse_mode=None
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
                "❌ Invalid PIN format!\n\n"
                "PIN must be 4-6 digits only.\n"
                "Please enter a valid PIN:",
                parse_mode=None
            )
            return
        
        # Store PIN in state and ask for confirmation
        await state.update_data(new_pin=pin)
        await message.answer(
            "🔐 Confirm Your PIN\n\n"
            "Please enter the same PIN again to confirm:",
            parse_mode=None
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
                "❌ PINs don't match!\n\n"
                "Please start over with /inbox to set a new PIN.",
                parse_mode=None
            )
            await state.clear()
            return
        
        # Hash and save PIN
        pin_hash = PINManager.hash_pin(original_pin)
        await UserOperations.set_user_pin(user_id, pin_hash)
        
        await message.answer(
            "✅ PIN set successfully!\n\n"
            "Your inbox is now protected. Use /inbox to access your messages.",
            parse_mode=None
        )
        await state.clear()
        
        # Show inbox after PIN setup
        await show_inbox_contents(message, user_id)
        
    except Exception as e:
        logger.error(f"Error confirming PIN: {e}")
        await message.answer("❌ Failed to set PIN. Please try again.")
        await state.clear()

async def show_inbox_contents(message: types.Message, user_id: int):
    """Display user's inbox contents with file delivery options (HTML-formatted, friendly dates/times)"""
    try:
        import html
        from collections import defaultdict
        from datetime import datetime, timedelta, timezone
        try:
           
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("Africa/Addis_Ababa")
        except Exception:
            # Fallback: use UTC if zoneinfo unavailable
            tz = timezone.utc

        inbox_items = await InboxOperations.get_user_inbox(user_id)

        # Ensure inbox_items is always a list
        if inbox_items is None:
            inbox_items = []
            logger.warning(f"Inbox items was None for user {user_id}, using empty list")

        if not inbox_items:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🆕 Create Drop ID", callback_data="create_from_inbox")],
                    [InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh_inbox")]
                ]
            )

            empty_msg = (
                "<b>Your Inbox is Empty</b>\n\n"
                "You haven't received any messages yet.\n\n"
                "<b>To receive messages</b>\n"
                "• Create a Drop ID with <code>/create_id</code>\n"
                "• Share it with others\n"
                "• They can send you messages with <code>/send YOUR_DROP_ID</code>"
            )

            await message.answer(
                empty_msg,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            return

        # Debug: Print all items to see what data we have
        logger.info(f"Found {len(inbox_items)} inbox items for user {user_id}")

        # Normalize item datetimes to user's timezone and group items by date (friendly)
        items_by_date = defaultdict(list)
        for item in inbox_items:
            created = item.created_at
            # If created_at is naive, treat as UTC
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            # Convert to user's tz
            try:
                created_local = created.astimezone(tz)
            except Exception:
                # fallback: keep as-is
                created_local = created

            item._created_local = created_local  # attach for later use
            date_key = created_local.date().isoformat()
            items_by_date[date_key].append(item)

        # Prepare friendly heading labels
        now_local = datetime.now(tz)
        today = now_local.date()
        yesterday = today - timedelta(days=1)

        # Build response in parts for readability
        parts = []
        parts.append("<b>Your Inbox</b>\n\n")

        # Iterate dates newest first
        for date_iso in sorted(items_by_date.keys(), reverse=True):
            items = items_by_date[date_iso]
            # parse date
            try:
                date_obj = datetime.fromisoformat(date_iso).date()
            except Exception:
                # fallback to showing raw string
                date_obj = None

            if date_obj == today:
                heading = "📅 Today"
            elif date_obj == yesterday:
                heading = "📅 Yesterday"
            elif date_obj:
                heading = date_obj.strftime("📅 %b %d, %Y") 
            else:
                heading = f"📅 {date_iso}"

            parts.append(f"{heading}\n")

            for item in items:
                # Get local time string, e.g., "3:45 PM"
                created_local = getattr(item, "_created_local", item.created_at)
                try:
                    time_str = created_local.strftime("%I:%M %p").lstrip("0")
                    tz_abbr = created_local.tzname() or ""
                    time_display = f"{time_str} {tz_abbr}".strip()
                except Exception:
                    time_display = created_local.strftime("%H:%M")

                sender = html.escape(str(getattr(item, "sender_anon_id", "anon")))
                drop = html.escape(str(getattr(item, "drop_id", "unknown")))

                if getattr(item, "file_id", None):
                    # File message - get actual file details
                    from utils.file_handlers import FileTypeDetector, FileValidator

                    file_icon = FileTypeDetector.get_file_icon(item.file_type)

                    # Safe file name
                    file_name_raw = getattr(item, "file_name", None)
                    if not file_name_raw:
                        # Generate descriptive fallback name
                        if item.file_type == "image":
                            file_name_raw = f"image_{item.id}.jpg"
                        elif item.file_type == "audio":
                            file_name_raw = f"audio_{item.id}.mp3"
                        elif item.file_type == "video":
                            file_name_raw = f"video_{item.id}.mp4"
                        elif item.file_type == "document":
                            file_name_raw = f"document_{item.id}.pdf"
                        else:
                            file_name_raw = f"file_{item.id}"

                    file_name = html.escape(str(file_name_raw))

                    # file size if available
                    file_size = getattr(item, "file_size", None)
                    if file_size:
                        size_str = FileValidator.format_file_size(file_size)
                        file_desc = f"{file_icon} {file_name} ({html.escape(size_str)})"
                    else:
                        file_desc = f"{file_icon} {file_name}"

                    parts.append(f"• <b>{time_display}</b> 👤 <code>{sender}</code> → <code>{html.escape(drop)}</code>: {file_desc}\n")

                    if item.message_text:
                        caption_preview = safe_truncate(item.message_text, 30)
                        caption_escaped = html.escape(caption_preview)
                        parts.append(f"  📝 {caption_escaped}\n")

                elif item.message_text:
                    # Text message
                    message_preview = safe_truncate(item.message_text, 50)
                    message_escaped = html.escape(message_preview)
                    parts.append(f"• <b>{time_display}</b> 👤 <code>{sender}</code> → <code>{html.escape(drop)}</code>: 💬 {message_escaped}\n")

            parts.append("\n")

        # Add management summary and hints
        parts.append(f"<b>Total Messages:</b> {len(inbox_items)}\n\n")
        parts.append("💡 Click on file buttons below to view / download files.\n")
        parts.append("🔧 Use <code>/disable_id</code> to manage your Drop IDs")

        response_text = "".join(parts)

        # Create file delivery buttons - only for items with files
        file_items = [item for item in inbox_items if getattr(item, "file_id", None)]

        if file_items:
            file_buttons = []
            current_row = []

            for i, item in enumerate(file_items):
                from utils.file_handlers import FileTypeDetector
                file_icon = FileTypeDetector.get_file_icon(item.file_type)

                
                file_name_raw = getattr(item, "file_name", None)
                if not file_name_raw:
                    if item.file_type == "image":
                        file_name_raw = f"Image_{item.id}"
                    elif item.file_type == "audio":
                        file_name_raw = f"Audio_{item.id}"
                    elif item.file_type == "video":
                        file_name_raw = f"Video_{item.id}"
                    elif item.file_type == "document":
                        file_name_raw = f"Document_{item.id}"
                    else:
                        file_name_raw = f"File_{item.id}"

                button_text = str(file_name_raw)
                if len(button_text) > 15:
                    button_text = button_text[:12] + "..."

                button = InlineKeyboardButton(
                    text=f"{file_icon} {button_text}",
                    callback_data=f"view_file_{item.id}"
                )

                current_row.append(button)

                # Add rows of 2 buttons each
                if len(current_row) >= 2 or i == len(file_items) - 1:
                    file_buttons.append(current_row)
                    current_row = []

            # Add navigation buttons
            nav_buttons = [
                InlineKeyboardButton(text="🆕 Create Drop ID", callback_data="create_from_inbox"),
                InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh_inbox")
            ]
            file_buttons.append(nav_buttons)

            keyboard = InlineKeyboardMarkup(inline_keyboard=file_buttons)
        else:
            # No files, just show navigation buttons
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🆕 Create Drop ID", callback_data="create_from_inbox")],
                    [InlineKeyboardButton(text="🔄 Refresh", callback_data="refresh_inbox")]
                ]
            )

        await message.answer(response_text, reply_markup=keyboard, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error showing inbox contents: {e}")
        logger.error(f"Full error details:", exc_info=True)
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
            f"🎯 Drop ID Created from Inbox!\n\n"
            f"Your new Drop ID: {drop_id.id}\n\n"
            f"Share this ID to start receiving messages!",
            parse_mode=None
        )
        await callback_query.answer("Drop ID created!")
    except Exception as e:
        logger.error(f"Error creating Drop ID from inbox: {e}")
        await callback_query.answer("❌ Failed to create Drop ID", show_alert=True)

@inbox_router.callback_query(lambda c: c.data.startswith("view_file_"))
async def view_file(callback_query: types.CallbackQuery):
    """Send the actual file to the user"""
    try:
        file_item_id = int(callback_query.data.replace("view_file_", ""))
        user_id = callback_query.from_user.id
        
        # Get the file item from database
        from database.connection import db
        response = db.table('inbox_items').select('*').eq('id', file_item_id).execute()
        
        if not response.data or len(response.data) == 0:
            await callback_query.answer("❌ File not found", show_alert=True)
            return
        
        file_data = response.data[0]
        
        # Verify the user owns this file (through Drop ID ownership)
        drop_id_response = db.table('drop_ids').select('owner_id').eq('id', file_data['drop_id']).execute()
        if not drop_id_response.data or drop_id_response.data[0]['owner_id'] != user_id:
            await callback_query.answer("❌ Access denied", show_alert=True)
            return
        
        # Send the file based on its type
        await send_file_to_user(callback_query, file_data)
        
    except Exception as e:
        logger.error(f"Error viewing file: {e}")
        await callback_query.answer("❌ Failed to load file", show_alert=True)

async def send_file_to_user(callback_query: types.CallbackQuery, file_data: dict):
    """Send the actual file to the user based on file type"""
    try:
        file_id = file_data['file_id']
        file_type = file_data['file_type']
        file_name = file_data.get('file_name', 'File')
        caption = file_data.get('message_text', '')
        
        # Add sender info to caption
        sender_info = f"\n\n👤 From: Anonymous ({file_data['sender_anon_id']})"
        if caption:
            full_caption = caption + sender_info
        else:
            full_caption = f"📎 {file_name}{sender_info}"
        
        # Send file based on type
        if file_type == 'image':
            await callback_query.message.answer_photo(
                photo=file_id,
                caption=full_caption,
                parse_mode=None
            )
        elif file_type == 'document':
            await callback_query.message.answer_document(
                document=file_id,
                caption=full_caption,
                parse_mode=None
            )
        elif file_type == 'audio':
            await callback_query.message.answer_audio(
                audio=file_id,
                caption=full_caption,
                parse_mode=None
            )
        elif file_type == 'video':
            await callback_query.message.answer_video(
                video=file_id,
                caption=full_caption,
                parse_mode=None
            )
        else:
            # Fallback for unknown file types
            await callback_query.message.answer_document(
                document=file_id,
                caption=full_caption,
                parse_mode=None
            )
        
        await callback_query.answer("✅ File sent!")
        
    except Exception as e:
        logger.error(f"Error sending file to user: {e}")
        await callback_query.answer("❌ Failed to send file", show_alert=True)

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
        "🚨 <b>Clear Entire Inbox?</b>\n\n"
        "This will permanently <b>delete</b> all your received messages.\n"
        "This action cannot be undone!\n\n"
        "Are you sure you want to clear your entire inbox?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback_query.answer()

@inbox_router.callback_query(text_filter("confirm_clear_inbox"))
async def confirm_clear_inbox(callback_query: types.CallbackQuery):
    """Clear user's entire inbox"""
    try:
        user_id = callback_query.from_user.id
        await InboxOperations.clear_user_inbox(user_id)
        
        await callback_query.message.edit_text(
            "✅ <b>Inbox Cleared!</b>\n\n"
            "All your messages have been permanently deleted.",
            parse_mode="HTML"
        )
        await callback_query.answer("Inbox cleared!")
    except Exception as e:
        logger.error(f"Error clearing inbox: {e}")
        await callback_query.answer("❌ Failed to clear inbox", show_alert=True)

@inbox_router.callback_query(text_filter("cancel_clear_inbox"))
async def cancel_clear_inbox(callback_query: types.CallbackQuery):
    """Cancel inbox clearance"""
    await callback_query.message.edit_text(
        "❌ Inbox clearance cancelled.\n\n"
        "Your messages are safe and unchanged."
    )
    await callback_query.answer("Cancelled")