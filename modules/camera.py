"""
Module Camera Thread để đọc video từ webcam trong background.
Sử dụng QThread để không block UI.
"""
import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal
import os


class CameraThread(QThread):
    """Thread đọc frame từ camera liên tục."""
    
    # Signal phát ra mỗi khi có frame mới
    frame_captured = Signal(np.ndarray)
    # Signal khi camera bị lỗi
    error_occurred = Signal(str)
    
    def __init__(self, camera_id: int = 0, parent=None):
        super().__init__(parent)
        self.camera_id = camera_id
        self._running = False
        self._cap = None

    def run(self):
        """Vòng lặp chính đọc frame từ camera."""
        # Ưu tiên backend DirectShow trên Windows để giảm độ trễ
        if os.name == "nt":
            self._cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
        else:
            self._cap = cv2.VideoCapture(self.camera_id)
        
        if not self._cap.isOpened():
            self.error_occurred.emit("Không thể mở camera")
            return
        
        # Thiết lập camera
        try:
            # Giảm buffer để tránh lag khung hình
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self._cap.set(cv2.CAP_PROP_FPS, 30)
        
        self._running = True
        print(f"[CameraThread] Started capturing from camera {self.camera_id}")
        while self._running:
            ret, frame = self._cap.read()
            if ret:
                # Flip horizontal để giống gương
                frame = cv2.flip(frame, 1)
                self.frame_captured.emit(frame)
            else:
                self.error_occurred.emit("Không đọc được frame từ camera")
                break
            
            # Giảm tải CPU một chút
            self.msleep(30)
        
        self._cap.release()

    def stop(self):
        """Dừng thread camera."""
        self._running = False
        self.wait()
        # Đảm bảo release camera nếu thread crash hoặc stop bất thường
        if self._cap and self._cap.isOpened():
            self._cap.release()

    def is_running(self) -> bool:
        """Kiểm tra thread có đang chạy không."""
        return self._running
