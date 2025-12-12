"""
Step 2: Capture – chụp khuôn mặt theo 5 góc với hướng dẫn chi tiết.
"""

import cv2
import numpy as np
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QImage, QPixmap, QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGraphicsDropShadowEffect,
)

from UI.styles import Theme
from common.camera import CameraThread
from modules.face_analyzer import DistanceStatus, PoseType
from .face_processing_thread import FaceProcessingThread


class CaptureStep(QWidget):
    """Bước 2: chụp 5 góc khuôn mặt."""

    finished = Signal(list)  # (pose_type, embedding, cropped_image)

    POSE_SEQUENCE = [
        PoseType.FRONTAL,
        PoseType.LEFT,
        PoseType.RIGHT,
        PoseType.UP,
        PoseType.DOWN
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
        self.latest_frame: np.ndarray | None = None  # Lưu frame mới nhất
        self.last_yaw: float | None = None  # Khởi tạo last_yaw

        self.camera_thread: CameraThread | None = None
        self.processor_thread = FaceProcessingThread()
        self.processor_thread.result_ready.connect(self._on_ai_result)
        self.processor_thread.model_loaded.connect(self._on_models_loaded)
        self.processor_thread.start()

        self.last_ai_result = {}  # Initialize as empty dict for new logic

        self._build_ui()

    # ------------------------------- UI setup ------------------------------- #
    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(30)

        # Panel camera
        camera_container = QFrame()
        camera_container.setProperty("class", "glass_panel")
        camera_layout = QVBoxLayout(camera_container)
        camera_layout.setAlignment(Qt.AlignCenter)

        self.camera_view = QLabel()
        self.camera_view.setAlignment(Qt.AlignCenter)
        self.camera_view.setFixedSize(400, 400)
        self.camera_view.setStyleSheet(
            f"background-color: #000; border: 3px solid {Theme.PRIMARY}; border-radius: 200px;"
        )
        camera_layout.addWidget(self.camera_view)

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

        # NÚt Chụp thủ công
        self.capture_btn = QPushButton("📸 Chụp")
        self.capture_btn.setFixedHeight(60)
        self.capture_btn.setStyleSheet(f"""
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
        """)
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

    # -------------------------- Capture life-cycle -------------------------- #
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
        
        # Reset baseline pose từ FRONTAL
        self.processor_thread.reset_pose_state()

        self.camera_view.setText("⌛\n\nĐang khởi động camera...")
        self.camera_view.setStyleSheet(
            f"background-color: #000; border: 3px solid {Theme.PRIMARY}; "
            f"border-radius: 200px; color: {Theme.TEXT_GRAY}; font-size: 16px;"
        )

        if self.camera_thread is None or not self.camera_thread.isRunning():
            self.camera_thread = CameraThread()
            self.camera_thread.frame_captured.connect(self._on_frame)
            self.camera_thread.error_occurred.connect(self._on_camera_error)
            self.camera_thread.started.connect(self._on_camera_started)
            self.camera_thread.start()

    def stop(self):
        if self.camera_thread:
            self.camera_thread.stop()

    def reset_ui(self):
        self.stop()
        self._reset_checklist()
        self.current_step_index = 0
        self.captured_data.clear()
        self.camera_view.clear()
        self.instruction_label.setText("Chuẩn bị...")
        self.distance_label.clear()

    def _on_camera_started(self):
        # Clear text trong camera_view để sẵn sàng hiển thị frame
        self.camera_view.clear()
        self.camera_view.setStyleSheet(
            f"background-color: #000; border: 3px solid {Theme.PRIMARY}; border-radius: 200px;"
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
            PoseType.FRONTAL: "👤 NHÌN THẲNG vào camera",
            PoseType.LEFT: "👈 XOAY MẶT SANG TRÁI",
            PoseType.RIGHT: "👉 XOAY MẶT SANG PHẢI",
            PoseType.UP: "⬆️ NGẨNG ĐẦU LÊN",
            PoseType.DOWN: "⬇️ CÚI ĐẦU XUỐNG",
        }

        msg = f"{step_num}/{total}: {pose_name}\n\n{instructions.get(current_pose, '')}\n\n👉 Nhấn nút CHỤP khi sẵn sàng"
        self.instruction_label.setText(msg)

    # ------------------------------- Frame loop ------------------------------ #
    @Slot(np.ndarray)
    def _on_frame(self, frame: np.ndarray):
        self.latest_frame = frame.copy()  # Lưu frame mới nhất
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
        
        # Cập nhật UI hướng dẫn
        if distance_status == DistanceStatus.NO_FACE:
            self.distance_label.setText("❌ Không thấy khuôn mặt")
            self.distance_label.setStyleSheet("color: #FF6B6B; font-size: 16px;")
            self.capture_btn.setEnabled(False)
        elif distance_status == DistanceStatus.TOO_FAR:
            self.distance_label.setText(f"⚠️ {pose_instruction}")
            self.distance_label.setStyleSheet("color: #FFD700; font-size: 16px;")
            self.capture_btn.setEnabled(False)
        elif distance_status == DistanceStatus.TOO_CLOSE:
            self.distance_label.setText(f"⚠️ {pose_instruction}")
            self.distance_label.setStyleSheet("color: #FFD700; font-size: 16px;")
            self.capture_btn.setEnabled(False)
        else:
            # Distance OK -> Check Pose
            if pose_ok:
                 self.distance_label.setText(f"✅ {pose_instruction}")
                 self.distance_label.setStyleSheet(f"color: {Theme.SECONDARY_GREEN}; font-size: 16px;")
                 self.capture_btn.setEnabled(True)
            else:
                 self.distance_label.setText(f"ℹ️ {pose_instruction}")
                 self.distance_label.setStyleSheet("color: #FFD700; font-size: 16px;")
                 self.capture_btn.setEnabled(False)

    def _on_manual_capture(self):
        """Xử lý khi người dùng nhấn nút Chụp - Tối ưu hóa: Dùng luôn kết quả AI đã cache."""
        # Lấy kết quả AI mới nhất
        if not self.last_ai_result or not self.last_ai_result.get("has_face"):
             self.distance_label.setText("❌ Chưa có dữ liệu khuôn mặt")
             return

        # Kiểm tra lại trạng thái lần cuối (an toàn)
        dist_status = self.last_ai_result["distance_status"]
        pose_ok = self.last_ai_result["pose_ok"]
        
        if dist_status != DistanceStatus.OK:
             self.distance_label.setText("❌ Khoảng cách không hợp lệ")
             return
             
        # Lấy dữ liệu đã tính toán sẵn
        embedding = self.last_ai_result["embedding"]
        face_box = self.last_ai_result["face_box"]
        frame_analyzed = self.last_ai_result["frame"] # Frame đồng bộ với kết quả AI
        
        if embedding is None or frame_analyzed is None:
             self.distance_label.setText("❌ Dữ liệu lỗi (No embedding/frame)")
             return

        # Crop khuôn mặt từ frame đã analyze (đảm bảo box khớp với frame)
        x, y, w, h = face_box
        # Expand box một chút để crop đẹp hơn (tùy chọn, ở đây giữ nguyên logic cũ hoặc thêm padding)
        # Logic cũ: cropped = frame[y:y+h, x:x+w]
        
        # Thêm padding an toàn
        img_h, img_w = frame_analyzed.shape[:2]
        # x, y, w, h are integers
        cropped = frame_analyzed[y : y + h, x : x + w]
        
        if cropped.size == 0:
             self.distance_label.setText("❌ Lỗi cắt ảnh")
             return

        # Lưu dữ liệu
        current_pose = self.POSE_SEQUENCE[self.current_step_index]
        self.captured_data.append((current_pose, embedding, cropped))
        self._mark_step_done(current_pose)
        
        # Hiệu ứng chụp (Optional: Playsound or Flash)
        
        # Chuyển bước tiếp theo
        self.current_step_index += 1
        if self.current_step_index >= len(self.POSE_SEQUENCE):
            self.stop()
            self.finished.emit(self.captured_data)
        else:
            self._update_instruction()
            self.capture_btn.setEnabled(False)

    def _draw_ui_overlay(self, frame: np.ndarray):
        if not self.last_ai_result:
            self._display_frame(frame)
            return

        display_frame = frame.copy()
        
        # Lấy trạng thái từ dict result (có thể là của frame trước, nhưng dùng để vẽ overlay cho frame hiện tại)
        # Lưu ý: frame input của hàm này là frame MỚI NHẤT từ camera, không phải frame trong result.
        # Overlay có thể bị lệch nhẹ nếu vật thể di chuyển nhanh, nhưng chấp nhận được cho realtime feedback.
        
        dist_status = self.last_ai_result.get("distance_status", DistanceStatus.NO_FACE)
        pose_ok = self.last_ai_result.get("pose_ok", False)
        
        border_color = Theme.DANGER_RED
        if dist_status == DistanceStatus.OK and pose_ok:
            border_color = Theme.SECONDARY_GREEN
        elif dist_status == DistanceStatus.OK:
            border_color = "#FFD700" # Warning color for wrong pose
            
        h, w = display_frame.shape[:2]
        color_bgr = self._hex_to_bgr(border_color)
        cv2.rectangle(display_frame, (10, 10), (w - 10, h - 10), color_bgr, 3)

        # Hiển thị giá trị Ratio ở góc dưới bên trái để debug
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

    # ------------------------- Capture & finish flow ------------------------ #
    def _mark_step_done(self, pose: PoseType):
        """Đánh dấu bước đã hoàn thành."""
        lbl = self.checklist_labels[pose]
        lbl.setText(f"✅  {self.POSE_NAMES[pose]}")
        lbl.setStyleSheet(
            f"color: {Theme.SECONDARY_GREEN}; font-size: 16px; padding: 8px; font-weight: bold;"
        )

    def _on_cancel(self):
        self.stop()
        self.finished.emit([])

    def _on_camera_error(self, msg: str):
        self.instruction_label.setText(f"Lỗi camera: {msg}")
        self.distance_label.setText("Vui lòng kiểm tra lại camera.")

    # -------------------------- Helper hiển thị ----------------------------- #
    def _display_frame(self, frame: np.ndarray):
        # Đảm bảo clear text nếu còn (first frame)
        if self.camera_view.text():
            self.camera_view.clear()
            self.camera_view.setStyleSheet(
                f"background-color: #000; border: 3px solid {Theme.PRIMARY}; border-radius: 200px;"
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
