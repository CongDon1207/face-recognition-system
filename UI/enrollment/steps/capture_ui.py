"""
UI mixin cho bước Capture (enroll).
Tách riêng để giảm độ dài file capture_step.py và tăng maintainability.
"""

import cv2
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap, QColor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGraphicsDropShadowEffect,
)

from UI.styles import Theme
from modules.face_analyzer import DistanceStatus, PoseType


class CaptureStepUI:
    """Mixin chỉ chứa phần dựng UI và vẽ overlay."""

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(30)

        # Panel camera
        camera_container = QFrame()
        camera_container.setProperty("class", "glass_panel")
        camera_layout = QVBoxLayout(camera_container)
        camera_layout.setAlignment(Qt.AlignCenter)

        # Khung ngoài 2 lớp (outer frame)
        self.camera_frame = QFrame()
        self.camera_frame.setFixedSize(410, 410)
        self.camera_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: transparent;
                border: 2px solid {Theme.BORDER_COLOR};
                border-radius: 16px;
            }}
            """
        )
        frame_layout = QVBoxLayout(self.camera_frame)
        frame_layout.setContentsMargins(6, 6, 6, 6)
        frame_layout.setAlignment(Qt.AlignCenter)

        # Khung trong (inner view)
        self.camera_view = QLabel()
        self.camera_view.setAlignment(Qt.AlignCenter)
        self.camera_view.setFixedSize(400, 400)
        self.camera_view.setStyleSheet(
            f"background-color: #000; border: 4px solid {Theme.PRIMARY}; border-radius: 12px;"
        )
        frame_layout.addWidget(self.camera_view)
        camera_layout.addWidget(self.camera_frame)

        self.instruction_label = QLabel("Đang tải mô hình AI...")
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.instruction_label.setStyleSheet(
            f"color: {Theme.PRIMARY}; font-size: 22px; font-weight: bold; padding: 15px;"
        )
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(Theme.PRIMARY))
        shadow.setOffset(0, 0)
        self.instruction_label.setGraphicsEffect(shadow)
        camera_layout.addWidget(self.instruction_label)

        self.distance_label = QLabel("Vui lòng chờ...")
        self.distance_label.setAlignment(Qt.AlignCenter)
        self.distance_label.setStyleSheet("color: #FFD700; font-size: 16px;")
        camera_layout.addWidget(self.distance_label)

        # Nút chụp thủ công
        self.capture_btn = QPushButton("📸 Chụp")
        self.capture_btn.setFixedHeight(60)
        self.capture_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                font-size: 20px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: {Theme.SECONDARY_GREEN};
            }}
            QPushButton:disabled {{
                background-color: #555;
                color: #999;
            }}
            """
        )
        self.capture_btn.clicked.connect(self._on_manual_capture)
        self.capture_btn.setEnabled(False)
        camera_layout.addWidget(self.capture_btn)

        layout.addWidget(camera_container, 2)

        # Panel checklist
        checklist_container = QFrame()
        checklist_container.setProperty("class", "glass_panel")
        checklist_layout = QVBoxLayout(checklist_container)
        checklist_layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Tiến trình quay các góc")
        header.setStyleSheet(
            f"color: {Theme.TEXT_WHITE}; font-size: 18px; font-weight: bold;"
        )
        checklist_layout.addWidget(header)

        self.checklist_labels: dict[PoseType, QLabel] = {}
        for pose in self.POSE_SEQUENCE:
            lbl = QLabel(f"⬜  {self.POSE_NAMES[pose]}")
            lbl.setStyleSheet(
                f"color: {Theme.TEXT_GRAY}; font-size: 16px; padding: 8px;"
            )
            self.checklist_labels[pose] = lbl
            checklist_layout.addWidget(lbl)

        checklist_layout.addStretch()

        cancel_btn = QPushButton("Hủy")
        cancel_btn.setProperty("class", "danger_button")
        cancel_btn.clicked.connect(self._on_cancel)
        checklist_layout.addWidget(cancel_btn)

        layout.addWidget(checklist_container, 1)

    def _on_camera_started(self):
        self.camera_view.clear()
        self.camera_view.setStyleSheet(
            f"background-color: #000; border: 4px solid {Theme.PRIMARY}; border-radius: 12px;"
        )
        self.distance_label.setText("")
        self._update_instruction()

    def _reset_checklist(self):
        for pose, lbl in self.checklist_labels.items():
            lbl.setText(f"⬜  {self.POSE_NAMES[pose]}")
            lbl.setStyleSheet(
                f"color: {Theme.TEXT_GRAY}; font-size: 16px; padding: 8px;"
            )

    def _update_instruction(self):
        if self.current_step_index >= len(self.POSE_SEQUENCE):
            self.instruction_label.setText("✅ Hoàn tất!")
            return

        current_pose = self.POSE_SEQUENCE[self.current_step_index]
        pose_name = self.POSE_NAMES[current_pose]
        step_num = self.current_step_index + 1
        total = len(self.POSE_SEQUENCE)

        instructions = {
            PoseType.FRONTAL: "Nhìn thẳng vào camera",
            PoseType.LEFT: "Xoay mặt sang trái",
            PoseType.RIGHT: "Xoay mặt sang phải",
            PoseType.UP: "Ngẩng đầu lên",
            PoseType.DOWN: "Cúi đầu xuống",
        }

        msg = (
            f"{step_num}/{total}: {pose_name}\n\n"
            f"{instructions.get(current_pose, '')}\n\n"
            "Nhấn nút CHỤP khi sẵn sàng"
        )
        self.instruction_label.setText(msg)

    def _draw_ui_overlay(self, frame: np.ndarray):
        if not self.last_ai_result:
            self._display_frame(frame)
            return

        display_frame = frame.copy()
        dist_status = self.last_ai_result.get("distance_status", DistanceStatus.NO_FACE)
        pose_ok = self.last_ai_result.get("pose_ok", False)

        border_color = Theme.DANGER_RED
        if dist_status == DistanceStatus.OK and pose_ok:
            border_color = Theme.SECONDARY_GREEN
        elif dist_status == DistanceStatus.OK:
            border_color = "#FFD700"

        h, w = display_frame.shape[:2]
        color_bgr = self._hex_to_bgr(border_color)

        min_dim = min(h, w)
        center = (w // 2, h // 2)
        axes = (int(min_dim * 0.36), int(min_dim * 0.48))
        cv2.ellipse(display_frame, center, axes, 0, 0, 360, color_bgr, 4)

        yaw_text = "Ratio: --"
        if self.last_yaw is not None:
            yaw_text = f"Ratio: {self.last_yaw:.2f}"

        cv2.putText(
            display_frame,
            yaw_text,
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            self._hex_to_bgr("#FFFFFF"),
            2,
            cv2.LINE_AA,
        )

        self._display_frame(display_frame)

    def _mark_step_done(self, pose: PoseType):
        lbl = self.checklist_labels[pose]
        lbl.setText(f"✅  {self.POSE_NAMES[pose]}")
        lbl.setStyleSheet(
            f"color: {Theme.SECONDARY_GREEN}; font-size: 16px; padding: 8px; font-weight: bold;"
        )

    def _display_frame(self, frame: np.ndarray):
        if self.camera_view.text():
            self.camera_view.clear()
            self.camera_view.setStyleSheet(
                f"background-color: #000; border: 4px solid {Theme.PRIMARY}; border-radius: 12px;"
            )

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        scaled = pixmap.scaled(
            400, 400, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        )
        self.camera_view.setPixmap(scaled)

    def _hex_to_bgr(self, hex_color: str) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return b, g, r

