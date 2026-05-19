"""
bot.py
======
Entry point untuk Bot Asisten Telegram.
Menginisialisasi bot, mendaftarkan semua handler, dan menjalankan polling.
"""

import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Import konfigurasi
from config import config

# Import handler modules
from handlers.admin_handler import register_admin_handlers
from handlers.mod_handler import register_mod_handlers
from handlers.auto_mod import register_auto_mod_handlers

# Import database untuk memastikan inisialisasi
from database.db_manager import db

# Setup logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Set level logging untuk library httpx (digunakan oleh python-telegram-bot)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler untuk command /start.
    Menampilkan pesan sambutan dan informasi bot.
    """
    user = update.effective_user
    
    # Cek apakah user adalah Owner
    is_owner = user.id == config.OWNER_ID
    is_admin = db.is_admin(user.id)
    
    # Tentukan role user
    if is_owner:
        role = "Owner (Superadmin)"
    elif is_admin:
        role = "Admin"
    else:
        role = "Member"
    
    welcome_message = (
        f"👋 <b>Halo, {user.first_name}!</b>\n\n"
        f"Saya adalah Bot Asisten Grup dengan fitur moderasi otomatis.\n\n"
        f"<b>Role Anda:</b> {role}\n\n"
    )
    
    # Tambahkan daftar command sesuai role
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
    elif is_admin:
        welcome_message += (
            "<b>📋 Command Admin:</b>\n"
            "• /mute - Bisukan user (reply)\n"
            "• /unmute - Unmute user (reply)\n"
            "• /ban - Keluarkan user (reply)\n\n"
            "<b>🛡️ Auto-Moderation:</b>\n"
            "Bot otomatis menghapus link dari user non-admin."
        )
    else:
        welcome_message += (
            "<b>ℹ️ Info:</b>\n"
            "Bot ini digunakan untuk moderasi grup.\n"
            "Link otomatis akan dihapus jika Anda bukan admin.\n\n"
            "Hubungi admin grup jika butuh bantuan."
        )
    
    await update.message.reply_text(welcome_message, parse_mode='HTML')
    logger.info(f"User {user.id} (@{user.username}) started the bot")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler untuk command /help.
    Menampilkan bantuan dan daftar command.
    """
    user = update.effective_user
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
    
    await update.message.reply_text(help_text, parse_mode='HTML')


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler global untuk menangani error yang tidak tertangani.
    """
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Jika update adalah Update object dan ada message
    if isinstance(update, Update) and update.message:
        try:
            await update.message.reply_text(
                "❌ Terjadi error saat memproses permintaan Anda.\n"
                "Silakan coba lagi atau hubungi admin bot."
            )
        except Exception as e:
            logger.error(f"Error sending error message: {e}")


def main():
    """
    Fungsi utama untuk menjalankan bot.
    """
    logger.info("=" * 50)
    logger.info("Starting Bot Asisten Telegram")
    logger.info(f"Owner ID: {config.OWNER_ID}")
    logger.info(f"Database: {db.db_path}")
    logger.info(f"Registered admins: {db.get_admin_count()}")
    logger.info("=" * 50)
    
    try:
        # Buat Application instance
        application = Application.builder().token(config.BOT_TOKEN).build()
        
        # Daftarkan command dasar
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        
        # Daftarkan semua handler dari modules
        register_admin_handlers(application)
        register_mod_handlers(application)
        register_auto_mod_handlers(application)
        
        # Daftarkan error handler
        application.add_error_handler(error_handler)
        
        logger.info("All handlers registered successfully")
        logger.info("Bot is running... Press Ctrl+C to stop")
        
        # Jalankan bot dengan polling
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True  # Skip update yang tertunda saat bot mati
        )
    
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()