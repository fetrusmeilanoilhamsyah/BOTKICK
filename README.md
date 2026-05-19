# 🤖 Bot Asisten Grup Telegram

Bot Telegram yang aman, modular, dan scalable untuk moderasi grup dengan sistem otorisasi berjenjang (Owner & Admin) dan fitur auto-moderation.

## ✨ Fitur Utama

### 🔐 Sistem Otorisasi Berjenjang
- **Owner (Superadmin)**: Kontrol penuh atas bot dan manajemen admin
- **Admin**: Dapat melakukan moderasi grup
- **Database SQLite**: Penyimpanan data admin yang aman dan terlindungi dari corrupt

### 👥 Manajemen Admin (Khusus Owner)
- `/addadmin <user_id>` - Tambah admin baru (via ID atau reply)
- `/deladmin <user_id>` - Hapus admin dari database
- `/listadmin` - Tampilkan daftar admin terdaftar

### 🛡️ Fitur Moderasi (Owner & Admin)
- `/mute [durasi]` - Bisukan user (5m, 2h, 1d, atau permanen)
- `/unmute` - Buka mute user
- `/ban` - Keluarkan user dari grup

### 🔍 Auto-Moderation
- Deteksi link otomatis (http, https, www, t.me, dll)
- Hapus pesan berisi link dari non-admin
- Peringatan otomatis yang menghilang setelah 10 detik

## 📁 Struktur Proyek

```
bot_asisten/
├── bot.py                 # Entry point aplikasi
├── config.py              # Konfigurasi dan environment variables
├── database/
│   └── db_manager.py      # SQLite database manager
├── handlers/
│   ├── admin_handler.py   # Handler command admin
│   ├── mod_handler.py     # Handler command moderasi
│   └── auto_mod.py        # Handler auto-moderation
├── utils/
│   └── decorators.py      # Decorator untuk otorisasi
├── .env                   # Environment variables (JANGAN commit!)
├── .env.example           # Template environment variables
├── .gitignore             # File yang diabaikan git
├── requirements.txt       # Dependencies Python
├── bot.log               # Log file (auto-generated)
└── bot_data.db           # Database SQLite (auto-generated)
```

## 🚀 Instalasi dan Setup

