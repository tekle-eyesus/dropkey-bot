from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.operations import DropIDOperations, InboxOperations
from config import config
import logging
import secrets
import string

logger = logging.getLogger(__name__)

send_router = Router()

def generate_anonymous_id(length: int = 6) -> str:
    """Generate anonymous sender ID"""
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

@send_router.message(Command("send"))
async def send_message_command(message: types.Message, command: CommandObject):
    """Handle /send command to send messages to Drop IDs"""
    try:
        if not command.args:
            await message.answer(
                "❌ **Usage:** `/send DROP_ID your message here`\n\n"
                "**Example:**\n"
                "`/send a8k4z9 Hello! This is a secret message.`\n\n"
                "💡 Get a Drop ID from the recipient first.",
                parse_mode="Markdown"
            )
            return

        # Parse command arguments
        args = command.args.strip().split(' ', 1)
        if len(args) < 2:
            await message.answer(
                "❌ **Invalid format!**\n\n"
                "**Correct usage:**\n"
                "`/send DROP_ID your message here`\n\n"
                "**Example:**\n"
                "`/send a8k4z9 This is my secret message!`",
                parse_mode="Markdown"
            )
            return

        drop_id, message_text = args

        # Validate Drop ID format
        if len(drop_id) != config.DROP_ID_LENGTH or not drop_id.isalnum():
            await message.answer(
                f"❌ **Invalid Drop ID format!**\n\n"
                f"Drop IDs are {config.DROP_ID_LENGTH} characters long and contain only letters and numbers.\n"
                f"**You provided:** `{drop_id}`",
                parse_mode="Markdown"
            )
            return

        # Check if Drop ID exists and is active
        target_drop = await DropIDOperations.get_drop_id(drop_id)
        
        if not target_drop:
            await message.answer(
                f"❌ **Drop ID not found!**\n\n"
                f"The Drop ID `{drop_id}` doesn't exist.\n"
                f"Please check with the recipient and try again.",
                parse_mode="Markdown"
            )
            return

        if not target_drop.is_active:
            await message.answer(
                f"❌ **Drop ID is disabled!**\n\n"
                f"The Drop ID `{drop_id}` is currently disabled.\n"
                f"Ask the recipient to enable it using `/enable_id`.",
                parse_mode="Markdown"
            )
            return

        if target_drop.is_expired():
            await message.answer(
                f"❌ **Drop ID has expired!**\n\n"
                f"The Drop ID `{drop_id}` has expired.\n"
                f"Ask the recipient to create a new one.",
                parse_mode="Markdown"
            )
            return

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
            # Disable the single-use Drop ID
            from database.connection import db
            await db.table('drop_ids')\
                .update({'is_active': False})\
                .eq('id', drop_id)\
                .execute()
            
            usage_note = "⚠️ This was a **single-use** Drop ID and has been automatically disabled."
        else:
            usage_note = "🔄 This Drop ID is still active and can receive more messages."

        # Send confirmation to sender
        confirmation_text = f"""
✅ **Message sent successfully!**

**To Drop ID:** `{drop_id}`
**Your Anonymous ID:** `{sender_anon_id}`
**Message:** {message_text}

{usage_note}

🔒 **Privacy Note:** Your identity is completely hidden from the recipient.
        """

        await message.answer(confirmation_text, parse_mode="Markdown")

        # Notify recipient (if we had their chat ID, we'd send a notification)
        # For now, we'll just log it - we'll add proper notifications later
        logger.info(f"Message sent to Drop ID {drop_id} from anonymous sender {sender_anon_id}")

    except Exception as e:
        logger.error(f"Error in send command: {e}")
        await message.answer(
            "❌ **Failed to send message.**\n\n"
            "Please try again later. If the problem persists, contact support.",
            parse_mode="Markdown"
        )