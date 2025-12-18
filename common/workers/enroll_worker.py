"""
Thread xử lý AI (detection, head pose, embedding) cho bước capture.
Tách riêng để đơn giản hóa UI và giữ file ngắn hơn.
"""

from PySide6.QtCore import QThread, QMutex, QWaitCondition, Signal

from modules.ai.face_analyzer import FaceAnalyzer, DistanceStatus, PoseType


class FaceProcessingThread(QThread):
    """Chạy InsightFace + head pose trên background thread."""

    model_loaded = Signal(bool, str)  # success, message
    result_ready = Signal(dict)  # Stores full analysis result

    PROCESS_EVERY_N_FRAMES = 3  # Giảm tải: chỉ xử lý 1/3 frame

    def __init__(self):
        super().__init__()
        self.face_analyzer: FaceAnalyzer | None = None
        self.running = True
        self.latest_frame = None
        self.target_pose: PoseType | None = None
        self.frame_mutex = QMutex()
        self.condition = QWaitCondition()
        self.is_models_loaded = False
        self._frame_counter = 0

    def initialize_models(self):
        """Khởi tạo model InsightFace + MediaPipe."""
        try:
            if self.face_analyzer is None:
                self.face_analyzer = FaceAnalyzer()
            self.face_analyzer._ensure_models()
            self.is_models_loaded = True
            self.model_loaded.emit(True, "Models loaded successfully")
        except Exception as exc:  # pragma: no cover
            print(f"Error loading models: {exc}")
            self.model_loaded.emit(False, str(exc))

    def update_frame(self, frame, target_pose: PoseType):
        """Nhận frame mới và pose mục tiêu cần kiểm tra."""
        if not self.is_models_loaded:
            return
        self._frame_counter += 1
        if self._frame_counter % self.PROCESS_EVERY_N_FRAMES != 0:
            return
        self.frame_mutex.lock()
        self.latest_frame = frame.copy()
        self.target_pose = target_pose
        self.frame_mutex.unlock()
        self.condition.wakeOne()

    def run(self):
        self.initialize_models()
        while self.running:
            self.frame_mutex.lock()
            if self.latest_frame is None and self.running:
                self.condition.wait(self.frame_mutex)
            if self.latest_frame is None or not self.running:
                self.frame_mutex.unlock()
                continue

            frame = self.latest_frame
            target_pose = self.target_pose
            self.latest_frame = None
            self.frame_mutex.unlock()

            if self.is_models_loaded and self.face_analyzer is not None:
                try:
                    # Gọi hàm phân tích tối ưu (1 pass)
                    result = self.face_analyzer.analyze_frame(frame, target_pose)
                    
                    # Đính kèm frame gốc vào result để đảm bảo đồng bộ khi chụp
                    # (Lưu ý: việc truyền frame qua signal có thể copy data, nhưng cần thiết để khớp)
                    result["frame"] = frame 
                    
                    self.result_ready.emit(result)
                except Exception as exc:  # pragma: no cover
                    print(f"Processing error: {exc}")

    def stop(self):
        self.running = False
        self.frame_mutex.lock()
        self.latest_frame = None  # Clear để tránh memory leak
        self.frame_mutex.unlock()
        self.condition.wakeOne()
        self.wait()

    def reset_pose_state(self):
        """Reset baseline pose khi bắt đầu sequence mới."""
        if self.face_analyzer is not None:
            self.face_analyzer.reset_pose_state()


