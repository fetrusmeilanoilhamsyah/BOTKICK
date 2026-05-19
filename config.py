"""
config.py
=========
Module untuk memuat dan memvalidasi environment variables dari file .env
dengan penanganan error yang aman.
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Memuat file .env dari direktori root proyek
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """
    Class untuk menyimpan konfigurasi bot yang dimuat dari environment variables.
    Melakukan validasi otomatis saat inisialisasi.
    """
    
    def __init__(self):
        """Inisialisasi dan validasi konfigurasi."""
        self.BOT_TOKEN = os.getenv('BOT_TOKEN')
        self.OWNER_ID = os.getenv('OWNER_ID')
        
        # Validasi konfigurasi
        self._validate()
    
    def _validate(self):
        """
        Memvalidasi bahwa semua konfigurasi wajib telah diisi.
        Keluar dari program jika ada yang kosong.
        """
        errors = []
        
        if not self.BOT_TOKEN:
            errors.append("BOT_TOKEN tidak ditemukan di file .env")
        
        if not self.OWNER_ID:
            errors.append("OWNER_ID tidak ditemukan di file .env")
        else:
            # Validasi bahwa OWNER_ID adalah angka
            try:
                self.OWNER_ID = int(self.OWNER_ID)
            except ValueError:
                errors.append("OWNER_ID harus berupa angka (User ID Telegram)")
        
        # Jika ada error, tampilkan dan keluar dari program
        if errors:
            print("=" * 50)
            print("ERROR: Konfigurasi tidak lengkap!")
            print("=" * 50)
            for error in errors:
                print(f"❌ {error}")
            print("\nSilakan:")
            print("1. Copy file '.env.example' ke '.env'")
            print("2. Isi BOT_TOKEN dan OWNER_ID dengan nilai yang benar")
            print("=" * 50)
            sys.exit(1)
    
    def __repr__(self):
        """Representasi aman (tidak menampilkan token)."""
        return f"Config(OWNER_ID={self.OWNER_ID}, BOT_TOKEN={'*' * 10})"


# Instance global yang bisa diimpor dari module lain
config = Config()