"""
Module Authenticator - So khớp embedding để xác thực người dùng.
Sử dụng Cosine Distance để tìm người dùng khớp nhất trong database.
"""
import numpy as np
from modules.database import DatabaseManager


class Authenticator:
    """Xác thực người dùng bằng face recognition."""
    
    def __init__(self, threshold: float = 0.4, db_manager: DatabaseManager = None):
        """
        Args:
            threshold: Ngưỡng Cosine distance (< threshold = match)
            db_manager: Database manager instance
        """
        self.threshold = threshold
        self.db = db_manager or DatabaseManager()
        self._embeddings_cache = []
        self._load_embeddings()
    
    def _load_embeddings(self):
        """Load tất cả embeddings từ database."""
        self._embeddings_cache = self.db.get_all_embeddings()
        print(f"Loaded {len(self._embeddings_cache)} embeddings from database")
    
    def reload_embeddings(self):
        """Reload embeddings (gọi sau khi có enrollment mới)."""
        self._load_embeddings()
    
    def authenticate(self, query_embedding: np.ndarray) -> tuple[bool, str | None, float]:
        """
        Xác thực embedding với database.
        
        Args:
            query_embedding: Embedding của khuôn mặt cần xác thực
            
        Returns:
            (success, user_id, distance): 
                - success: True nếu tìm thấy match
                - user_id: ID người dùng được nhận diện (None nếu không match)
                - distance: Khoảng cách nhỏ nhất tìm được
        """
        if len(self._embeddings_cache) == 0:
            return False, None, 1.0
        
        min_distance = float('inf')
        matched_user_id = None
        
        # So sánh với tất cả embeddings trong database
        for user_id, db_embedding in self._embeddings_cache:
            distance = self._cosine_distance(query_embedding, db_embedding)
            if distance < min_distance:
                min_distance = distance
                matched_user_id = user_id
        
        # Kiểm tra ngưỡng
        success = min_distance < self.threshold
        
        return success, matched_user_id if success else None, min_distance
    
    @staticmethod
    def _cosine_distance(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Tính Cosine distance giữa 2 embeddings."""
        # Normalize vectors
        emb1_norm = emb1 / (np.linalg.norm(emb1) + 1e-8)
        emb2_norm = emb2 / (np.linalg.norm(emb2) + 1e-8)
        
        # Cosine similarity
        similarity = np.dot(emb1_norm, emb2_norm)
        
        # Convert to distance (0 = identical, 1 = opposite)
        distance = 1.0 - similarity
        
        return distance
    
    def get_user_info(self, user_id: str) -> dict | None:
        """Lấy thông tin chi tiết của user."""
        return self.db.get_user(user_id)


# Test standalone
if __name__ == "__main__":
    auth = Authenticator()
    print(f"Authenticator initialized with threshold={auth.threshold}")
    print(f"Total users in database: {len(set([uid for uid, _ in auth._embeddings_cache]))}")
