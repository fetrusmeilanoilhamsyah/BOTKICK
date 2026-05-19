"""
bot.py
======
Entry point untuk Bot Asisten Telegram.
Menginisialisasi bot, mendaftarkan semua handler, dan menjalankan polling.

Refactoring:
    - /start dan /help di grup kini menggunakan send_and_auto_delete agar
      balasan bot terhapus otomatis dan chat tetap bersih.
    - /start dan /help di private chat tetap menggunakan reply_text biasa
      (tidak perlu dihapus karena bukan grup).
    - error_handler global ditingkatkan penanganannya.
"""

import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError

# Import konfigurasi
from config import config

# Import handler modules
from handlers.admin_handler import register_admin_handlers
from handlers.mod_handler import register_mod_handlers
from handlers.auto_mod import register_auto_mod_handlers

# Import helpers
from utils.helpers import send_and_auto_delete

# Import database
from database.db_manager import db

# ──────────────────────────────────────────────
# SETUP LOGGING
# ──────────────────────────────────────────────

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Kurangi noise dari library internal
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# COMMAND DASAR
# ──────────────────────────────────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler untuk command /start.
    Hanya bisa diakses oleh Owner dan Admin terdaftar.

    - Member biasa: command dihapus senyap di grup / pesan penolakan di private.
    - Di grup (owner/admin): balasan auto-delete setelah 20 detik.
    - Di private (owner/admin): balasan permanen.
    """
    user = update.effective_user
    chat = update.effective_chat

    is_owner = user.id == config.OWNER_ID
    is_admin = db.is_admin(user.id)

    # ── Tolak akses member biasa ──
    if not (is_owner or is_admin):
        logger.warning(
            f"[start_command] Akses ditolak — user {user.id} "
            f"(@{user.username}) bukan owner/admin."
        )
        if chat.type in ['group', 'supergroup']:
            # Hapus command secara senyap, tidak beri respons
            try:
                await update.message.delete()
            except Exception:
                pass
        else:
            # Private chat: beri tahu singkat
            await update.message.reply_text(
                "🔒 <b>Akses Terbatas</b>\n\n"
                "Command ini hanya dapat digunakan oleh "
                "<b>Owner</b> dan <b>Admin</b> bot.",
                parse_mode='HTML'
            )
        return

    if is_owner:
        role = "👑 Owner (Superadmin)"
    else:
        role = "🛡️ Admin"

    welcome_message = (
        f"👋 <b>Halo, {user.first_name}!</b>\n\n"
        f"Saya adalah Bot Asisten Grup dengan fitur moderasi otomatis.\n\n"
        f"<b>Role Anda:</b> {role}\n\n"
    )

    if is_owner:
        welcome_message += (
            "<b>📋 Command Owner:</b>\n"
            "• /addadmin - Tambah admin baru\n"
            "• /deladmin - Hapus admin\n"
            "• /listadmin - Lihat daftar admin\n"
            "• /mute - Bisukan user (reply)\n"
            "• /unmute - Unmute user (reply)\n"
            "• /ban - Keluarkan user (reply)\n\n"
            "<b>🛡️ Auto-Moderation:</b>\n"
            "Bot otomatis menghapus link dari user non-admin.\n\n"
            "<b>⚙️ Status Database:</b>\n"
            f"Admin terdaftar: {db.get_admin_count()} user"
        )
    else:
        welcome_message += (
            "<b>📋 Command Admin:</b>\n"
            "• /mute - Bisukan user (reply)\n"
            "• /unmute - Unmute user (reply)\n"
            "• /ban - Keluarkan user (reply)\n\n"
            "<b>🛡️ Auto-Moderation:</b>\n"
            "Bot otomatis menghapus link dari user non-admin."
        )

    # ── Kirim respons sesuai konteks chat ──
    if chat.type in ['group', 'supergroup']:
        await send_and_auto_delete(
            update, context,
            text=welcome_message,
            delay=10,
            delete_command=True,
        )
    else:
        await update.message.reply_text(welcome_message, parse_mode='HTML')

    logger.info(f"[start_command] User {user.id} (@{user.username}) menjalankan /start")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler untuk command /help.
    - Di grup: balasan dihapus otomatis setelah 20 detik & command dihapus.
    - Di private chat: balasan permanen (tidak dihapus).
    """
    user = update.effective_user
    chat = update.effective_chat

    is_owner = user.id == config.OWNER_ID
    is_admin = db.is_admin(user.id)

    help_text = "<b>📖 Bantuan Bot Asisten Grup</b>\n\n"

    if is_owner:
        help_text += (
            "<b>Command Owner:</b>\n"
            "• <code>/addadmin &lt;user_id&gt;</code> atau reply + <code>/addadmin</code>\n"
            "  └ Tambah admin baru ke database\n\n"
            "• <code>/deladmin &lt;user_id&gt;</code> atau reply + <code>/deladmin</code>\n"
            "  └ Hapus admin dari database\n\n"
            "• <code>/listadmin</code>\n"
            "  └ Tampilkan daftar semua admin\n\n"
            "<b>Command Moderasi:</b>\n"
            "• Reply pesan + <code>/mute [durasi]</code>\n"
            "  └ Bisukan user (contoh: 5m, 2h, 1d)\n\n"
            "• Reply pesan + <code>/unmute</code>\n"
            "  └ Buka mute user\n\n"
            "• Reply pesan + <code>/ban</code>\n"
            "  └ Keluarkan user dari grup\n\n"
            "<b>Fitur Auto-Moderation:</b>\n"
            "Bot otomatis mendeteksi dan menghapus pesan berisi link dari user non-admin."
        )
    elif is_admin:
        help_text += (
            "<b>Command Moderasi:</b>\n"
            "• Reply pesan + <code>/mute [durasi]</code>\n"
            "  └ Bisukan user (contoh: 5m, 2h, 1d)\n\n"
            "• Reply pesan + <code>/unmute</code>\n"
            "  └ Buka mute user\n\n"
            "• Reply pesan + <code>/ban</code>\n"
            "  └ Keluarkan user dari grup\n\n"
            "<b>Fitur Auto-Moderation:</b>\n"
            "Bot otomatis mendeteksi dan menghapus pesan berisi link dari user non-admin."
        )
    else:
        help_text += (
            "Anda tidak memiliki akses ke command admin.\n\n"
            "<b>Peraturan Grup:</b>\n"
            "• Link otomatis akan dihapus jika Anda bukan admin\n"
            "• Ikuti peraturan grup yang telah ditetapkan\n\n"
            "Hubungi admin grup jika butuh bantuan."
        )

    # Di grup: hapus command + auto-delete balasan setelah 20 detik
    if chat.type in ['group', 'supergroup']:
        await send_and_auto_delete(
            update, context,
            text=help_text,
            delay=10,
            delete_command=True,
        )
    else:
        # Di private chat: balasan permanen
        await update.message.reply_text(help_text, parse_mode='HTML')

    logger.info(f"User {user.id} (@{user.username}) menjalankan /help")


