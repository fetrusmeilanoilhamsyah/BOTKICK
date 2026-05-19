# 🤖 Bot Asisten Grup Telegram

Bot moderasi grup Telegram yang **modular**, **aman**, dan **production-ready** dengan sistem otorisasi berjenjang, auto-moderation, dan fitur auto-clean chat.

---

## ✨ Fitur Utama

| Fitur | Keterangan |
|---|---|
| 🔐 Otorisasi berjenjang | Owner → Admin → Member, berbasis database SQLite |
| 🧹 Auto-clean command | Pesan `/command` admin terhapus otomatis setelah dieksekusi |
| ⏱️ Auto-delete balasan | Notifikasi bot menghilang sendiri setelah 10 detik |
| 🔇 Moderasi grup | `/mute`, `/unmute`, `/ban` dengan dukungan durasi |
| 🛡️ Auto-moderation | Deteksi & hapus link otomatis dari non-admin |
| 🔒 Akses terbatas | `/start` hanya bisa digunakan Owner & Admin |

---

## 📁 Struktur Proyek

```
bot-asistengrup/
├── bot.py                  # Entry point
├── config.py               # Konfigurasi & env variables
├── requirements.txt
├── .env                    # ⚠️ RAHASIA — jangan di-commit!
├── .env.example
├── handlers/
│   ├── admin_handler.py    # /addadmin, /deladmin, /listadmin
│   ├── mod_handler.py      # /mute, /unmute, /ban
│   └── auto_mod.py         # Deteksi & hapus link otomatis
├── utils/
│   ├── decorators.py       # @owner_only, @admin_only, dll.
│   └── helpers.py          # send_and_auto_delete & helper lain
└── database/
    └── db_manager.py       # SQLite manager
```

---

## 📋 Daftar Command

### 👑 Owner Only

| Command | Keterangan |
|---|---|
| `/start` | Info bot & daftar command |
| `/addadmin <id>` atau reply + `/addadmin` | Tambah admin baru |
| `/deladmin <id>` atau reply + `/deladmin` | Hapus admin |
| `/listadmin` | Tampilkan semua admin |

### 🛡️ Owner & Admin

| Command | Keterangan |
|---|---|
| `/mute` | Mute permanen (reply ke pesan user) |
| `/mute 5m` / `2h` / `1d` | Mute dengan durasi |
| `/unmute` | Buka mute (reply ke pesan user) |
| `/ban` | Kick user dari grup (reply ke pesan user) |

> Semua pesan command dan balasan bot **terhapus otomatis dalam 10 detik**.

---

## 🚀 Deploy ke Ubuntu 24 (Aktif Terus & Anti-Crash)

### Langkah 1 — Persiapan di VPS

```bash
# Update sistem
sudo apt update && sudo apt upgrade -y

# Install Python & pip
sudo apt install python3 python3-pip python3-venv git -y

# Clone proyek
git clone https://github.com/username/bot-asistengrup.git
cd bot-asistengrup

# Buat virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Langkah 2 — Konfigurasi `.env`

```bash
cp .env.example .env
nano .env
```

Isi file `.env`:
```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
OWNER_ID=123456789
```

Simpan: `Ctrl+X` → `Y` → `Enter`

### Langkah 3 — Test Jalankan Bot

```bash
source venv/bin/activate
python bot.py
```

Kalau sudah muncul `Application started` dan bot merespon, lanjut ke langkah berikutnya. Stop dulu dengan `Ctrl+C`.

### Langkah 4 — Buat Service systemd

```bash
sudo nano /etc/systemd/system/bot-asisten.service
```

Isi file (ganti `ubuntu` dengan username VPS kamu, sesuaikan path):
```ini
[Unit]
Description=Bot Asisten Grup Telegram
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/bot-asistengrup
ExecStart=/home/ubuntu/bot-asistengrup/venv/bin/python bot.py
Environment=PYTHONUNBUFFERED=1

# Auto-restart jika crash
Restart=always
RestartSec=5

# Logging
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Simpan: `Ctrl+X` → `Y` → `Enter`

### Langkah 5 — Aktifkan & Jalankan

