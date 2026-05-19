"""
handlers/auto_mod.py
====================
Module berisi handler untuk auto-moderation (deteksi link otomatis).
Menghapus pesan yang mengandung link dari user yang bukan Owner/Admin.
"""

import logging
import re
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from telegram.error import TelegramError

from config import config
from database.db_manager import db

# Setup logging
logger = logging.getLogger(__name__)

# Regex pattern untuk mendeteksi berbagai jenis link
LINK_PATTERNS = [
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',  # http/https links
    r'www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',  # www. links
    r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}\/[^\s]*',  # domain.com/path
    r't\.me/[a-zA-Z0-9_]+',  # Telegram links
]

# Compile regex untuk performa lebih baik
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in LINK_PATTERNS]


def contains_link(text: str) -> bool:
    """
    Mengecek apakah teks mengandung link.
    
    Args:
        text: Teks yang akan dicek
    
    Returns:
        True jika mengandung link, False jika tidak
    """
    if not text:
        return False
    
    for pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            return True
    
    return False


async def is_user_privileged(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Mengecek apakah user memiliki privilege (Owner/Admin bot/Admin grup).
    
    Args:
        update: Update object dari Telegram
        context: Context object
    
    Returns:
        True jika user memiliki privilege, False jika tidak
    """
    user = update.effective_user
    chat = update.effective_chat
    
    # Cek 1: Apakah user adalah Owner bot?
    if user.id == config.OWNER_ID:
        return True
    
    # Cek 2: Apakah user adalah Admin terdaftar di database?
    if db.is_admin(user.id):
        return True
    
    # Cek 3: Apakah user adalah Admin bawaan grup?
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in ['creator', 'administrator']:
            return True
    except TelegramError as e:
        logger.error(f"Error checking admin status: {e}")
    
    return False


async def auto_delete_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler untuk mendeteksi dan menghapus pesan yang mengandung link.
    Hanya berlaku untuk user yang bukan Owner/Admin.
    """
    message = update.message
    chat = update.effective_chat
    user = update.effective_user
    
    # Hanya proses pesan di grup
    if chat.type not in ['group', 'supergroup']:
        return
    
    # Cek apakah user memiliki privilege
    is_privileged = await is_user_privileged(update, context)
    
    if is_privileged:
        # User memiliki privilege, skip auto-moderation
        return
    
    # Ambil teks dari pesan (termasuk caption untuk media)
    text = message.text or message.caption or ""
    
    # Cek apakah teks mengandung link
    if contains_link(text):
        try:
            # Hapus pesan yang mengandung link
            await message.delete()
            
            # Kirim peringatan (akan terhapus otomatis setelah 10 detik)
            username = f"@{user.username}" if user.username else user.first_name
            warning_message = await context.bot.send_message(
                chat_id=chat.id,
                text=(
                    f"⚠️ <b>Link Terdeteksi</b>\n\n"
                    f"Pesan dari {username} dihapus karena mengandung link.\n"
                    f"Hanya admin yang boleh mengirim link di grup ini."
                ),
                parse_mode='HTML'
            )
            
            # Hapus peringatan setelah 10 detik
            await context.application.job_queue.run_once(
                callback=delete_warning_message,
                when=10,
                data={'chat_id': chat.id, 'message_id': warning_message.message_id}
            )
            
            logger.info(
                f"Link deleted from user {user.id} (@{user.username}) "
                f"in chat {chat.id}"
            )
        
        except TelegramError as e:
            logger.error(f"Error deleting message with link: {e}")


async def delete_warning_message(context: ContextTypes.DEFAULT_TYPE):
    """
    Callback untuk menghapus pesan peringatan setelah delay.
    
    Args:
        context: Context object yang berisi data pesan yang akan dihapus
    """
    job_data = context.job.data
    
    try:
        await context.bot.delete_message(
            chat_id=job_data['chat_id'],
            message_id=job_data['message_id']
        )
    except TelegramError as e:
        logger.error(f"Error deleting warning message: {e}")


# Fungsi untuk mendaftarkan handler auto-moderation ke aplikasi
def register_auto_mod_handlers(application):
    """
    Mendaftarkan message handler untuk auto-moderation.
    
    Args:
        application: Instance dari telegram.ext.Application
    """
    # Handler untuk semua pesan teks dan media dengan caption
    link_filter = (
        filters.TEXT | 
        filters.CAPTION
    ) & ~filters.COMMAND
    
    application.add_handler(
        MessageHandler(link_filter, auto_delete_links)
    )
    
    logger.info("Auto-moderation handlers registered successfully")