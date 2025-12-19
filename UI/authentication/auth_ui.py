from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QPushButton)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap, QImage
from UI.styles import Theme
import cv2
import numpy as np
import time
from common.camera import CameraThread
from modules.ai.face_analyzer import FaceAnalyzer, PoseType, DistanceStatus
from modules.authenticator import Authenticator
from common.workers.auth_worker import AuthWorker

class AuthenticationView(QWidget):
    """
    Authentication UI - Camera-based face recognition with liveness detection
    """
    authentication_success = Signal(str, str)
    fail_count_changed = Signal(int) 

    def __init__(self):
        super().__init__()

        self.is_checking = False
        self.fps_value = 0.0
        
        # Backend components (Threaded)
        self.camera_thread = None
        self.auth_worker = None
        
        # State
        self.last_frame_time = 0
        self.auth_cooldown = 2.0
        self.last_auth_time = 0
        self.last_ai_result = {}
        
        # NEW: Timeout UI state
        self.is_locked = False  # Khóa tạm thời sau khi fail quá nhiều
        self.lockout_timer = None
        
        self.setMinimumSize(900, 650)
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 50, 40, 50)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # --- Camera Panel ---
        camera_panel = self.create_camera_panel()
        main_layout.addWidget(camera_panel, alignment=Qt.AlignCenter)
        
        main_layout.addSpacing(20)
        
        # --- Controls Bar ---
        controls_layout = QHBoxLayout()
        self.btn_toggle = QPushButton("START AUTHENTICATION")
        self.btn_toggle.setFixedSize(250, 50)
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.toggle_authentication)
        self.btn_toggle.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.PRIMARY};
                border: 2px solid {Theme.PRIMARY};
                border-radius: 25px;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 244, 255, 30);
            }}
        """)
        controls_layout.addWidget(self.btn_toggle)
        main_layout.addLayout(controls_layout)
        
        main_layout.addSpacing(10)
        
        # --- Title & Instruction ---
        title_label = QLabel("IDENTIFICATION")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 28px; font-weight: 300; letter-spacing: 3px;")
        main_layout.addWidget(title_label, alignment=Qt.AlignCenter)
        
        self.instruction_label = QLabel("Click START to begin verification")
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.instruction_label.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 15px; letter-spacing: 0.5px;")
        main_layout.addWidget(self.instruction_label, alignment=Qt.AlignCenter)
        
    def create_camera_panel(self):
        panel = QFrame()
        panel.setFixedSize(900, 420)
        panel.setStyleSheet(f"QFrame {{ background-color: rgba(5, 8, 22, 200); border: 2px solid {Theme.PRIMARY}; border-radius: 12px; }}")
        
        # Viewport
        self.camera_viewport = QFrame(panel)
        self.camera_viewport.setFixedSize(400, 360)
        self.camera_viewport.setStyleSheet(f"QFrame {{ background-color: #000000; border: 2px solid {Theme.PRIMARY}; border-radius: 10px; }}")
        self.camera_viewport.move((900 - 400) // 2, (420 - 360) // 2)
        
        viewport_layout = QVBoxLayout(self.camera_viewport)
        self.camera_status = QLabel("Camera Offline")
        viewport_layout.addWidget(self.camera_status, alignment=Qt.AlignCenter)
        
        # Loading Overlay
        self.loading_label = QLabel("Initializing System...", self.camera_viewport)
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet(f"background-color: rgba(0,0,0,180); color: {Theme.PRIMARY}; font-size: 16px; font-weight: bold;")
        self.loading_label.setFixedSize(400, 360)
        self.loading_label.hide()
        
        # HUD
        self.hud_frame = QFrame(panel)
        self.hud_frame.setFixedSize(200, 120)  # NEW: Tăng height để thêm timer
        self.hud_frame.setStyleSheet(f"QFrame {{ background-color: rgba(0, 0, 0, 230); border: 1px solid {Theme.PRIMARY}; border-radius: 6px; }}")
        self.hud_frame.move(20, 420 - 120 - 20)
        
        hud_layout = QVBoxLayout(self.hud_frame)
        hud_style = f"color: {Theme.PRIMARY}; font-size: 11px; font-weight: bold; font-family: 'Consolas';"
        
        self.liveness_label = QLabel("STATUS: READY")
        self.liveness_label.setStyleSheet(hud_style)
        
        self.fps_label = QLabel("FPS: 0.0")
        self.fps_label.setStyleSheet(hud_style)
        
        # NEW: Timer label
        self.timer_label = QLabel("TIME: 0s")
        self.timer_label.setStyleSheet(hud_style)
        
        # NEW: Fail counter label
        self.fail_label = QLabel("FAILS: 0/3")
        self.fail_label.setStyleSheet(f"color: {Theme.SECONDARY_RED}; font-size: 11px; font-weight: bold; font-family: 'Consolas';")
        
        hud_layout.addWidget(self.liveness_label)
        hud_layout.addWidget(self.fps_label)
        hud_layout.addWidget(self.timer_label)
        hud_layout.addWidget(self.fail_label)
        
        # Status Message
        self.status_message = QLabel("")
        self.status_message.setParent(panel)
        self.status_message.setFixedSize(400, 60)
        self.status_message.setAlignment(Qt.AlignCenter)
        self.status_message.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 16px; font-weight: bold;")
        self.status_message.move((900-400)//2, 420 - 50)
        
        return panel

    def toggle_authentication(self):
        if self.is_locked:
            self.status_message.setText("⏳ Vui lòng đợi trước khi thử lại")
            return
            
        if not self.is_checking:
            self.start_authentication()
            self.btn_toggle.setText("STOP AUTHENTICATION")
            self.btn_toggle.setStyleSheet(f"QPushButton {{ color: {Theme.SECONDARY_RED}; border: 2px solid {Theme.SECONDARY_RED}; border-radius: 25px; font-size: 14px; font-weight: bold; background: transparent; }}")
        else:
            self.stop_authentication()
            self.btn_toggle.setText("START AUTHENTICATION")
            self.btn_toggle.setStyleSheet(f"QPushButton {{ color: {Theme.PRIMARY}; border: 2px solid {Theme.PRIMARY}; border-radius: 25px; font-size: 14px; font-weight: bold; background: transparent; }}")

    def start_authentication(self):
        if self.is_checking: return
        self.is_checking = True
        self.camera_status.hide()
        
        self.loading_label.setText("⏳ Đang khởi tạo AI...\nVui lòng đợi")
        self.loading_label.show()
        self.loading_label.raise_()
        
        # Init Worker
        self.auth_worker = AuthWorker()
        self.auth_worker.result_ready.connect(self._on_ai_result)
        self.auth_worker.auth_result.connect(self._on_auth_result)
        self.auth_worker.model_ready.connect(self._on_model_ready)
        self.auth_worker.timeout_warning.connect(self._on_timeout_warning)  # NEW
        self.auth_worker.start()
    
    def _on_model_ready(self):
        """Callback khi AI model đã sẵn sàng"""
        self.loading_label.setText("⏳ Đang mở camera...")
        
        self.camera_thread = CameraThread()
        self.camera_thread.frame_captured.connect(self._on_frame_captured)
        self.camera_thread.error_occurred.connect(self._on_camera_error)
        self.camera_thread.start()
    
    def _on_camera_error(self, error_msg: str):
        """Xử lý lỗi camera"""
        self.loading_label.setText(f"❌ Lỗi: {error_msg}")
        self.status_message.setText(error_msg)
        self.status_message.setStyleSheet(f"color: {Theme.DANGER_RED}; font-size: 16px; font-weight: bold;")

    def stop_authentication(self):
        self.is_checking = False
        if self.camera_thread:
            self.camera_thread.stop()
            self.camera_thread = None
        if self.auth_worker:
            self.auth_worker.stop()
            self.auth_worker = None
        
        self.camera_status.setText("Camera Offline")
        self.camera_status.show()
        if hasattr(self, 'camera_label'):
            self.camera_label.hide()
        self.status_message.setText("")
        self.liveness_label.setText("STATUS: READY")
        self.timer_label.setText("TIME: 0s")
        self.loading_label.hide()

    def _on_frame_captured(self, frame: np.ndarray):
        t = time.time()
        if self.last_frame_time > 0:
            self.fps_value = 1.0 / (t - self.last_frame_time)
        self.last_frame_time = t
        
        self.loading_label.hide()
        self.fps_label.setText(f"FPS: {self.fps_value:.1f}")
        
        if self.auth_worker:
            self.auth_worker.process_frame(frame)
            
        self._draw_ui_overlay(frame)

    def _on_ai_result(self, result: dict):
        if not self.is_checking or self.auth_worker is None:
            return
            
        self.last_ai_result = result
        
        # NEW: Cập nhật timer và fail count
        time_elapsed = result.get("time_elapsed", 0)
        fail_count = result.get("fail_count", 0)
        
        self.timer_label.setText(f"TIME: {int(time_elapsed)}s")
        self.fail_label.setText(f"FAILS: {fail_count}/3")
        self.fail_count_changed.emit(fail_count)
        # Đổi màu fail_label nếu gần đến giới hạn
        if fail_count >= 2:
            self.fail_label.setStyleSheet(f"color: {Theme.DANGER_RED}; font-size: 11px; font-weight: bold; font-family: 'Consolas';")
        else:
            self.fail_label.setStyleSheet(f"color: {Theme.SECONDARY_RED}; font-size: 11px; font-weight: bold; font-family: 'Consolas';")
        
        # 1. Kiểm tra nếu không có mặt
        if not result.get("has_face"):
            self.status_message.setText("Không tìm thấy khuôn mặt")
            self.status_message.setStyleSheet(f"color: {Theme.DANGER_RED}; font-size: 16px; font-weight: bold;")
            self.liveness_label.setText("STATUS: NO FACE")
            return
        
        # 2. Lấy các thông số
        is_real = result.get("is_real", False)
        l_status = result.get("liveness_status", "PROCESSING")
        instruction = result.get("pose_instruction", "")
        dist_status = result.get("distance_status")
        
        self.liveness_label.setText(f"STATUS: {l_status}")

        if l_status in ["SPOOF/FAKE", "SPOOF/VIDEO", "SPOOF/FLAT"]:
            self.status_message.setText("CẢNH BÁO: PHÁT HIỆN GIẢ MẠO!")
            self.status_message.setStyleSheet(f"color: {Theme.DANGER_RED}; font-size: 16px; font-weight: bold;")
            return 

        if not is_real or l_status == "PROCESSING":
            self.status_message.setText(instruction if instruction else "Đang kiểm tra thực thể...")
            self.status_message.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 16px; font-weight: bold;")
            return
            
        if dist_status == DistanceStatus.TOO_FAR:
            self.status_message.setText("Lại gần hơn một chút")
            self.status_message.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 16px; font-weight: bold;")
            return
        elif dist_status == DistanceStatus.TOO_CLOSE:
            self.status_message.setText("Lùi xa hơn một chút")
            self.status_message.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 16px; font-weight: bold;")
            return
        
        elif dist_status == DistanceStatus.OK:
            now = time.time()
            if now - self.last_auth_time > self.auth_cooldown:
                if "embedding" in result and result["embedding"] is not None:
                    self.status_message.setText("Đang nhận diện khuôn mặt...")
                    self.status_message.setStyleSheet(f"color: {Theme.SECONDARY_GREEN}; font-size: 16px; font-weight: bold;")
                    self.auth_worker.authenticate(result["embedding"])
                    self.last_auth_time = now
            else:
                if "THÀNH CÔNG" not in self.status_message.text():
                    self.status_message.setText("Giữ nguyên vị trí...")

    def _on_timeout_warning(self, warning_msg: str):
        """NEW: Xử lý timeout warning"""
        print(f"[AuthView] Timeout warning received: {warning_msg}")
        
        self.status_message.setText(f"⏰ {warning_msg}")
        self.status_message.setStyleSheet(f"color: {Theme.DANGER_RED}; font-size: 16px; font-weight: bold;")
        
        # Nếu đã fail quá nhiều lần, khóa tạm thời
        if "THẤT BẠI" in warning_msg and "LẦN" in warning_msg:
            self._start_lockout_period(30)  # Khóa 30 giây

    def _start_lockout_period(self, seconds: int):
        """NEW: Khóa hệ thống tạm thời"""
        print(f"[AuthView] Starting lockout period: {seconds}s")
        
        self.is_locked = True
        self.stop_authentication()
        
        # Disable button
        self.btn_toggle.setEnabled(False)
        self.btn_toggle.setText(f"⏳ Chờ {seconds}s")
        self.btn_toggle.setStyleSheet(f"QPushButton {{ color: #666666; border: 2px solid #666666; border-radius: 25px; font-size: 14px; font-weight: bold; background: transparent; }}")
        
        # Countdown timer
        self.lockout_timer = QTimer(self)
        remaining = [seconds]  # Use list để capture by reference
        
        def countdown():
            remaining[0] -= 1
            if remaining[0] > 0:
                self.btn_toggle.setText(f"⏳ Chờ {remaining[0]}s")
            else:
                self._end_lockout_period()
        
        self.lockout_timer.timeout.connect(countdown)
        self.lockout_timer.start(1000)

    def _end_lockout_period(self):
        """NEW: Kết thúc thời gian khóa"""
        print("[AuthView] Lockout period ended")
        
        if self.lockout_timer:
            self.lockout_timer.stop()
            self.lockout_timer = None
        
        self.is_locked = False
        self.btn_toggle.setEnabled(True)
        self.btn_toggle.setText("START AUTHENTICATION")
        self.btn_toggle.setStyleSheet(f"QPushButton {{ color: {Theme.PRIMARY}; border: 2px solid {Theme.PRIMARY}; border-radius: 25px; font-size: 14px; font-weight: bold; background: transparent; }}")
        
        # Reset fail count trong worker
        if self.auth_worker:
            self.auth_worker.reset_fail_count()
        
        self.status_message.setText("✓ Sẵn sàng xác thực lại")
        self.status_message.setStyleSheet(f"color: {Theme.SECONDARY_GREEN}; font-size: 16px; font-weight: bold;")

    def _on_auth_result(self, success, user_id, distance):
        if success:
            info = self.auth_worker.authenticator.get_user_info(user_id)
            name = info['fullname'] if info else user_id
            self.status_message.setText(f"✓ THÀNH CÔNG: {name}")
            self.status_message.setStyleSheet(f"color: {Theme.SECONDARY_GREEN}; font-size: 16px; font-weight: bold;")
            self.authentication_success.emit(user_id, name)
        else:
            self.status_message.setText("✗ KHÔNG NHẬN DIỆN ĐƯỢC")
            self.status_message.setStyleSheet(f"color: {Theme.DANGER_RED}; font-size: 16px; font-weight: bold;")

    def _draw_ui_overlay(self, frame: np.ndarray):
        display_frame = frame.copy()
        h, w = display_frame.shape[:2]
        
        color_hex = Theme.PRIMARY
        
        if self.last_ai_result:
            if not self.last_ai_result.get("has_face"):
                color_hex = Theme.DANGER_RED
            elif not self.last_ai_result.get("is_real", True):
                color_hex = Theme.SECONDARY_RED
            elif self.last_ai_result.get("distance_status") == DistanceStatus.OK:
                if "THÀNH CÔNG" in self.status_message.text():
                    color_hex = Theme.SECONDARY_GREEN
                elif "KHÔNG NHẬN DIỆN" in self.status_message.text():
                    color_hex = Theme.DANGER_RED
                else:
                    color_hex = Theme.SECONDARY_GREEN
            else:
                color_hex = "#FFD700"
        
        r, g, b = int(color_hex[1:3], 16), int(color_hex[3:5], 16), int(color_hex[5:7], 16)
        cv2.ellipse(display_frame, (w//2, h//2), (int(min(h,w)*0.36), int(min(h,w)*0.48)), 0, 0, 360, (b, g, r), 3)
        
        self._display_frame(display_frame)

    def _display_frame(self, frame: np.ndarray):
        try:
            frame_resized = cv2.resize(frame, (400, 360))
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            q_image = QImage(frame_rgb.tobytes(), w, h, ch * w, QImage.Format_RGB888).copy()
            pixmap = QPixmap.fromImage(q_image)
            
            if not hasattr(self, 'camera_label'):
                self.camera_label = QLabel(self.camera_viewport)
                self.camera_label.setFixedSize(400, 360)
                self.camera_label.show()
                self.camera_status.hide()
            
            self.camera_label.show()
            self.camera_label.setPixmap(pixmap)
        except Exception as e:
            print(f"Display error: {e}")