# ──────────────────────────────────────────────
# GLOBAL ERROR HANDLER
# ──────────────────────────────────────────────

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler global untuk menangani error yang tidak tertangani oleh handler lain.
    Mencatat error ke log dan mengirim notifikasi singkat ke user jika memungkinkan.
    """
    logger.error(
        f"[error_handler] Exception saat memproses update: {context.error}",
        exc_info=context.error
    )

    # Hanya kirim notifikasi jika ada update dengan pesan
    if not isinstance(update, Update) or not update.message:
        return

    # Jangan kirim notifikasi untuk error permission yang sudah ditangani helper
    if isinstance(context.error, TelegramError):
        logger.warning(
            f"[error_handler] TelegramError tidak tertangani: {context.error}"
        )

    try:
        await update.message.reply_text(
            "❌ <b>Terjadi kesalahan</b>\n\n"
            "Ada error saat memproses permintaan Anda.\n"
            "Silakan coba lagi atau hubungi admin bot.",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"[error_handler] Gagal mengirim pesan error ke user: {e}")


# ──────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────

def main():
    """
    Fungsi utama untuk menjalankan bot.
    Menginisialisasi Application, mendaftarkan handler, lalu mulai polling.
    """
    logger.info("=" * 50)
    logger.info("Starting Bot Asisten Telegram")
    logger.info(f"Owner ID    : {config.OWNER_ID}")
    logger.info(f"Database    : {db.db_path}")
    logger.info(f"Total Admin : {db.get_admin_count()} user")
    logger.info("=" * 50)

    try:
        # Bangun Application — JobQueue aktif secara default di ptb v20+
        application = Application.builder().token(config.BOT_TOKEN).build()

        # ── Command dasar ──
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))

        # ── Handler dari module terpisah ──
        register_admin_handlers(application)
        register_mod_handlers(application)
        register_auto_mod_handlers(application)

        # ── Global error handler ──
        application.add_error_handler(error_handler)

        logger.info("Semua handler berhasil didaftarkan.")
        logger.info("Bot berjalan... Tekan Ctrl+C untuk berhenti.")

        # Jalankan bot dengan polling
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True  # Abaikan update yang tertunda saat bot mati
        )

    except KeyboardInterrupt:
        logger.info("Bot dihentikan oleh user (KeyboardInterrupt).")

    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
