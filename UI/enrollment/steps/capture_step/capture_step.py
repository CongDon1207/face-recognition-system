"""
Bước 2: Capture – điều phối camera, AI và lưu dữ liệu chụp 5 góc.
Phần UI/overlay được tách sang capture_ui.py.
"""

import numpy as np
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QWidget

from UI.styles import Theme
from modules.camera import CameraThread
from modules.ai.face_analyzer import DistanceStatus, PoseType
from UI.workers.enroll_worker import FaceProcessingThread
from .capture_ui import CaptureStepUI


class CaptureStep(CaptureStepUI, QWidget):
    """Bước 2: chụp 5 góc khuôn mặt."""

    finished = Signal(list)  # (pose_type, embedding, cropped_image)

    DISTANCE_STABLE_REQUIRED = 3

    POSE_SEQUENCE = [
        PoseType.FRONTAL,
        PoseType.LEFT,
        PoseType.RIGHT,
        PoseType.UP,
        PoseType.DOWN,
    ]

    POSE_NAMES = {
        PoseType.FRONTAL: "Nhìn thẳng",
        PoseType.LEFT: "Xoay trái",
        PoseType.RIGHT: "Xoay phải",
        PoseType.UP: "Ngẩng lên",
        PoseType.DOWN: "Cúi xuống",
    }

    def __init__(self):
        super().__init__()
        self.current_step_index = 0
        self.captured_data: list[tuple[PoseType, np.ndarray, np.ndarray]] = []
        self.latest_frame: np.ndarray | None = None
        self.last_yaw: float | None = None
        self._distance_ok_stable = 0

        self.camera_thread: CameraThread | None = None
        self.processor_thread = FaceProcessingThread()
        self.processor_thread.result_ready.connect(self._on_ai_result)
        self.processor_thread.model_loaded.connect(self._on_models_loaded)
        self.processor_thread.start()

        self.last_ai_result = {}
        self._build_ui()

    def _on_models_loaded(self, success: bool, msg: str):
        if success:
            self.instruction_label.setText("Sẵn sàng!")
            self.distance_label.setText("")
        else:
            self.instruction_label.setText("Lỗi AI!")
            self.distance_label.setText(msg)

    def start_capture(self, user_id: str = "temp"):
        self.user_id = user_id
        self.current_step_index = 0
        self.captured_data.clear()
        self._reset_checklist()
        self.processor_thread.reset_pose_state()

        self.camera_view.setText("⏳\n\nĐang khởi động camera...")
        self.camera_view.setStyleSheet(
            f"background-color: #000; border: 4px solid {Theme.PRIMARY}; border-radius: 12px; "
            f"color: {Theme.TEXT_GRAY}; font-size: 16px;"
        )

        # Fix race condition: dừng thread cũ trước khi tạo mới
        if self.camera_thread is not None:
            if self.camera_thread.isRunning():
                print("[CaptureStep] Stopping old camera thread...")
                self.camera_thread.stop()
                self.camera_thread.wait(1000)  # Doi toi da 1s
            self.camera_thread = None

        # Tao camera thread moi
        self.camera_thread = CameraThread()
        self.camera_thread.frame_captured.connect(self._on_frame)
        self.camera_thread.error_occurred.connect(self._on_camera_error)
        self.camera_thread.started.connect(self._on_camera_started)
        self.camera_thread.start()
        print("[CaptureStep] Started new camera thread")

    def stop(self):
        if self.camera_thread:
            print("[CaptureStep] Stopping camera thread...")
            self.camera_thread.stop()
            self.camera_thread.wait(1000)  # Doi toi da 1s
            self.camera_thread = None

    def reset_ui(self):
        self.stop()
        self._reset_checklist()
        self.current_step_index = 0
        self.captured_data.clear()
        self.camera_view.clear()
        self.instruction_label.setText("Chuẩn bị...")
        self.distance_label.clear()

    @Slot(np.ndarray)
    def _on_frame(self, frame: np.ndarray):
        self.latest_frame = frame.copy()
        if self.current_step_index >= len(self.POSE_SEQUENCE):
            return
        if self.processor_thread.is_models_loaded:
            current_pose = self.POSE_SEQUENCE[self.current_step_index]
            self.processor_thread.update_frame(frame, current_pose)
        self._draw_ui_overlay(frame)

    def _on_ai_result(self, result: dict):
        self.last_ai_result = result

        distance_status = result["distance_status"]
        pose_instruction = result["pose_instruction"]
        pose_ok = result["pose_ok"]
        self.last_yaw = result["yaw"]

        if distance_status != DistanceStatus.OK:
            self._distance_ok_stable = 0

        if distance_status == DistanceStatus.NO_FACE:
            self.distance_label.setText("❌ Không thấy khuôn mặt")
            self.distance_label.setStyleSheet("color: #FF6B6B; font-size: 16px;")
            self.capture_btn.setEnabled(False)
        elif distance_status in (DistanceStatus.TOO_FAR, DistanceStatus.TOO_CLOSE):
            self.distance_label.setText(f"⚠️ {pose_instruction}")
            self.distance_label.setStyleSheet("color: #FFD700; font-size: 16px;")
            self.capture_btn.setEnabled(False)
        else:
            self._distance_ok_stable += 1
            if pose_ok and self._distance_ok_stable >= self.DISTANCE_STABLE_REQUIRED:
                self.distance_label.setText(f"✅ {pose_instruction}")
                self.distance_label.setStyleSheet(
                    f"color: {Theme.SECONDARY_GREEN}; font-size: 16px;"
                )
                self.capture_btn.setEnabled(True)
            elif pose_ok:
                self.distance_label.setText(
                    f"✅ {pose_instruction} (Giữ khoảng cách ổn định)"
                )
                self.distance_label.setStyleSheet(
                    f"color: {Theme.SECONDARY_GREEN}; font-size: 16px;"
                )
                self.capture_btn.setEnabled(False)
            else:
                self.distance_label.setText(f"ℹ️ {pose_instruction}")
                self.distance_label.setStyleSheet("color: #FFD700; font-size: 16px;")
                self.capture_btn.setEnabled(False)

    def _on_manual_capture(self):
        if not self.last_ai_result or not self.last_ai_result.get("has_face"):
            self.distance_label.setText("❌ Chưa có dữ liệu khuôn mặt")
            return

        dist_status = self.last_ai_result["distance_status"]
        pose_ok = self.last_ai_result["pose_ok"]

        if dist_status != DistanceStatus.OK or not pose_ok:
            self.distance_label.setText("❌ Chưa đạt điều kiện chụp")
            return

        embedding = self.last_ai_result["embedding"]
        face_box = self.last_ai_result["face_box"]
        frame_analyzed = self.last_ai_result["frame"]

        if embedding is None or frame_analyzed is None or face_box is None:
            self.distance_label.setText("❌ Dữ liệu lỗi")
            return

        x, y, w, h = face_box
        img_h, img_w = frame_analyzed.shape[:2]

        pad_w = int(w * 0.15)
        pad_h = int(h * 0.20)

        x1 = max(0, int(x - pad_w))
        y1 = max(0, int(y - pad_h))
        x2 = min(img_w, int(x + w + pad_w))
        y2 = min(img_h, int(y + h + pad_h))

        if x2 <= x1 or y2 <= y1:
            self.distance_label.setText("❌ Lỗi hộp khuôn mặt (ngoài biên)")
            return

        cropped = frame_analyzed[y1:y2, x1:x2]
        if cropped.size == 0:
            self.distance_label.setText("❌ Lỗi cắt ảnh")
            return

        current_pose = self.POSE_SEQUENCE[self.current_step_index]
        self.captured_data.append((current_pose, embedding, cropped))
        self._mark_step_done(current_pose)

        self.current_step_index += 1
        if self.current_step_index >= len(self.POSE_SEQUENCE):
            self.stop()
            self.finished.emit(self.captured_data)
        else:
            self._update_instruction()
            self.capture_btn.setEnabled(False)

    def _on_cancel(self):
        self.stop()
        self.finished.emit([])

    def _on_camera_error(self, msg: str):
        self.instruction_label.setText(f"Lỗi camera: {msg}")
        self.distance_label.setText("Vui lòng kiểm tra lại camera.")

