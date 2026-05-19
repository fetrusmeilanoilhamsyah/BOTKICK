"""
utils/helpers.py
================
Module berisi fungsi-fungsi utilitas (helper) yang dapat digunakan kembali
(reusable) oleh semua handler di seluruh proyek bot.

Fitur Utama:
    - delete_message_job     : Callback JobQueue untuk menghapus satu pesan.
    - auto_delete_reply      : Kirim balasan bot & jadwalkan penghapusannya otomatis.
    - clean_command          : Hapus pesan command yang dikirim admin secara instan.
    - send_and_auto_delete   : Gabungan all-in-one: hapus command + kirim balasan + jadwal hapus balasan.

Cara Pakai Cepat (di handler mana pun):
    from utils.helpers import send_and_auto_delete

    async def my_command(update, context):
        await send_and_auto_delete(
            update, context,
            text="✅ Aksi berhasil!",
            parse_mode='HTML',
            delay=10          # balasan bot dihapus setelah 10 detik (default)
        )
"""

import logging
from typing import Optional

from telegram import Message, Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest, Forbidden, TelegramError

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# KONSTANTA DEFAULT
# ──────────────────────────────────────────────

#: Delay default (detik) sebelum balasan bot dihapus otomatis.
DEFAULT_DELETE_DELAY: int = 10


# ──────────────────────────────────────────────
# 1. CALLBACK JOB – penghapus pesan tunggal
# ──────────────────────────────────────────────

async def delete_message_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Callback untuk JobQueue: menghapus satu pesan berdasarkan data yang disertakan.

    Data yang diharapkan di ``context.job.data``:
        {
            "chat_id"    : int,   # ID chat tempat pesan berada
            "message_id" : int,   # ID pesan yang akan dihapus
        }

    Penanganan Error:
        - BadRequest  : Pesan sudah terhapus atau tidak ditemukan → di-log, tidak crash.
        - Forbidden   : Bot tidak punya izin hapus → di-log, tidak crash.
        - TelegramError: Error lainnya → di-log, tidak crash.
    """
    job_data: dict = context.job.data
    chat_id: int = job_data["chat_id"]
    message_id: int = job_data["message_id"]

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.debug(
            f"[delete_message_job] Pesan {message_id} di chat {chat_id} berhasil dihapus."
        )

    except BadRequest as e:
        # Pesan sudah dihapus lebih dulu, atau message_id tidak valid → aman diabaikan
        logger.debug(
            f"[delete_message_job] Pesan {message_id} di chat {chat_id} "
            f"tidak bisa dihapus (mungkin sudah terhapus): {e}"
        )

    except Forbidden as e:
        # Bot tidak punya izin hapus pesan di chat tersebut
        logger.warning(
            f"[delete_message_job] Bot tidak punya izin hapus pesan "
            f"{message_id} di chat {chat_id}: {e}"
        )

    except TelegramError as e:
        # Error tak terduga lainnya dari Telegram API
        logger.error(
            f"[delete_message_job] TelegramError saat menghapus pesan "
            f"{message_id} di chat {chat_id}: {e}"
        )


# ──────────────────────────────────────────────
# 2. HAPUS COMMAND INSTAN
# ──────────────────────────────────────────────

async def clean_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Menghapus pesan command yang dikirim oleh admin secara instan.

    Fungsi ini aman dipanggil kapan saja; jika penghapusan gagal (misalnya
    bot tidak punya izin ``delete_messages``), error akan di-log dan eksekusi
    handler tetap berlanjut tanpa crash.

    Args:
        update  : Update object dari Telegram.
        context : Context object dari handler.

    Contoh::

        async def mute_command(update, context):
            await clean_command(update, context)   # hapus /mute dari chat
            # ... logika mute ...
    """
    message: Optional[Message] = update.message
    if not message:
        return

    try:
        await message.delete()
        logger.debug(
            f"[clean_command] Pesan command {message.message_id} "
            f"di chat {message.chat_id} berhasil dihapus."
        )

    except BadRequest as e:
        logger.debug(
            f"[clean_command] Gagal hapus command {message.message_id} "
            f"(mungkin sudah terhapus): {e}"
        )

    except Forbidden as e:
        logger.warning(
            f"[clean_command] Bot tidak punya izin hapus command "
            f"{message.message_id} di chat {message.chat_id}: {e}"
        )

    except TelegramError as e:
        logger.error(
            f"[clean_command] TelegramError saat menghapus command "
            f"{message.message_id}: {e}"
        )


# ──────────────────────────────────────────────
# 3. KIRIM BALASAN + JADWALKAN PENGHAPUSANNYA
# ──────────────────────────────────────────────

