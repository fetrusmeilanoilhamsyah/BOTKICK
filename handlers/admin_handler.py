"""
handlers/admin_handler.py
=========================
Module berisi handler untuk command manajemen admin.
Command ini HANYA bisa diakses oleh Owner bot.

Refactoring: Semua pesan command dan balasan bot kini dihapus otomatis
menggunakan `send_and_auto_delete` dari utils.helpers.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from config import config
from utils.decorators import owner_only
from utils.helpers import send_and_auto_delete
from database.db_manager import db

# Setup logging
logger = logging.getLogger(__name__)


@owner_only
async def add_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command /addadmin untuk menambahkan admin baru ke database.

    Usage:
        /addadmin <user_id>             - Tambah admin dengan User ID
        Reply ke pesan user + /addadmin - Tambah admin via reply
    """
    message = update.message

    # ── Cara 1: Via reply ke pesan user ──
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        user_id = target_user.id
        username = target_user.username

    # ── Cara 2: Via argumen <user_id> ──
    elif context.args:
        try:
            user_id = int(context.args[0])
            username = None  # Username tidak diketahui jika via ID manual
        except (ValueError, IndexError):
            await send_and_auto_delete(
                update, context,
                text=(
                    "❌ <b>Format salah!</b>\n\n"
                    "Gunakan:\n"
                    "• <code>/addadmin &lt;user_id&gt;</code>\n"
                    "• Reply pesan user + <code>/addadmin</code>"
                ),
                delay=10,
                delete_command=False,
            )
            return

    # ── Tidak ada reply dan tidak ada argumen ──
    else:
        await send_and_auto_delete(
            update, context,
            text=(
                "❌ <b>Format salah!</b>\n\n"
                "Gunakan:\n"
                "• <code>/addadmin &lt;user_id&gt;</code>\n"
                "• Reply pesan user + <code>/addadmin</code>"
            ),
            delay=10,
            delete_command=False,
        )
        return

    # ── Cegah Owner menambahkan dirinya sendiri ──
    if user_id == config.OWNER_ID:
        await send_and_auto_delete(
            update, context,
            text="⚠️ Anda adalah Owner bot, tidak perlu ditambahkan sebagai admin.",
            delay=10,
            delete_command=True,
        )
        return

    # ── Tambahkan admin ke database ──
    success = db.add_admin(user_id, username)

    if success:
        username_display = f"@{username}" if username else f"ID: {user_id}"
        await send_and_auto_delete(
            update, context,
            text=(
                f"✅ <b>Admin berhasil ditambahkan!</b>\n\n"
                f"User: {username_display}\n"
                f"User ID: <code>{user_id}</code>"
            ),
            delay=10,
            delete_command=True,
        )
        logger.info(f"Owner added new admin: {user_id} (@{username})")
    else:
        await send_and_auto_delete(
            update, context,
            text=(
                f"⚠️ <b>Admin sudah terdaftar</b>\n\n"
                f"User ID <code>{user_id}</code> sudah ada di database."
            ),
            delay=10,
            delete_command=True,
        )


@owner_only
async def remove_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command /deladmin untuk menghapus admin dari database.

    Usage:
        /deladmin <user_id>             - Hapus admin dengan User ID
        Reply ke pesan user + /deladmin - Hapus admin via reply
    """
    message = update.message

    # ── Cara 1: Via reply ke pesan user ──
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        user_id = target_user.id

    # ── Cara 2: Via argumen <user_id> ──
    elif context.args:
        try:
            user_id = int(context.args[0])
        except (ValueError, IndexError):
            await send_and_auto_delete(
                update, context,
                text=(
                    "❌ <b>Format salah!</b>\n\n"
                    "Gunakan:\n"
                    "• <code>/deladmin &lt;user_id&gt;</code>\n"
                    "• Reply pesan user + <code>/deladmin</code>"
                ),
                delay=10,
                delete_command=False,
            )
            return

    # ── Tidak ada reply dan tidak ada argumen ──
    else:
        await send_and_auto_delete(
            update, context,
            text=(
                "❌ <b>Format salah!</b>\n\n"
                "Gunakan:\n"
                "• <code>/deladmin &lt;user_id&gt;</code>\n"
                "• Reply pesan user + <code>/deladmin</code>"
            ),
            delay=10,
            delete_command=False,
        )
        return

    # ── Hapus admin dari database ──
    success = db.remove_admin(user_id)

    if success:
        await send_and_auto_delete(
            update, context,
            text=(
                f"✅ <b>Admin berhasil dihapus!</b>\n\n"
                f"User ID: <code>{user_id}</code>"
            ),
            delay=10,
            delete_command=True,
        )
        logger.info(f"Owner removed admin: {user_id}")
    else:
        await send_and_auto_delete(
            update, context,
            text=(
                f"⚠️ <b>Admin tidak ditemukan</b>\n\n"
                f"User ID <code>{user_id}</code> tidak ada di database."
            ),
            delay=10,
            delete_command=True,
        )


@owner_only
async def list_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command /listadmin untuk menampilkan daftar admin terdaftar.
    Balasan dihapus otomatis setelah 30 detik (lebih lama karena berisi info penting).
    """
    # ── Ambil semua admin dari database ──
    admins = db.get_all_admins()

    if not admins:
        await send_and_auto_delete(
            update, context,
            text=(
                "📋 <b>Daftar Admin</b>\n\n"
                "Belum ada admin yang terdaftar di database."
            ),
            delay=10,
            delete_command=True,
        )
        return

    # ── Format daftar admin ──
    admin_list = []
    for idx, admin in enumerate(admins, 1):
        username = f"@{admin['username']}" if admin['username'] else "N/A"
        added_at = admin['added_at'].split('.')[0]  # Hapus milidetik

        admin_list.append(
            f"{idx}. <b>User ID:</b> <code>{admin['user_id']}</code>\n"
            f"   <b>Username:</b> {username}\n"
            f"   <b>Ditambahkan:</b> {added_at}"
        )

    response = (
        f"📋 <b>Daftar Admin Terdaftar</b>\n"
        f"Total: {len(admins)} admin\n\n"
        + "\n\n".join(admin_list)
    )

    # Delay lebih panjang (30 detik) karena info penting perlu sempat dibaca
    await send_and_auto_delete(
        update, context,
        text=response,
        delay=10,
        delete_command=True,
    )
    logger.info(f"Owner viewed admin list: {len(admins)} admins")


def register_admin_handlers(application):
    """
    Mendaftarkan semua command handler untuk manajemen admin.

    Args:
        application: Instance dari telegram.ext.Application
    """
    application.add_handler(CommandHandler("addadmin", add_admin_command))
    application.add_handler(CommandHandler("deladmin", remove_admin_command))
    application.add_handler(CommandHandler("listadmin", list_admin_command))

    logger.info("Admin handlers registered successfully")
