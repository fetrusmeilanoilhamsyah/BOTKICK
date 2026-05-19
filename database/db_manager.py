"""
database/db_manager.py
======================
Module untuk mengelola database SQLite yang menyimpan daftar admin.
Menggunakan context manager untuk memastikan koneksi selalu ditutup dengan aman.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Optional

# Setup logging
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Class untuk mengelola operasi database SQLite.
    Menyimpan daftar admin yang diberikan akses oleh Owner.
    """
    
    def __init__(self, db_path: str = "bot_data.db"):
        """
        Inisialisasi database manager.
        
        Args:
            db_path: Path ke file database SQLite
        """
        self.db_path = Path(db_path)
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Membuat koneksi ke database.
        
        Returns:
            Connection object ke database
        """
        conn = sqlite3.Connection(self.db_path)
        conn.row_factory = sqlite3.Row  # Memungkinkan akses kolom dengan nama
        return conn
    
    def _init_database(self):
        """
        Inisialisasi database: membuat tabel jika belum ada.
        Tabel 'admins' menyimpan user_id dan username (opsional).
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Buat tabel admins jika belum ada
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS admins (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
        
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def add_admin(self, user_id: int, username: Optional[str] = None) -> bool:
        """
        Menambahkan admin baru ke database.
        
        Args:
            user_id: User ID Telegram
            username: Username Telegram (opsional)
        
        Returns:
            True jika berhasil, False jika gagal (misal: sudah ada)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "INSERT INTO admins (user_id, username) VALUES (?, ?)",
                    (user_id, username)
                )
                
                conn.commit()
                logger.info(f"Admin added: {user_id} (@{username})")
                return True
        
        except sqlite3.IntegrityError:
            # User sudah ada di database (PRIMARY KEY constraint)
            logger.warning(f"Admin {user_id} already exists")
            return False
        
        except sqlite3.Error as e:
            logger.error(f"Error adding admin: {e}")
            return False
    
    def remove_admin(self, user_id: int) -> bool:
        """
        Menghapus admin dari database.
        
        Args:
            user_id: User ID Telegram yang akan dihapus
        
        Returns:
            True jika berhasil dihapus, False jika tidak ditemukan atau error
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "DELETE FROM admins WHERE user_id = ?",
                    (user_id,)
                )
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Admin removed: {user_id}")
                    return True
                else:
                    logger.warning(f"Admin {user_id} not found in database")
                    return False
        
        except sqlite3.Error as e:
            logger.error(f"Error removing admin: {e}")
            return False
    
    def is_admin(self, user_id: int) -> bool:
        """
        Mengecek apakah user adalah admin yang terdaftar di database.
        
        Args:
            user_id: User ID Telegram
        
        Returns:
            True jika user adalah admin, False jika bukan
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT 1 FROM admins WHERE user_id = ?",
                    (user_id,)
                )
                
                result = cursor.fetchone()
                return result is not None
        
        except sqlite3.Error as e:
            logger.error(f"Error checking admin status: {e}")
            return False
    
    def get_all_admins(self) -> List[dict]:
        """
        Mengambil daftar semua admin dari database.
        
        Returns:
            List berisi dictionary dengan informasi admin
            Format: [{'user_id': 123, 'username': 'john', 'added_at': '...'}, ...]
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    "SELECT user_id, username, added_at FROM admins ORDER BY added_at DESC"
                )
                
                rows = cursor.fetchall()
                
                # Konversi Row objects ke dictionary
                admins = [dict(row) for row in rows]
                
                return admins
        
        except sqlite3.Error as e:
            logger.error(f"Error fetching admins: {e}")
            return []
    
    def get_admin_count(self) -> int:
        """
        Menghitung jumlah admin yang terdaftar.
        
        Returns:
            Jumlah admin dalam database
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM admins")
                
                count = cursor.fetchone()[0]
                return count
        
        except sqlite3.Error as e:
            logger.error(f"Error counting admins: {e}")
            return 0


# Instance global untuk digunakan di seluruh aplikasi
db = DatabaseManager()