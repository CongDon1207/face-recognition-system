"""
Module quản lý Database cho hệ thống Face Recognition.
Sử dụng SQLite để lưu trữ thông tin người dùng và embedding khuôn mặt.
"""
import sqlite3
import numpy as np
from pathlib import Path
from datetime import datetime
import os

# Đường dẫn mặc định cho database
DB_PATH = Path(__file__).parent.parent / "data" / "faces.db"
FACES_DIR = Path(__file__).parent.parent / "data" / "faces"


class DatabaseManager:
    """Quản lý kết nối và thao tác với SQLite database."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Tạo kết nối mới đến database."""
        return sqlite3.connect(str(self.db_path))

    def _init_db(self):
        """Khởi tạo các bảng nếu chưa tồn tại."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Bảng users
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    fullname TEXT NOT NULL,
                    avatar_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Bảng face_embeddings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS face_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    pose_type TEXT NOT NULL,
                    image_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            conn.commit()

    def add_user(self, user_id: str, fullname: str, avatar_path: str = None) -> bool:
        """Thêm người dùng mới vào database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (id, fullname, avatar_path) VALUES (?, ?, ?)",
                    (user_id, fullname, avatar_path)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            # User ID đã tồn tại
            return False

    def add_embedding(self, user_id: str, embedding: np.ndarray, 
                      pose_type: str, image_path: str = None) -> int:
        """Lưu embedding khuôn mặt vào database."""
        # Chuyển numpy array thành bytes
        embedding_bytes = embedding.tobytes()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO face_embeddings 
                   (user_id, embedding, pose_type, image_path) VALUES (?, ?, ?, ?)""",
                (user_id, embedding_bytes, pose_type, image_path)
            )
            conn.commit()
            return cursor.lastrowid

    def get_user(self, user_id: str) -> dict | None:
        """Lấy thông tin người dùng theo ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, fullname, avatar_path, created_at FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "fullname": row[1], "avatar_path": row[2], "created_at": row[3]}
        return None

    def get_all_embeddings(self) -> list[tuple[str, np.ndarray]]:
        """Lấy tất cả embeddings để so sánh (cho Authentication)."""
        results = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, embedding FROM face_embeddings")
            for row in cursor.fetchall():
                user_id = row[0]
                embedding = np.frombuffer(row[1], dtype=np.float32)
                results.append((user_id, embedding))
        return results

    def user_exists(self, user_id: str) -> bool:
        """Kiểm tra user ID đã tồn tại chưa."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE id = ?", (user_id,))
            return cursor.fetchone() is not None

    def save_face_image(self, user_id: str, pose_type: str, image: np.ndarray) -> str:
        """Lưu ảnh khuôn mặt vào thư mục data/faces/{user_id}/."""
        import cv2
        user_dir = FACES_DIR / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{pose_type.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = user_dir / filename
        cv2.imwrite(str(filepath), image)
        return str(filepath)