async def auto_delete_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    delay: int = DEFAULT_DELETE_DELAY,
    parse_mode: Optional[str] = "HTML",
    **reply_kwargs,
) -> Optional[Message]:
    """
    Mengirim pesan teks ke chat dan menjadwalkan penghapusan otomatis via JobQueue.

    CATATAN PENTING: Fungsi ini menggunakan ``send_message`` (bukan ``reply_text``)
    agar tetap berfungsi meskipun pesan command asli sudah dihapus sebelumnya
    oleh ``clean_command``. Ini menghindari error "Message to be replied not found".

    Args:
        update      : Update object dari Telegram.
        context     : Context object dari handler.
        text        : Teks pesan balasan yang akan dikirim.
        delay       : Waktu (detik) sebelum balasan dihapus. Default: 10 detik.
        parse_mode  : Mode parsing teks ('HTML', 'Markdown', dll). Default: 'HTML'.
        **reply_kwargs : Argumen tambahan yang diteruskan ke ``send_message()``.
                         Contoh: ``disable_web_page_preview=True``.

    Returns:
        Message | None : Objek pesan yang dikirim, atau None jika gagal.

    Contoh::

        reply_msg = await auto_delete_reply(
            update, context,
            text="✅ <b>User berhasil di-mute!</b>",
            delay=15,
        )
    """
    message: Optional[Message] = update.message
    if not message:
        return None

    sent_message: Optional[Message] = None

    try:
        # Gunakan send_message (bukan reply_text) agar tidak crash
        # jika pesan command sudah dihapus lebih dulu oleh clean_command.
        sent_message = await context.bot.send_message(
            chat_id=message.chat_id,
            text=text,
            parse_mode=parse_mode,
            **reply_kwargs,
        )
        logger.debug(
            f"[auto_delete_reply] Pesan terkirim (ID: {sent_message.message_id}) "
            f"di chat {message.chat_id}, akan dihapus dalam {delay} detik."
        )

    except TelegramError as e:
        logger.error(f"[auto_delete_reply] Gagal mengirim pesan: {e}")
        return None

    # Jadwalkan penghapusan pesan via JobQueue
    try:
        context.application.job_queue.run_once(
            callback=delete_message_job,
            when=delay,
            data={
                "chat_id": message.chat_id,
                "message_id": sent_message.message_id,
            },
            name=f"del_{message.chat_id}_{sent_message.message_id}",
        )
    except Exception as e:
        # JobQueue mungkin tidak tersedia (misal: saat testing tanpa scheduler)
        logger.warning(f"[auto_delete_reply] Gagal menjadwalkan penghapusan: {e}")

    return sent_message


# ──────────────────────────────────────────────
# 4. ALL-IN-ONE: hapus command + kirim + jadwal hapus
# ──────────────────────────────────────────────

async def send_and_auto_delete(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    delay: int = DEFAULT_DELETE_DELAY,
    parse_mode: Optional[str] = "HTML",
    delete_command: bool = True,
    **reply_kwargs,
) -> Optional[Message]:
    """
    Fungsi utilitas all-in-one yang menggabungkan tiga aksi sekaligus:
        1. Kirim pesan balasan bot ke chat.
        2. Hapus pesan command admin secara instan (opsional).
        3. Jadwalkan penghapusan otomatis balasan via JobQueue.

    URUTAN PENTING: Balasan dikirim DULU, BARU command dihapus.
    Ini mencegah error "Message to be replied not found" yang terjadi
    jika command dihapus sebelum balasan sempat dikirim.

    Ini adalah fungsi yang direkomendasikan untuk digunakan di semua handler
    command admin agar kode tetap DRY (Don't Repeat Yourself).

    Args:
        update          : Update object dari Telegram.
        context         : Context object dari handler.
        text            : Teks pesan balasan yang akan dikirim.
        delay           : Waktu (detik) sebelum balasan dihapus. Default: 10 detik.
        parse_mode      : Mode parsing teks. Default: 'HTML'.
        delete_command  : Jika True, hapus pesan command admin. Default: True.
        **reply_kwargs  : Argumen tambahan untuk ``send_message()``.

    Returns:
        Message | None : Objek pesan balasan yang terkirim, atau None jika gagal.

    Contoh penggunaan di handler::

        from utils.helpers import send_and_auto_delete

        @admin_only
        @group_only
        @require_reply
        async def mute_command(update, context):
            # ... logika mute ...

            await send_and_auto_delete(
                update, context,
                text=f"🔇 <b>User berhasil di-mute!</b>\\n\\nDurasi: {duration_text}",
                delay=10,
            )

        # Untuk error / validasi (tidak perlu hapus command):
        async def some_command(update, context):
            if not context.args:
                await send_and_auto_delete(
                    update, context,
                    text="❌ Format salah!",
                    delete_command=False,  # jangan hapus command jika ada error input
                    delay=8,
                )
                return
    """
    # Langkah 1: Kirim balasan DULU (sebelum command dihapus)
    # Menggunakan send_message agar tidak bergantung pada keberadaan pesan asli.
    sent = await auto_delete_reply(
        update,
        context,
        text=text,
        delay=delay,
        parse_mode=parse_mode,
        **reply_kwargs,
    )
