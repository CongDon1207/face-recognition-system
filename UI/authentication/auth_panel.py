from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt
from UI.styles import Theme
import cv2
import numpy as np


class AuthCameraPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.camera_label = None
        self._build_ui()

    def _build_ui(self):
        self.setFixedSize(900, 430)
        self.setStyleSheet(
            f"QFrame {{ background-color: rgba(5, 8, 22, 200); "
            f"border: 2px solid {Theme.PRIMARY}; border-radius: 12px; }}"
        )

        # Main horizontal layout: HUD | Camera | Info
        main_h_layout = QHBoxLayout(self)
        main_h_layout.setContentsMargins(12, 12, 12, 12)
        main_h_layout.setSpacing(12)

        # === LEFT: HUD Panel ===
        self.hud_frame = QFrame()
        self.hud_frame.setFixedSize(160, 140)
        self.hud_frame.setStyleSheet(
            f"QFrame {{ background-color: rgba(0, 0, 0, 200); "
            f"border: 1px solid {Theme.PRIMARY}; border-radius: 8px; }}"
        )
        hud_layout = QVBoxLayout(self.hud_frame)
        hud_layout.setContentsMargins(10, 10, 10, 10)
        hud_layout.setSpacing(8)
        
        hud_style = (
            f"color: {Theme.PRIMARY}; font-size: 11px; "
            "font-weight: bold; font-family: 'Consolas'; border: none; background: transparent;"
        )

        self.liveness_label = QLabel("STATUS: READY")
        self.liveness_label.setStyleSheet(hud_style)

        self.fps_label = QLabel("FPS: 0.0")
        self.fps_label.setStyleSheet(hud_style)

        self.timer_label = QLabel("TIME: 0s")
        self.timer_label.setStyleSheet(hud_style)

        self.fail_label = QLabel("FAILS: 0/3")
        self.fail_label.setStyleSheet(
            f"color: {Theme.SECONDARY_RED}; font-size: 11px; "
            "font-weight: bold; font-family: 'Consolas'; border: none; background: transparent;"
        )

        hud_layout.addWidget(self.liveness_label)
        hud_layout.addWidget(self.fps_label)
        hud_layout.addWidget(self.timer_label)
        hud_layout.addWidget(self.fail_label)
        hud_layout.addStretch()

        main_h_layout.addWidget(self.hud_frame, alignment=Qt.AlignTop)

        # === CENTER: Camera Viewport ===
        center_layout = QVBoxLayout()
        center_layout.setSpacing(8)

        self.camera_viewport = QFrame()
        self.camera_viewport.setFixedSize(440, 340)
        self.camera_viewport.setStyleSheet(
            f"QFrame {{ background-color: #000000; "
            f"border: 2px solid {Theme.PRIMARY}; border-radius: 10px; }}"
        )

        viewport_layout = QVBoxLayout(self.camera_viewport)
        viewport_layout.setContentsMargins(0, 0, 0, 0)
        self.camera_status = QLabel("Camera Offline")
        self.camera_status.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 14px; border: none;")
        viewport_layout.addWidget(self.camera_status, alignment=Qt.AlignCenter)

        self.loading_label = QLabel("Initializing System...", self.camera_viewport)
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet(
            f"background-color: rgba(0,0,0,180); color: {Theme.PRIMARY}; "
            "font-size: 15px; font-weight: bold; border: none;"
        )
        self.loading_label.setFixedSize(440, 340)
        self.loading_label.hide()

        center_layout.addWidget(self.camera_viewport, alignment=Qt.AlignCenter)

        # Status message - below camera
        self.status_message = QLabel("")
        self.status_message.setFixedSize(440, 45)
        self.status_message.setAlignment(Qt.AlignCenter)
        self.status_message.setWordWrap(True)
        self.status_message.setStyleSheet(
            f"color: {Theme.PRIMARY}; font-size: 12px; font-weight: bold; "
            f"background-color: rgba(0, 0, 0, 180); border-radius: 6px; padding: 6px; "
            f"border: 1px solid {Theme.PRIMARY};"
        )
        center_layout.addWidget(self.status_message, alignment=Qt.AlignCenter)

        main_h_layout.addLayout(center_layout)

        # === RIGHT: Spacer to balance ===
        right_spacer = QFrame()
        right_spacer.setFixedSize(160, 140)
        right_spacer.setStyleSheet("background: transparent; border: none;")
        main_h_layout.addWidget(right_spacer, alignment=Qt.AlignTop)

    def display_frame(self, frame: np.ndarray):
        try:
            frame_resized = cv2.resize(frame, (440, 340))
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            q_image = QImage(frame_rgb.tobytes(), w, h, ch * w, QImage.Format_RGB888).copy()
            pixmap = QPixmap.fromImage(q_image)

            if self.camera_label is None:
                self.camera_label = QLabel(self.camera_viewport)
                self.camera_label.setFixedSize(440, 340)
                self.camera_label.setStyleSheet("border: none;")
                self.camera_label.show()
                self.camera_status.hide()

            self.camera_label.show()
            self.camera_label.setPixmap(pixmap)
        except Exception as e:
            print(f"Display error: {e}")