### 1. Prerequisites
- Python 3.8 atau lebih baru
- pip (Python package manager)
- Bot Token dari [@BotFather](https://t.me/BotFather)
- User ID Telegram Anda (dapat dari [@userinfobot](https://t.me/userinfobot))

### 2. Clone atau Download Repository
```bash
cd bot_asisten
```

### 3. Install Dependencies
```bash
# Buat virtual environment (opsional tapi direkomendasikan)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 4. Konfigurasi Environment Variables
```bash
# Copy template .env
cp .env.example .env

# Edit file .env dengan editor favorit Anda
nano .env  # atau vim, atau text editor lain
```

Isi file `.env` dengan:
```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
OWNER_ID=123456789
```

**Cara mendapatkan:**
- `BOT_TOKEN`: Chat [@BotFather](https://t.me/BotFather) → `/newbot` → ikuti instruksi
- `OWNER_ID`: Chat [@userinfobot](https://t.me/userinfobot) → kirim pesan apa saja → copy ID Anda

### 5. Jalankan Bot
```bash
python bot.py
```

Jika berhasil, Anda akan melihat:
```
==================================================
Starting Bot Asisten Telegram
Owner ID: 123456789
Database: bot_data.db
Registered admins: 0
==================================================
Bot is running... Press Ctrl+C to stop
```

## 📱 Cara Menggunakan Bot

### Setup Awal di Grup

1. **Tambahkan bot ke grup Telegram Anda**
   - Buka grup → Add Members → cari bot Anda → Add

2. **Promosikan bot menjadi Admin**
   - Grup → Group Info → Administrators → Add Administrator
   - Pilih bot Anda dan berikan permissions:
     - ✅ Delete Messages
     - ✅ Ban Users
     - ✅ Restrict Members

3. **Test bot**
   - Kirim `/start` di private chat dengan bot
   - Kirim `/start` di grup untuk verifikasi

### Command Owner

**Menambah Admin:**
```
Cara 1: Via User ID
/addadmin 987654321

Cara 2: Via Reply
(Reply pesan user yang ingin dijadikan admin)
/addadmin
```

**Menghapus Admin:**
```
/deladmin 987654321
atau reply + /deladmin
```

**Lihat Daftar Admin:**
```
/listadmin
```

### Command Moderasi (Owner & Admin)

**Mute User:**
```
(Reply pesan user yang ingin di-mute)
/mute           # Mute permanen
/mute 5m        # Mute 5 menit
/mute 2h        # Mute 2 jam
/mute 1d        # Mute 1 hari
```

**Unmute User:**
```
(Reply pesan user)
/unmute
```

**Ban User:**
```
(Reply pesan user)
/ban
```

### Auto-Moderation

Bot otomatis menghapus pesan berisi link dari user yang:
- ❌ Bukan Owner bot
- ❌ Bukan Admin terdaftar di database
- ❌ Bukan Admin bawaan grup

Link yang terdeteksi:
- `http://example.com`
- `https://example.com`
- `www.example.com`
- `t.me/username`
- Dan berbagai format URL lainnya

## 🔧 Deploy ke Production (VPS)

### Menggunakan systemd (Ubuntu/Debian)

1. **Buat service file:**
```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

2. **Isi dengan:**
```ini
[Unit]
Description=Telegram Bot Asisten
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/bot_asisten
ExecStart=/path/to/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. **Enable dan start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# Cek status
sudo systemctl status telegram-bot

# Lihat log
sudo journalctl -u telegram-bot -f
```

### Menggunakan Screen (Alternatif sederhana)

```bash
# Install screen jika belum ada
sudo apt install screen

# Buat session baru
screen -S telegram-bot

# Jalankan bot
python bot.py

# Detach dari session: Ctrl+A lalu D
# Reattach: screen -r telegram-bot
```

## 📊 Database

Bot menggunakan SQLite dengan struktur:

```sql
CREATE TABLE admins (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Backup database:**
```bash
cp bot_data.db bot_data.db.backup
```

## 🔒 Keamanan

### File Sensitif
- ✅ `.env` - Sudah ada di `.gitignore`
- ✅ `*.db` - Sudah ada di `.gitignore`
- ✅ `bot.log` - Sudah ada di `.gitignore`

### Best Practices
1. **Jangan commit `.env` ke repository**
2. **Backup database secara berkala**
3. **Gunakan user dengan privileges terbatas untuk production**
4. **Monitor log secara rutin**: `tail -f bot.log`

## 📝 Logging

Bot menghasilkan log di dua tempat:
1. **File**: `bot.log` - Semua log tersimpan di sini
2. **Console**: Output real-time saat bot berjalan

Level logging:
- INFO: Operasi normal
- WARNING: Hal yang perlu perhatian
- ERROR: Error yang perlu diperbaiki

## 🐛 Troubleshooting

### Bot tidak merespon
```bash
# Cek apakah bot berjalan
ps aux | grep bot.py

# Cek log untuk error
tail -f bot.log

# Cek token bot
cat .env
```

### Database error
```bash
# Cek permissions
ls -la bot_data.db

# Hapus dan biarkan auto-generate ulang (DATA AKAN HILANG!)
rm bot_data.db
python bot.py
```

### Bot tidak bisa delete/mute/ban
- Pastikan bot adalah Admin di grup
- Cek permissions bot di grup settings

## 🔄 Update Bot

```bash
# Pull update terbaru (jika menggunakan git)
git pull

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart bot
sudo systemctl restart telegram-bot
```

## 📞 Support

Jika ada masalah:
1. Cek log: `tail -f bot.log`
2. Cek konfigurasi: Pastikan `.env` sudah benar
3. Cek permissions: Bot harus admin di grup
4. Test di private chat dulu untuk isolasi masalah

## 📄 License

Project ini dibuat untuk tujuan edukasi dan penggunaan pribadi.

## 🙏 Credits

Dibuat dengan menggunakan:
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v20+
- SQLite3
- Python 3.8+

---

**⚠️ PENTING:** Jangan lupa untuk:
- ✅ Copy `.env.example` ke `.env`
- ✅ Isi `BOT_TOKEN` dan `OWNER_ID`
- ✅ Jangan commit file `.env` dan `*.db` ke repository
- ✅ Promosikan bot sebagai admin di grup