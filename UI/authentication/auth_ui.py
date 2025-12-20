from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
)
from PySide6.QtCore import Qt, Signal, QTimer
from UI.styles import Theme
import numpy as np
import time
from modules.camera import CameraThread
from UI.workers.auth_worker import AuthWorker
from UI.authentication.auth_panel import AuthCameraPanel
from UI.authentication.auth_view_logic import AuthViewLogic

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
        
        # Liveness passed state
        self.liveness_passed = False
        self.liveness_passed_time = None
        self.liveness_delay = 2.0  # Delay 2s trước khi bắt đầu face recognition
        self.face_recognition_timeout = 10.0  # Timeout 10s cho face recognition
        self.authentication_completed = False  # Có kết quả authentication rồi (success/fail)
        
        # NEW: Timeout UI state
        self.is_locked = False  # Khóa tạm thời sau khi fail quá nhiều
        self.lockout_timer = None
        
        self.setMinimumSize(950, 700)
        self.init_ui()
        self.view_logic = AuthViewLogic(self)
    
    def showEvent(self, event):
        """Reset UI when view is shown"""
        super().showEvent(event)
        self.reset_ui_state()
    
    def reset_ui_state(self):
        """Reset all UI elements to initial state"""
        # Reset button
        self.btn_toggle.setText("START AUTHENTICATION")
        self.btn_toggle.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.PRIMARY};
                border: 2px solid {Theme.PRIMARY};
                border-radius: 22px;
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 244, 255, 30);
            }}
        """)
        
        # Reset progress
        self.liveness_progress.setValue(0)
        if hasattr(self, 'progress_label'):
            self.progress_label.setText("Bước: 0/4")
        
        # Reset labels
        self.instruction_label.setText("Click START to begin verification")
        self.status_message.setText("")
        self.liveness_label.setText("STATUS: READY")
        self.timer_label.setText("TIME: 0s")
        self.fps_label.setText("FPS: 0.0")
        
        # Reset lock state
        self.is_locked = False
        if self.lockout_timer:
            self.lockout_timer.stop()
            self.lockout_timer = None
        
        # Reset liveness passed state
        self.liveness_passed = False
        self.liveness_passed_time = None
        self.authentication_completed = False
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # --- Title ---
        title_label = QLabel("FACE AUTHENTICATION")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 22px; font-weight: 300; letter-spacing: 2px;")
        main_layout.addWidget(title_label, alignment=Qt.AlignCenter)
        
        self.instruction_label = QLabel("Click START to begin verification")
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.instruction_label.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 12px; letter-spacing: 0.5px;")
        main_layout.addWidget(self.instruction_label, alignment=Qt.AlignCenter)
        
        main_layout.addSpacing(8)
        
        # --- Camera Panel ---
        self.camera_panel = AuthCameraPanel()
        main_layout.addWidget(self.camera_panel, alignment=Qt.AlignCenter)

        self.camera_status = self.camera_panel.camera_status
        self.loading_label = self.camera_panel.loading_label
        self.liveness_label = self.camera_panel.liveness_label
        self.fps_label = self.camera_panel.fps_label
        self.timer_label = self.camera_panel.timer_label
        self.fail_label = self.camera_panel.fail_label
        self.status_message = self.camera_panel.status_message

        main_layout.addSpacing(10)

        # --- Liveness Progress ---
        progress_container = QVBoxLayout()
        progress_container.setSpacing(3)
        
        self.liveness_progress = QProgressBar()
        self.liveness_progress.setRange(0, 100)
        self.liveness_progress.setValue(0)
        self.liveness_progress.setTextVisible(False)
        self.liveness_progress.setFixedWidth(450)
        self.liveness_progress.setFixedHeight(10)
        self.liveness_progress.setStyleSheet(
            f"""
            QProgressBar {{
                border: 2px solid {Theme.PRIMARY};
                border-radius: 6px;
                background-color: rgba(0, 0, 0, 150);
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0.5, x2:1, y2:0.5,
                    stop:0 {Theme.PRIMARY}, 
                    stop:0.5 {Theme.SECONDARY_GREEN}, 
                    stop:1 {Theme.PRIMARY});
                border-radius: 4px;
                margin: 1px;
            }}
            """
        )
        progress_container.addWidget(self.liveness_progress, alignment=Qt.AlignCenter)
        
        # Label hiển thị số bước
        self.progress_label = QLabel("Step: 0/4")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 11px;")
        progress_container.addWidget(self.progress_label, alignment=Qt.AlignCenter)
        
        main_layout.addLayout(progress_container)
        
        main_layout.addSpacing(10)
        
        # --- Controls Bar ---
        self.btn_toggle = QPushButton("START AUTHENTICATION")
        self.btn_toggle.setFixedSize(200, 40)
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.toggle_authentication)
        self.btn_toggle.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.PRIMARY};
                border: 2px solid {Theme.PRIMARY};
                border-radius: 22px;
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 244, 255, 30);
            }}
        """)
        main_layout.addWidget(self.btn_toggle, alignment=Qt.AlignCenter)
        
    def toggle_authentication(self):
        if self.is_locked:
            self.status_message.setText("Vui lòng đợi trước khi thử lại")
            return
            
        if not self.is_checking:
            self.start_authentication()
            self.btn_toggle.setText("STOP")
            self.btn_toggle.setStyleSheet(f"QPushButton {{ color: {Theme.SECONDARY_RED}; border: 2px solid {Theme.SECONDARY_RED}; border-radius: 22px; font-size: 13px; font-weight: bold; background: transparent; }}")
        else:
            self.stop_authentication()
            self.btn_toggle.setText("START AUTHENTICATION")
            self.btn_toggle.setStyleSheet(f"QPushButton {{ color: {Theme.PRIMARY}; border: 2px solid {Theme.PRIMARY}; border-radius: 22px; font-size: 13px; font-weight: bold; background: transparent; }}")

    def start_authentication(self):
        if self.is_checking: return
        self.is_checking = True
        self.camera_status.hide()
        
        self.loading_label.setText("⏳ Đang khởi tạo AI...\nVui lòng đợi")
        self.loading_label.show()
        self.loading_label.raise_()
        
        # Init Worker
        self.auth_worker = AuthWorker()
        self.auth_worker.result_ready.connect(self.view_logic.on_ai_result)
        self.auth_worker.auth_result.connect(self.view_logic.on_auth_result)
        self.auth_worker.model_ready.connect(self._on_model_ready)
        self.auth_worker.timeout_warning.connect(self.view_logic.on_timeout_warning)  # NEW
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
        if self.camera_panel.camera_label:
            self.camera_panel.camera_label.hide()
        self.status_message.setText("")
        self.liveness_label.setText("STATUS: READY")
        self.timer_label.setText("TIME: 0s")
        self.liveness_progress.setValue(0)
        if hasattr(self, 'progress_label'):
            self.progress_label.setText("Bước: 0/4")
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
            
        self.view_logic.draw_ui_overlay(frame)

