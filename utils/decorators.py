"""
utils/decorators.py
===================
Module berisi decorator untuk mengamankan command bot dengan sistem otorisasi.
Menggunakan functools.wraps untuk mempertahankan metadata function original.
"""

import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from config import config
from database.db_manager import db

# Setup logging
logger = logging.getLogger(__name__)


def owner_only(func):
    """
    Decorator untuk command yang HANYA bisa diakses oleh Owner/Superadmin.
    
    Usage:
        @owner_only
        async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
            ...
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        # Cek apakah user adalah Owner
        if user.id != config.OWNER_ID:
            logger.warning(
                f"Unauthorized access attempt to {func.__name__} by "
                f"user {user.id} (@{user.username})"
            )
            
            await update.message.reply_text(
                "❌ <b>Akses Ditolak</b>\n\n"
                "Command ini hanya bisa digunakan oleh Owner bot.",
                parse_mode='HTML'
            )
            return
        
        # Jika lolos pengecekan, jalankan function asli
        return await func(update, context)
    
    return wrapper


def admin_only(func):
    """
    Decorator untuk command yang bisa diakses oleh Owner dan Admin terdaftar.
    
    Usage:
        @admin_only
        async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
            ...
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        # Cek apakah user adalah Owner atau Admin terdaftar
        is_owner = user.id == config.OWNER_ID
        is_admin = db.is_admin(user.id)
        
        if not (is_owner or is_admin):
            logger.warning(
                f"Unauthorized access attempt to {func.__name__} by "
                f"user {user.id} (@{user.username})"
            )
            
            await update.message.reply_text(
                "❌ <b>Akses Ditolak</b>\n\n"
                "Command ini hanya bisa digunakan oleh Owner atau Admin bot.",
                parse_mode='HTML'
            )
            return
        
        # Jika lolos pengecekan, jalankan function asli
        return await func(update, context)
    
    return wrapper


def group_only(func):
    """
    Decorator untuk command yang hanya bisa digunakan di grup (bukan private chat).
    
    Usage:
        @group_only
        @admin_only
        async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
            ...
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        
        # Cek apakah pesan dikirim di grup
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text(
                "⚠️ Command ini hanya bisa digunakan di dalam grup.",
                parse_mode='HTML'
            )
            return
        
        # Jika di grup, jalankan function asli
        return await func(update, context)
    
    return wrapper


def require_reply(func):
    """
    Decorator untuk command yang memerlukan reply ke pesan user lain.
    
    Usage:
        @require_reply
        @admin_only
        async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
            ...
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.message
        
        # Cek apakah command ini adalah reply
        if not message.reply_to_message:
            await message.reply_text(
                "⚠️ Gunakan command ini dengan <b>reply</b> ke pesan user yang ingin dikenakan aksi.\n\n"
                "Contoh: Reply pesan user, lalu ketik command.",
                parse_mode='HTML'
            )
            return
        
        # Jika ada reply, jalankan function asli
        return await func(update, context)
    
    return wrapper