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
        conn = sqlite3.connect(str(self.db_path))
        # Bật foreign keys để ON DELETE CASCADE có hiệu lực
        try:
            conn.execute("PRAGMA foreign_keys = ON;")
        except sqlite3.Error:
            pass
        return conn

    def _init_db(self):
        """Khởi tạo các bảng nếu chưa tồn tại."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Bảng users
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    fullname TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    dob TEXT,
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
            # Bảng events - lưu logs cho Dashboard
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    result TEXT NOT NULL,
                    score REAL,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def add_user(self, user_id: str, fullname: str, email: str = None, 
                 phone: str = None, dob: str = None, avatar_path: str = None) -> bool:
        """Thêm người dùng mới vào database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (id, fullname, email, phone, dob, avatar_path) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, fullname, email, phone, dob, avatar_path)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
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
            cursor.execute("SELECT id, fullname, email, phone, dob, avatar_path, created_at FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0], 
                    "fullname": row[1], 
                    "email": row[2], 
                    "phone": row[3], 
                    "dob": row[4], 
                    "avatar_path": row[5], 
                    "created_at": row[6]
                }
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

    def save_face_image(self, user_id: str, pose_type: str, image: np.ndarray) -> str | None:
        """Lưu ảnh khuôn mặt vào thư mục data/faces/{user_id}/."""
        import cv2
        try:
            user_dir = FACES_DIR / user_id
            user_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{pose_type.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = user_dir / filename
            success = cv2.imwrite(str(filepath), image)
            if not success:
                print(f"Failed to write image: {filepath}")
                return None
            return str(filepath)
        except Exception as e:
            print(f"Error saving face image: {e}")
            return None

    def enroll_user_with_embeddings(
        self,
        user_id: str,
        fullname: str,
        email: str | None,
        phone: str | None,
        dob: str | None,
        avatar_path: str | None,
        embeddings_data: list[tuple[np.ndarray, str, str | None]],
    ) -> bool:
        """
        Ghi enrollment theo 1 transaction:
        - Thêm user trước
        - Thêm embeddings sau
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (id, fullname, email, phone, dob, avatar_path) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, fullname, email, phone, dob, avatar_path),
                )
                for embedding, pose_type, image_path in embeddings_data:
                    cursor.execute(
                        """INSERT INTO face_embeddings
                           (user_id, embedding, pose_type, image_path)
                           VALUES (?, ?, ?, ?)""",
                        (user_id, embedding.tobytes(), pose_type, image_path),
                    )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        except sqlite3.Error as e:
            print(f"DB Error: {e}")
            return False

    # ========== Events (Logs) Methods ==========
    
    def add_event(self, event_type: str, user_id: str = None, result: str = "success", 
                  score: float = None, details: str = None) -> int:
        """
        Ghi một event vào bảng logs.
        event_type: 'enroll', 'auth', 'auth_fail', 'logout'
        result: 'success', 'fail', 'cancelled'
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO events (event_type, user_id, result, score, details)
                   VALUES (?, ?, ?, ?, ?)""",
                (event_type, user_id, result, score, details)
            )
            conn.commit()
            return cursor.lastrowid

    def get_events(self, limit: int = 50, event_type: str = None) -> list[dict]:
        """Lấy danh sách events gần nhất (cho Dashboard logs)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if event_type:
                cursor.execute(
                    """SELECT id, event_type, user_id, result, score, details, created_at 
                       FROM events WHERE event_type = ? ORDER BY created_at DESC LIMIT ?""",
                    (event_type, limit)
                )
            else:
                cursor.execute(
                    """SELECT id, event_type, user_id, result, score, details, created_at 
                       FROM events ORDER BY created_at DESC LIMIT ?""",
                    (limit,)
                )
            rows = cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "event_type": row[1],
                    "user_id": row[2],
                    "result": row[3],
                    "score": row[4],
                    "details": row[5],
                    "created_at": row[6]
                }
                for row in rows
            ]

    def get_stats(self) -> dict:
        """Lấy thống kê tổng quan cho Dashboard."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Tổng số users
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            # Tổng số enroll events
            cursor.execute("SELECT COUNT(*) FROM events WHERE event_type = 'enroll'")
            total_enrolls = cursor.fetchone()[0]
            
            # Tổng số auth events (thành công)
            cursor.execute("SELECT COUNT(*) FROM events WHERE event_type = 'auth' AND result = 'success'")
            total_auth_success = cursor.fetchone()[0]
            
            # Tổng số auth events (thất bại)
            cursor.execute("SELECT COUNT(*) FROM events WHERE event_type = 'auth_fail'")
            total_auth_fail = cursor.fetchone()[0]
            
            # Auth hôm nay
            cursor.execute("""
                SELECT COUNT(*) FROM events 
                WHERE event_type = 'auth' AND result = 'success'
                AND date(created_at) = date('now')
            """)
            auth_today = cursor.fetchone()[0]
            
            return {
                "total_users": total_users,
                "total_enrolls": total_enrolls,
                "total_auth_success": total_auth_success,
                "total_auth_fail": total_auth_fail,
                "auth_today": auth_today
            }

    def get_all_users(self) -> list[dict]:
        """Lấy danh sách tất cả users."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, fullname, email, phone, dob, avatar_path, created_at FROM users ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "fullname": row[1],
                    "email": row[2],
                    "phone": row[3],
                    "dob": row[4],
                    "avatar_path": row[5],
                    "created_at": row[6]
                }
                for row in rows
            ]
