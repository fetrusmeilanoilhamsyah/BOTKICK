"""
handlers/auto_mod.py
====================
Module berisi handler untuk auto-moderation (deteksi link otomatis).
Menghapus pesan yang mengandung link dari user yang bukan Owner/Admin.

Refactoring: Menggunakan `delete_message_job` dari utils.helpers agar
callback penghapusan pesan peringatan konsisten dengan seluruh sistem.
"""

import logging
import re
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from telegram.error import BadRequest, Forbidden, TelegramError

from config import config
from database.db_manager import db
from utils.helpers import delete_message_job

# Setup logging
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# KONSTANTA
# ──────────────────────────────────────────────

#: Delay (detik) sebelum pesan peringatan link dihapus.
WARNING_DELETE_DELAY: int = 10

# Regex pattern untuk mendeteksi berbagai jenis link
LINK_PATTERNS = [
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',  # http/https
    r'www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',        # www.
    r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}\/[^\s]*',         # domain.com/path
    r't\.me/[a-zA-Z0-9_]+',                                                                    # Telegram links
]

# Compile regex untuk performa lebih baik
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in LINK_PATTERNS]


# ──────────────────────────────────────────────
# FUNGSI UTILITAS LOKAL
# ──────────────────────────────────────────────

def contains_link(text: str) -> bool:
    """
    Mengecek apakah teks mengandung link.

    Args:
        text: Teks yang akan dicek.

    Returns:
        True jika mengandung link, False jika tidak.
    """
    if not text:
        return False

    for pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            return True

    return False


async def is_user_privileged(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Mengecek apakah user memiliki privilege (Owner / Admin bot / Admin grup Telegram).

    Urutan pengecekan (dari paling cepat ke paling lambat):
        1. Owner bot (cek lokal, instan)
        2. Admin terdaftar di database (cek lokal, instan)
        3. Admin bawaan grup Telegram (API call, sedikit lebih lambat)

    Args:
        update  : Update object dari Telegram.
        context : Context object.

    Returns:
        True jika user memiliki privilege, False jika tidak.
    """
    user = update.effective_user
    chat = update.effective_chat

    # Cek 1: Owner bot
    if user.id == config.OWNER_ID:
        return True

    # Cek 2: Admin terdaftar di database
    if db.is_admin(user.id):
        return True

    # Cek 3: Admin bawaan grup (creator / administrator)
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in ['creator', 'administrator']:
            return True
    except TelegramError as e:
        logger.error(f"[is_user_privileged] Error saat cek status admin: {e}")

    return False


# ──────────────────────────────────────────────
# HANDLER UTAMA
# ──────────────────────────────────────────────

async def auto_delete_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler untuk mendeteksi dan menghapus pesan yang mengandung link.
    Hanya berlaku untuk user yang bukan Owner / Admin.

    Alur:
        1. Abaikan pesan di luar grup.
        2. Abaikan jika pengirim memiliki privilege.
        3. Hapus pesan jika mengandung link.
        4. Kirim peringatan ke grup.
        5. Jadwalkan penghapusan peringatan via JobQueue (reuse delete_message_job).
    """
    message = update.message
    chat = update.effective_chat
    user = update.effective_user

    # Hanya proses pesan di grup / supergroup
    if chat.type not in ['group', 'supergroup']:
        return

    # Lewati jika user memiliki privilege
    if await is_user_privileged(update, context):
        return

    # Ambil teks dari pesan (termasuk caption untuk media)
    text = message.text or message.caption or ""

    if not contains_link(text):
        return

    # ── Hapus pesan yang mengandung link ──
    try:
        await message.delete()
    except BadRequest as e:
        logger.debug(f"[auto_delete_links] Pesan sudah terhapus atau tidak ditemukan: {e}")
        return
    except Forbidden as e:
        logger.warning(f"[auto_delete_links] Bot tidak punya izin hapus pesan: {e}")
        return
    except TelegramError as e:
        logger.error(f"[auto_delete_links] Gagal menghapus pesan link: {e}")
        return

    # ── Kirim peringatan ke grup ──
    username = f"@{user.username}" if user.username else user.first_name
    try:
        warning_msg = await context.bot.send_message(
            chat_id=chat.id,
            text=(
                f"⚠️ <b>Link Terdeteksi</b>\n\n"
                f"Pesan dari {username} dihapus karena mengandung link.\n"
                f"Hanya admin yang boleh mengirim link di grup ini."
            ),
            parse_mode='HTML'
        )
    except TelegramError as e:
        logger.error(f"[auto_delete_links] Gagal mengirim peringatan: {e}")
        return

    # ── Jadwalkan penghapusan peringatan via JobQueue (reuse helper) ──
    try:
        context.application.job_queue.run_once(
            callback=delete_message_job,
            when=WARNING_DELETE_DELAY,
            data={
                "chat_id": chat.id,
                "message_id": warning_msg.message_id,
            },
            name=f"automod_warn_{chat.id}_{warning_msg.message_id}",
        )
    except Exception as e:
        logger.warning(f"[auto_delete_links] Gagal menjadwalkan hapus peringatan: {e}")

    logger.info(
        f"[auto_delete_links] Link dihapus dari user {user.id} (@{user.username}) "
        f"di chat {chat.id}"
    )


# ──────────────────────────────────────────────
# REGISTRASI HANDLER
# ──────────────────────────────────────────────

def register_auto_mod_handlers(application):
    """
    Mendaftarkan message handler untuk auto-moderation.

    Args:
        application: Instance dari telegram.ext.Application
    """
    # Filter: pesan teks ATAU media dengan caption, tapi bukan command
    link_filter = (filters.TEXT | filters.CAPTION) & ~filters.COMMAND

    application.add_handler(
        MessageHandler(link_filter, auto_delete_links)
    )

    logger.info("Auto-moderation handlers registered successfully")