from PySide6.QtCore import QThread, Signal
import numpy as np
from modules.ai.face_analyzer import FaceAnalyzer, PoseType
from modules.authenticator import Authenticator

class AuthWorker(QThread):
    """
    Worker thread để chạy AI (FaceAnalyzer và Authenticator).
    Giúp UI không bị lag khi xử lý frame.
    """
    result_ready = Signal(dict)
    auth_result = Signal(bool, str, float)  # success, user_id, distance
    model_ready = Signal()  # Emit khi model đã load xong
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.face_analyzer = None
        self.authenticator = None
        self._running = True
        self._pending_frame = None
        self._models_loaded = False

    def process_frame(self, frame: np.ndarray):
        """Nhận frame mới để xử lý (chỉ lưu cái mới nhất)."""
        self._pending_frame = frame

    def run(self):
        """Vòng lặp xử lý AI."""
        print("[AuthWorker] Starting - Loading models...")
        
        # Khởi tạo models trong thread (tránh block UI)
        try:
            self.face_analyzer = FaceAnalyzer()
            self.face_analyzer._ensure_models()
            self.authenticator = Authenticator()
            self._models_loaded = True
            print("[AuthWorker] Models loaded successfully")
            self.model_ready.emit()
        except Exception as e:
            print(f"[AuthWorker] Failed to load models: {e}")
            return
        
        while self._running:
            if self._pending_frame is not None and self._models_loaded:
                frame = self._pending_frame
                self._pending_frame = None  # Clear để đợi frame tiếp theo
                
                try:
                    # Phân tích khuôn mặt
                    result = self.face_analyzer.analyze_frame(frame, PoseType.FRONTAL)
                    self.result_ready.emit(result)
                except Exception as e:
                    print(f"[AuthWorker] Error: {e}")
            
            self.msleep(10)  # Tránh chiếm dụng 100% CPU khi rảnh

    def authenticate(self, embedding: np.ndarray):
        """Thực hiện xác thực (gọi từ UI hoặc chạy trong loop)."""
        if embedding is not None:
            success, user_id, distance = self.authenticator.authenticate(embedding)
            self.auth_result.emit(success, user_id, distance)

    def stop(self):
        """Dừng thread."""
        self._running = False
        self.wait()
        print("[AuthWorker] Stopped")
