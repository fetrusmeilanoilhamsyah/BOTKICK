"""
handlers/mod_handler.py
=======================
Module berisi handler untuk command moderasi grup.
Command ini bisa diakses oleh Owner dan Admin terdaftar.
"""

import logging
from datetime import datetime, timedelta, timezone
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, CommandHandler
from telegram.error import TelegramError

from utils.decorators import admin_only, group_only, require_reply

# Setup logging
logger = logging.getLogger(__name__)


@admin_only
@group_only
@require_reply
async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command /mute untuk membisukan user di grup.
    User tidak bisa mengirim pesan, tetapi tetap bisa melihat grup.
    """
    message = update.message
    chat = update.effective_chat
    admin_user = update.effective_user
    target_user = message.reply_to_message.from_user
    
    # Cegah mute diri sendiri
    if target_user.id == admin_user.id:
        await message.reply_text("⚠️ Anda tidak bisa mute diri sendiri!")
        return
    
    # Cegah mute bot
    bot = await context.bot.get_me()
    if target_user.id == bot.id:
        await message.reply_text("⚠️ Bot tidak bisa di-mute!")
        return
    
    # Parse durasi mute (opsional)
    until_date = None
    duration_text = "permanen"
    
    if context.args:
        try:
            duration_str = context.args[0].lower()
            
            # Menggunakan timezone.utc untuk konsistensi dengan server Telegram
            now = datetime.now(timezone.utc)
            
            # Parse durasi: angka + satuan (m/h/d)
            if duration_str.endswith('m'):
                minutes = int(duration_str[:-1])
                until_date = now + timedelta(minutes=minutes)
                duration_text = f"{minutes} menit"
            
            elif duration_str.endswith('h'):
                hours = int(duration_str[:-1])
                until_date = now + timedelta(hours=hours)
                duration_text = f"{hours} jam"
            
            elif duration_str.endswith('d'):
                days = int(duration_str[:-1])
                until_date = now + timedelta(days=days)
                duration_text = f"{days} hari"
            
            else:
                await message.reply_text(
                    "❌ <b>Format durasi salah!</b>\n\n"
                    "Gunakan:\n"
                    "• <code>5m</code> = 5 menit\n"
                    "• <code>2h</code> = 2 jam\n"
                    "• <code>1d</code> = 1 hari\n"
                    "• Tanpa argumen = mute permanen",
                    parse_mode='HTML'
                )
                return
        
        except (ValueError, IndexError):
            await message.reply_text(
                "❌ <b>Format durasi salah!</b>\n\n"
                "Contoh: <code>/mute 5m</code> atau <code>/mute 2h</code>",
                parse_mode='HTML'
            )
            return
    
    # Permissions untuk user yang di-mute
    muted_permissions = ChatPermissions(
        can_send_messages=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False,
        can_change_info=False,
        can_invite_users=False,
        can_pin_messages=False
    )
    
    try:
        # Restrict user
        await context.bot.restrict_chat_member(
            chat_id=chat.id,
            user_id=target_user.id,
            permissions=muted_permissions,
            until_date=until_date
        )
        
        username = f"@{target_user.username}" if target_user.username else target_user.first_name
        
        await message.reply_text(
            f"🔇 <b>User berhasil di-mute!</b>\n\n"
            f"User: {username}\n"
            f"User ID: <code>{target_user.id}</code>\n"
            f"Durasi: {duration_text}\n"
            f"Oleh: @{admin_user.username}",
            parse_mode='HTML'
        )
        
        logger.info(
            f"User {target_user.id} muted in chat {chat.id} "
            f"by admin {admin_user.id} for {duration_text}"
        )
    
    except TelegramError as e:
        await message.reply_text(
            f"❌ <b>Gagal mute user!</b>\n\n"
            f"Error: {str(e)}\n\n"
            f"Pastikan bot memiliki hak admin di grup ini.",
            parse_mode='HTML'
        )
        logger.error(f"Error muting user: {e}")


@admin_only
@group_only
@require_reply
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /ban untuk mengeluarkan (kick) user dari grup."""
    message = update.message
    chat = update.effective_chat
    admin_user = update.effective_user
    target_user = message.reply_to_message.from_user
    
    if target_user.id == admin_user.id:
        await message.reply_text("⚠️ Anda tidak bisa ban diri sendiri!")
        return
    
    bot = await context.bot.get_me()
    if target_user.id == bot.id:
        await message.reply_text("⚠️ Bot tidak bisa di-ban!")
        return
    
    try:
        await context.bot.ban_chat_member(chat_id=chat.id, user_id=target_user.id)
        
        await context.bot.unban_chat_member(
            chat_id=chat.id,
            user_id=target_user.id,
            only_if_banned=True
        )
        
        username = f"@{target_user.username}" if target_user.username else target_user.first_name
        
        await message.reply_text(
            f"🚫 <b>User berhasil di-ban!</b>\n\n"
            f"User: {username}\n"
            f"User ID: <code>{target_user.id}</code>\n"
            f"Oleh: @{admin_user.username}\n\n"
            f"User bisa join kembali jika memiliki invite link.",
            parse_mode='HTML'
        )
        
        logger.info(f"User {target_user.id} banned from chat {chat.id} by admin {admin_user.id}")
    
    except TelegramError as e:
        await message.reply_text(
            f"❌ <b>Gagal ban user!</b>\n\n"
            f"Error: {str(e)}\n\n"
            f"Pastikan bot memiliki hak admin di grup ini.",
            parse_mode='HTML'
        )
        logger.error(f"Error banning user: {e}")


@admin_only
@group_only
@require_reply
async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /unmute untuk membuka mute user."""
    message = update.message
    chat = update.effective_chat
    admin_user = update.effective_user
    target_user = message.reply_to_message.from_user
    
    # Permissions normal
    normal_permissions = ChatPermissions(
        can_send_messages=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_change_info=False,
        can_invite_users=True,
        can_pin_messages=False
    )
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat.id,
            user_id=target_user.id,
            permissions=normal_permissions
        )
        
        username = f"@{target_user.username}" if target_user.username else target_user.first_name
        
        await message.reply_text(
            f"🔊 <b>User berhasil di-unmute!</b>\n\n"
            f"User: {username}\n"
            f"User ID: <code>{target_user.id}</code>\n"
            f"Oleh: @{admin_user.username}",
            parse_mode='HTML'
        )
        
        logger.info(f"User {target_user.id} unmuted in chat {chat.id} by admin {admin_user.id}")
    
    except TelegramError as e:
        await message.reply_text(
            f"❌ <b>Gagal unmute user!</b>\n\n"
            f"Error: {str(e)}",
            parse_mode='HTML'
        )
        logger.error(f"Error unmuting user: {e}")


def register_mod_handlers(application):
    """Mendaftarkan semua command handler untuk moderasi grup."""
    application.add_handler(CommandHandler("mute", mute_command))
    application.add_handler(CommandHandler("unmute", unmute_command))
    application.add_handler(CommandHandler("ban", ban_command))
    
    logger.info("Moderation handlers registered successfully")