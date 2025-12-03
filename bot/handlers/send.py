# bot/handlers/send.py
from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.operations import DropIDOperations, InboxOperations
from utils.file_handlers import FileTypeDetector, FileValidator
from config import config
import logging
import secrets
import string

logger = logging.getLogger(__name__)

send_router = Router()

class SendStates(StatesGroup):
    """States for file sending process"""
    waiting_for_file = State()

def generate_anonymous_id(length: int = 6) -> str:
    """Generate anonymous sender ID"""
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

@send_router.message(Command("send"))
async def send_message_command(message: types.Message, command: CommandObject, state: FSMContext):
    """Handle /send command to send messages or files to Drop IDs"""
    try:
        if not command.args:
            await message.answer(
                "📤 <b>Send Messages & Files</b>\n\n"
                "Usage:\n"
                "• /send DROP_ID your message here\n"
                "• Or just send /send DROP_ID and then send the file\n\n"
                "Examples:\n"
                "• /send a8k4z9 Hello! This is a message\n"
                "• /send a8k4z9 (then send a file)\n\n"
                "💡 Get a Drop ID from the recipient first.",
                parse_mode="HTML"
            )
            return

        # Parse command arguments
        args = command.args.strip().split(' ', 1)
        if len(args) < 1:
            await message.answer(
                "❌ <b>Invalid format!</b>\n\n"
                "Correct usage:\n"
                "/send DROP_ID your message here\n\n"
                "Or send /send DROP_ID and then send the file.",
                parse_mode="HTML"
            )
            return

        drop_id = args[0]
        message_text = args[1] if len(args) > 1 else None

        # Validate Drop ID format
        if len(drop_id) != config.DROP_ID_LENGTH or not drop_id.isalnum():
            await message.answer(
                f"❌ <b>Invalid Drop ID format!</b>\n\n"
                f"Drop IDs are {config.DROP_ID_LENGTH} characters long and contain only letters and numbers.\n"
                f"You provided: {drop_id}",
                parse_mode="HTML"
            )
            return

        # Check if Drop ID exists and is active
        target_drop = await DropIDOperations.get_drop_id(drop_id)
        
        if not target_drop:
            await message.answer(
                f"❌ <b>Drop ID not found!</b>\n\n"
                f"The Drop ID {drop_id} doesn't exist.\n"
                f"Please check with the recipient and try again.",
                parse_mode="HTML"
            )
            return

        if not target_drop.is_active:
            await message.answer(
                f"❌ <b>Drop ID is disabled!</b>\n\n"
                f"The Drop ID {drop_id} is currently disabled.\n"
                f"Ask the recipient to enable it using /enable_id.",
                parse_mode="HTML"
            )
            return

        if target_drop.is_expired():
            await message.answer(
                f"❌ <b>Drop ID has expired!</b>\n\n"
                f"The Drop ID {drop_id} has expired.\n"
                f"Ask the recipient to create a new one.",
                parse_mode="HTML"
            )
            return

        # If only Drop ID provided, wait for file
        if not message_text:
            await state.set_state(SendStates.waiting_for_file)
            await state.update_data(drop_id=drop_id)
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_send")]
                ]
            )
            
            await message.answer(
                f"📎 <b>Ready to send file to Drop ID: <code>{drop_id}</code></b>\n\n"
                f"Please send the file now (photo, document, audio, video).\n"
                f"Max size: 50MB\n\n"
                f"<b>Supported files:</b>\n"
                f"• 🖼️ Images (JPEG, PNG, GIF)\n"
                f"• 📄 Documents (PDF, TXT, DOC)\n"
                f"• 🎵 Audio (MP3, OGG)\n"
                f"• 🎬 Video (MP4)\n\n"
                f"Or send /send {drop_id} your_message to send text only.",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            return

        # If message text provided, send as text message
        await process_text_message(message, drop_id, message_text, target_drop)
        
    except Exception as e:
        logger.error(f"Error in send command: {e}")
        await message.answer(
            "❌ <b>Failed to send message.</b>\n\n"
            "Please try again later.",
            parse_mode="HTML"
        )

async def process_text_message(message: types.Message, drop_id: str, message_text: str, target_drop):
    """Process and send a text message"""
    try:
        # Generate anonymous sender ID
        sender_anon_id = generate_anonymous_id()

        # Add message to inbox
        inbox_item = await InboxOperations.add_inbox_item(
            drop_id=drop_id,
            sender_anon_id=sender_anon_id,
            message_text=message_text
        )

        # Handle single-use Drop IDs
        if target_drop.is_single_use:
            await disable_single_use_drop_id(drop_id)
            usage_note = "⚠️ This was a single-use Drop ID and has been automatically disabled."
        else:
            usage_note = "🔄 This Drop ID is still active and can receive more messages."

        # Send confirmation to sender
        confirmation_text = (
            f"✅ <b>Message sent successfully!</b>\n\n"
            f"<b>To Drop ID:</b> <code>{drop_id}</code>\n"
            f"Your Anonymous ID: <code>{sender_anon_id}</code>\n"
            f"Message: {message_text}\n\n"
            f"<i>{usage_note}</i>\n\n"
            f"🔒 <b>Privacy Note:</b> Your identity is completely hidden from the recipient."
        )

        await message.answer(confirmation_text, parse_mode="HTML")
        logger.info(f"Text message sent to Drop ID {drop_id} from anonymous sender {sender_anon_id}")

    except Exception as e:
        logger.error(f"Error processing text message: {e}")
        await message.answer("❌ Failed to send message. Please try again.", parse_mode=None)

async def disable_single_use_drop_id(drop_id: str):
    """Disable a single-use Drop ID after use"""
    try:
        from database.connection import db
        await db.table('drop_ids')\
            .update({'is_active': False})\
            .eq('id', drop_id)\
            .execute()
    except Exception as e:
        logger.error(f"Error disabling single-use Drop ID: {e}")

# Add this debug function to bot/handlers/send.py

async def debug_file_info(file_info: dict):
    """Debug function to log file info"""
    import logging
    logger = logging.getLogger(__name__)
    logger.debug("File Info Debug:")
    for key, value in file_info.items():
        logger.debug(f"  {key}: {value}")

# Then update the handle_file_message function to call this:
@send_router.message(SendStates.waiting_for_file)
async def handle_file_message(message: types.Message, state: FSMContext):
    """Handle file messages when waiting for file"""
    try:
        data = await state.get_data()
        drop_id = data.get('drop_id')
        
        if not drop_id:
            await message.answer("❌ Session expired. Please start over with /send DROP_ID")
            await state.clear()
            return

        # Get fresh Drop ID info
        target_drop = await DropIDOperations.get_drop_id(drop_id)
        if not target_drop or not target_drop.is_active or target_drop.is_expired():
            await message.answer("❌ Drop ID is no longer valid. Please check with the recipient.")
            await state.clear()
            return

        # Process the file based on type
        file_info = await extract_file_info(message)
        
        # Debug logging
        await debug_file_info(file_info)
        
        if not file_info:
            await message.answer(
                "❌ <b>Unsupported file type or no file detected.</b>\n\n"
                "Please send a photo, document, audio, or video file.\n"
                "Max size: 50MB",
                parse_mode="HTML"
            )
            return

        # Validate file safety and size
        if not FileValidator.is_file_safe(file_info['file_name'], file_info['mime_type']):
            await message.answer(
                "❌ <b>File type not allowed for security reasons.</b>\n\n"
                "Please send a different file type.",
                parse_mode="HTML"
            )
            return

        if not FileValidator.is_size_within_limit(file_info['file_size']):
            await message.answer(
                f"❌ <b>File too large!</b>\n\n"
                f"Max size: {FileValidator.format_file_size(FileValidator.MAX_FILE_SIZE)}\n"
                f"Your file: {FileValidator.format_file_size(file_info['file_size'])}",
                parse_mode="HTML"
            )
            return

        # Send the file
        await process_file_message(message, drop_id, file_info, target_drop)
        await state.clear()

    except Exception as e:
        logger.error(f"Error handling file message: {e}")
        logger.error(f"Full error details:", exc_info=True)  # This will print full traceback
        await message.answer("❌ Failed to send file. Please try again.", parse_mode=None)
        await state.clear()
        
async def extract_file_info(message: types.Message) -> dict:
    """Extract file information from different message types"""
    file_info = {}
    
    if message.photo:
        # Photo message (largest size)
        photo = message.photo[-1]
        file_info.update({
            'file_id': photo.file_id,
            'file_type': 'image',
            'file_size': photo.file_size,
            'mime_type': 'image/jpeg',
            'file_name': f'photo_{message.message_id}.jpg'
        })
    
    elif message.document:
        # Document message
        doc = message.document
        file_info.update({
            'file_id': doc.file_id,
            'file_type': FileTypeDetector.categorize_file(doc.mime_type, doc.file_name),
            'file_size': doc.file_size,
            'mime_type': doc.mime_type,
            'file_name': doc.file_name
        })
    
    elif message.audio:
        # Audio message
        audio = message.audio
        file_info.update({
            'file_id': audio.file_id,
            'file_type': 'audio',
            'file_size': audio.file_size,
            'mime_type': audio.mime_type,
            'file_name': audio.file_name or f'audio_{message.message_id}.mp3'
        })
    
    elif message.video:
        # Video message
        video = message.video
        file_info.update({
            'file_id': video.file_id,
            'file_type': 'video',
            'file_size': video.file_size,
            'mime_type': video.mime_type,
            'file_name': video.file_name or f'video_{message.message_id}.mp4'
        })
    
    elif message.voice:
        # Voice message
        voice = message.voice
        file_info.update({
            'file_id': voice.file_id,
            'file_type': 'audio',
            'file_size': voice.file_size,
            'mime_type': 'audio/ogg',
            'file_name': f'voice_{message.message_id}.ogg'
        })
    
    return file_info if file_info else None


async def process_file_message(message: types.Message, drop_id: str, file_info: dict, target_drop):
    """Process and send a file message"""
    try:
        # Generate anonymous sender ID
        sender_anon_id = generate_anonymous_id()

        inbox_item = await InboxOperations.add_file_item(
            drop_id=drop_id,
            sender_anon_id=sender_anon_id,
            file_id=file_info['file_id'],
            file_type=file_info['file_type'],
            file_name=file_info['file_name'],
            file_size=file_info['file_size'],
            mime_type=file_info['mime_type'],
            message_text=message.caption  
        )

        # Handle single-use Drop IDs
        if target_drop.is_single_use:
            await disable_single_use_drop_id(drop_id)
            usage_note = "⚠️ This was a single-use Drop ID and has been automatically disabled."
        else:
            usage_note = "🔄 This Drop ID is still active and can receive more messages."

        # Prepare confirmation message
        file_icon = FileTypeDetector.get_file_icon(file_info['file_type'])
        file_size_str = FileValidator.format_file_size(file_info['file_size'])
        
        # Build file description
        file_description = f"{file_icon} {file_info['file_name'] or 'Unnamed file'}"
        if file_info['file_size']:
            file_description += f" ({file_size_str})"
        
        confirmation_text = (
            f"✅ <b>File sent successfully!</b>\n\n"
            f"To Drop ID: <code>{drop_id}</code>\n"
            f"Your Anonymous ID: <code>{sender_anon_id}</code>\n"
            f"File: {file_description}\n"
            f"Type: {file_info['file_type'].title()}\n\n"
            f"<i>{usage_note}</i>\n\n"
            f"🔒 <b>Privacy Note:</b> Your identity is completely hidden from the recipient."
        )

        await message.answer(confirmation_text, parse_mode="HTML")
        logger.info(f"File sent to Drop ID {drop_id} from anonymous sender {sender_anon_id}")

    except Exception as e:
        logger.error(f"Error processing file message: {e}")
        await message.answer("❌ Failed to send file. Please try again.", parse_mode=None)

@send_router.callback_query(lambda c: c.data == "cancel_send")
async def cancel_send_file(callback_query: types.CallbackQuery, state: FSMContext):
    """Cancel file sending process"""
    await state.clear()
    await callback_query.message.edit_text(
        "❌ File sending cancelled.\n\n"
        "<i>No file was sent.</i>",
        parse_mode="HTML"
    )
    await callback_query.answer("Cancelled")

# Handle direct file sends (without /send command)
@send_router.message(
    lambda message: message.content_type in ['photo', 'document', 'audio', 'video', 'voice'] 
    and message.text is None  # No caption with command
    and not (message.caption and message.caption.startswith('/'))  # No command in caption
)
async def handle_direct_file_send(message: types.Message):
    """Handle direct file sends (without /send command)"""
    await message.answer(
        "💡 <b>To send a file anonymously, use:</b>\n"
        "/send DROP_ID\n\n"
        "Then send your file.\n\n"
        "<i>Get a Drop ID from the recipient first!</i>",
        parse_mode="HTML"
    )