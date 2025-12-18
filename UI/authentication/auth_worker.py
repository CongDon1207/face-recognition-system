from PySide6.QtCore import QThread, Signal
import numpy as np
from modules.face_analyzer import FaceAnalyzer, PoseType
from modules.authenticator import Authenticator

class AuthWorker(QThread):
    """
    Worker thread để chạy AI (FaceAnalyzer và Authenticator).
    Giúp UI không bị lag khi xử lý frame.
    """
    result_ready = Signal(dict)
    auth_result = Signal(bool, str, float) # success, user_id, distance
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.face_analyzer = FaceAnalyzer()
        self.authenticator = Authenticator()
        self._running = True
        self._pending_frame = None
        self._processing = False

    def process_frame(self, frame: np.ndarray):
        """Nhận frame mới để xử lý (chỉ lưu cái mới nhất)."""
        self._pending_frame = frame

    def run(self):
        """Vòng lặp xử lý AI."""
        print("[AuthWorker] Started")
        while self._running:
            if self._pending_frame is not None:
                frame = self._pending_frame
                self._pending_frame = None # Clear để đợi frame tiếp theo
                
                try:
                    # Phân tích khuôn mặt
                    result = self.face_analyzer.analyze_frame(frame, PoseType.FRONTAL)
                    self.result_ready.emit(result)
                    
                    # Nếu có khuôn mặt OK, có thể thực hiện auth (UI sẽ quyết định timing)
                    # Hoặc emit luôn kết quả detect để UI vẽ overlay
                except Exception as e:
                    print(f"[AuthWorker] Error: {e}")
            
            self.msleep(10) # Tránh chiếm dụng 100% CPU khi rảnh

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