```bash
# Reload konfigurasi systemd
sudo systemctl daemon-reload

# Aktifkan agar auto-start saat VPS reboot
sudo systemctl enable bot-asisten

# Jalankan sekarang
sudo systemctl start bot-asisten

# Cek status — pastikan "active (running)"
sudo systemctl status bot-asisten
```

Output sukses:
```
● bot-asisten.service - Bot Asisten Grup Telegram
     Loaded: loaded (/etc/systemd/system/bot-asisten.service; enabled)
     Active: active (running) since ...
```

---

## 🔧 Perintah Sehari-hari

```bash
# Cek status bot
sudo systemctl status bot-asisten

# Lihat log live (Ctrl+C untuk keluar)
sudo journalctl -u bot-asisten -f

# Lihat 50 log terakhir
sudo journalctl -u bot-asisten -n 50

# Restart bot (setelah update kode)
sudo systemctl restart bot-asisten

# Stop bot
sudo systemctl stop bot-asisten
```

---

## 🔄 Update Kode

```bash
cd /home/ubuntu/bot-asistengrup

# Pull update terbaru
git pull

# Update dependencies (jika ada perubahan)
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Restart bot agar perubahan berlaku
sudo systemctl restart bot-asisten
```

---

## 🛡️ Anti-Crash

Bot sudah dilindungi secara berlapis:

| Perlindungan | Cara Kerja |
|---|---|
| **systemd `Restart=always`** | Bot restart otomatis dalam 5 detik jika crash |
| **systemd `enable`** | Bot hidup otomatis saat VPS reboot |
| **Error handler global** | Semua exception di handler tertangkap, bot tidak crash |
| **`BadRequest` handling** | Pesan sudah terhapus → di-log, bot lanjut jalan |
| **`Forbidden` handling** | Bot tidak punya izin → di-log, bot lanjut jalan |
| **`drop_pending_updates=True`** | Update lama dibuang saat bot baru nyala |

**⚠️ Satu hal yang WAJIB dihindari — jangan jalankan 2 instance:**
```bash
# Cek apakah ada instance yang sudah jalan
ps aux | grep bot.py

# Kalau ada, matikan dulu
pkill -f bot.py

# Baru jalankan via systemd
sudo systemctl start bot-asisten
```

---

## 🐛 Troubleshooting

| Masalah | Solusi |
|---|---|
| `Conflict: terminated by other getUpdates` | Ada 2 instance — `pkill -f bot.py` lalu `systemctl start bot-asisten` |
| Bot tidak respon di grup | Jadikan bot Admin dengan izin Delete Messages, Ban Users, Restrict Members |
| Bot tidak bisa hapus pesan | Cek permission **Delete Messages** di pengaturan admin grup |
| `[Errno 2] No such file .env` | Jalankan `cp .env.example .env` lalu isi token & owner ID |
| Service gagal start | `journalctl -u bot-asisten -n 30` untuk lihat error |

---

## 🔒 Keamanan

- ❌ Jangan commit `.env` ke GitHub
- ❌ Jangan share `BOT_TOKEN` ke siapapun  
- ✅ File `.env`, `*.db`, `bot.log` sudah ada di `.gitignore`

**Backup database:**
```bash
cp bot_data.db bot_data_backup_$(date +%Y%m%d).db
```

**Backup otomatis tiap hari jam 02.00:**
```bash
crontab -e
# Tambahkan baris ini:
0 2 * * * cp /home/ubuntu/bot-asistengrup/bot_data.db /home/ubuntu/bot_data_$(date +\%Y\%m\%d).db
```

---

## 📦 Setup Grup

1. **Tambahkan bot ke grup** → Add Members → cari username bot
2. **Jadikan bot Admin** → Group Info → Administrators → Add Administrator
   - ✅ Delete Messages
   - ✅ Ban Users
   - ✅ Restrict Members
3. Test dengan `/start` di private chat bot

---

> **⚠️ Checklist sebelum deploy:**
> - [ ] Isi `BOT_TOKEN` dan `OWNER_ID` di `.env`
> - [ ] Bot sudah jadi Admin di grup dengan izin Delete/Ban/Restrict
> - [ ] Service systemd sudah `enabled` dan `active (running)`
> - [ ] Tidak ada instance bot lain yang berjalan