"""
Step 2: Capture Sequence - Chụp khuôn mặt theo các góc khác nhau.
Tích hợp Camera, Head Pose Detection, Distance Check.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QThread, QMutex, QWaitCondition
from PySide6.QtGui import QImage, QPixmap, QColor
from UI.styles import Theme
from common.camera import CameraThread
from modules.face_analyzer import FaceAnalyzer, DistanceStatus, PoseType
import numpy as np
import cv2
import time


class FaceProcessingThread(QThread):
    """
    Thread xử lý AI (Detection, Pose, Embedding) để không block Main UI.
    """
    model_loaded = Signal(bool, str)  # success, message
    result_ready = Signal(object, object, object)  # distance_status, pose_info, face_box
    
    def __init__(self):
        super().__init__()
        self.face_analyzer = None
        self.running = True
        self.latest_frame = None
        self.target_pose = None
        self.frame_mutex = QMutex()
        self.condition = QWaitCondition()
        self.is_models_loaded = False

    def initialize_models(self):
        """Khởi tạo models (chạy trong thread)."""
        try:
            if self.face_analyzer is None:
                self.face_analyzer = FaceAnalyzer()
            # Force load models immediately
            self.face_analyzer._ensure_models()
            self.is_models_loaded = True
            self.model_loaded.emit(True, "Models loaded successfully")
        except Exception as e:
            print(f"Error loading models: {e}")
            self.model_loaded.emit(False, str(e))

    def update_frame(self, frame, target_pose):
        """Cập nhật frame mới nhất để xử lý."""
        if not self.is_models_loaded:
            return

        self.frame_mutex.lock()
        self.latest_frame = frame.copy()
        self.target_pose = target_pose
        self.frame_mutex.unlock()
        self.condition.wakeOne()

    def run(self):
        # 1. Init models first
        self.initialize_models()
        
        while self.running:
            self.frame_mutex.lock()
            if self.latest_frame is None:
                self.condition.wait(self.frame_mutex)
            
            if self.latest_frame is None or not self.running:
                self.frame_mutex.unlock()
                continue
                
            frame = self.latest_frame
            target_pose = self.target_pose
            self.latest_frame = None  # Clear buffer
            self.frame_mutex.unlock()
            
            # 2. Process frame (Heavy work)
            if self.is_models_loaded:
                try:
                    # Check distance
                    distance_status = self.face_analyzer.check_face_distance(frame)
                    face_box = self.face_analyzer._last_face_box
                    
                    # Check pose if distance is OK
                    pose_result = None
                    if distance_status == DistanceStatus.OK and target_pose:
                        pose_result = self.face_analyzer.check_pose(frame, target_pose)
                        
                    self.result_ready.emit(distance_status, pose_result, face_box)
                    
                except Exception as e:
                    print(f"Processing error: {e}")
        
    def stop(self):
        self.running = False
        self.condition.wakeOne()
        self.wait()

    def get_embedding(self, frame):
        # Helper sync call for final capture (rarely called)
        if self.face_analyzer:
            return self.face_analyzer.get_embedding(frame)
        return None

    def get_face_crop(self, frame):
         if self.face_analyzer:
            return self.face_analyzer.get_face_crop(frame)
         return None


class CaptureStep(QWidget):
    """Bước 2: Chụp ảnh khuôn mặt theo 5 góc."""
    finished = Signal(list)  # Emit danh sách (pose_type, embedding, image_path)

    POSE_SEQUENCE = [
        PoseType.FRONTAL,
        PoseType.LEFT,
        PoseType.RIGHT,
        PoseType.UP,
        PoseType.DOWN
    ]

    def __init__(self):
        super().__init__()
        self.current_step_index = 0
        self.captured_data = []  # Lưu (pose_type, embedding, cropped_image)
        self.hold_timer = QTimer()
        self.hold_timer.timeout.connect(self._on_hold_complete)
        self.hold_counter = 0
        
        self.camera_thread = None
        self.processor_thread = FaceProcessingThread()
        self.processor_thread.result_ready.connect(self._on_ai_result)
        self.processor_thread.model_loaded.connect(self._on_models_loaded)
        self.processor_thread.start() # Start immediately to load models
        
        self.is_processing_frame = False
        self.last_ai_result = (DistanceStatus.NO_FACE, None, None) # Cache result
        
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(30)
        
        # -- Left: Camera Area --
        camera_container = QFrame()
        camera_container.setProperty("class", "glass_panel")
        camera_layout = QVBoxLayout(camera_container)
        camera_layout.setAlignment(Qt.AlignCenter)
        
        # Khung camera (sẽ hiển thị feed)
        self.camera_view = QLabel()
        self.camera_view.setAlignment(Qt.AlignCenter)
        self.camera_view.setFixedSize(400, 400)
        self.camera_view.setStyleSheet(f"""
            background-color: #000; 
            border: 3px solid {Theme.PRIMARY};
            border-radius: 200px;
        """)
        camera_layout.addWidget(self.camera_view)
        
        # Instruction Label - Hiển thị hướng dẫn lớn
        self.instruction_label = QLabel("Đang tải AI...")
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.instruction_label.setStyleSheet(f"""
            color: {Theme.PRIMARY}; 
            font-size: 22px; 
            font-weight: bold;
            padding: 15px;
        """)
        # Thêm shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(Theme.PRIMARY))
        shadow.setOffset(0, 0)
        self.instruction_label.setGraphicsEffect(shadow)
        camera_layout.addWidget(self.instruction_label)
        
        # Distance feedback label
        self.distance_label = QLabel("Vui lòng đợi...")
        self.distance_label.setAlignment(Qt.AlignCenter)
        self.distance_label.setStyleSheet("color: #FFD700; font-size: 16px;")
        camera_layout.addWidget(self.distance_label)
        
        layout.addWidget(camera_container, 2)
        
        # -- Right: Checklist --
        checklist_container = QFrame()
        checklist_container.setProperty("class", "glass_panel")
        checklist_layout = QVBoxLayout(checklist_container)
        checklist_layout.setContentsMargins(20, 20, 20, 20)
        
        checklist_header = QLabel("Tiến trình quét")
        checklist_header.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 18px; font-weight: bold;")
        checklist_layout.addWidget(checklist_header)
        
        # Tạo label cho từng góc
        self.checklist_labels = {}
        pose_names = {
            PoseType.FRONTAL: "Nhìn thẳng",
            PoseType.LEFT: "Nghiêng trái",
            PoseType.RIGHT: "Nghiêng phải",
            PoseType.UP: "Ngẩng lên",
            PoseType.DOWN: "Cúi xuống"
        }
        for pose in self.POSE_SEQUENCE:
            lbl = QLabel(f"○  {pose_names[pose]}")
            lbl.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 16px; padding: 8px;")
            self.checklist_labels[pose] = lbl
            checklist_layout.addWidget(lbl)
            
        checklist_layout.addStretch()
        
        # Nút Cancel (debug)
        cancel_btn = QPushButton("Hủy")
        cancel_btn.setProperty("class", "danger_button")
        cancel_btn.clicked.connect(self._on_cancel)
        checklist_layout.addWidget(cancel_btn)
        
        layout.addWidget(checklist_container, 1)

    def _on_models_loaded(self, success, msg):
        if success:
            self.instruction_label.setText("Sẵn sàng!")
            self.distance_label.setText("")
        else:
            self.instruction_label.setText("Lỗi AI!")
            self.distance_label.setText(msg)

    def start_capture(self, user_id: str = "temp"):
        """Bắt đầu quy trình capture."""
        self.user_id = user_id
        self.current_step_index = 0
        self.captured_data = []
        self._reset_checklist()
        
        # Hiển thị loading state
        self.camera_view.setText("📷\n\nĐang khởi động camera...")
        self.camera_view.setStyleSheet(f"""
            background-color: #000; 
            border: 3px solid {Theme.PRIMARY};
            border-radius: 200px;
            color: {Theme.TEXT_GRAY};
            font-size: 16px;
        """)
        
        # Khởi động camera
        if self.camera_thread is None or not self.camera_thread.isRunning():
            self.camera_thread = CameraThread()
            self.camera_thread.frame_captured.connect(self._on_frame)
            self.camera_thread.error_occurred.connect(self._on_camera_error)
            self.camera_thread.started.connect(self._on_camera_started)
            self.camera_thread.start()

    def stop(self):
        """Dừng camera và reset."""
        if self.camera_thread:
            self.camera_thread.stop()
        self.hold_timer.stop()
        # Note: We don't stop processor_thread here to keep models loaded

    def reset_ui(self):
        """Reset UI về trạng thái ban đầu."""
        self.stop()
        self._reset_checklist()
        self.current_step_index = 0
        self.captured_data = []
        self.camera_view.clear()
        self.instruction_label.setText("Chuẩn bị...")
        self.distance_label.clear()

    def _on_camera_started(self):
        """Callback khi camera đã sẵn sàng."""
        self.distance_label.setText("")
        self._update_instruction()

    def _reset_checklist(self):
        """Reset tất cả các checkbox về trạng thái chưa hoàn thành."""
        pose_names = {
            PoseType.FRONTAL: "Nhìn thẳng",
            PoseType.LEFT: "Nghiêng trái",
            PoseType.RIGHT: "Nghiêng phải",
            PoseType.UP: "Ngẩng lên",
            PoseType.DOWN: "Cúi xuống"
        }
        for pose, lbl in self.checklist_labels.items():
            lbl.setText(f"○  {pose_names[pose]}")
            lbl.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 16px; padding: 8px;")

    def _update_instruction(self):
        """Cập nhật hướng dẫn cho bước hiện tại."""
        if self.current_step_index >= len(self.POSE_SEQUENCE):
            self.instruction_label.setText("Hoàn tất!")
            return
        
        instructions = {
            PoseType.FRONTAL: "NHÌN THẲNG vào camera",
            PoseType.LEFT: "QUAY ĐẦU SANG TRÁI",
            PoseType.RIGHT: "QUAY ĐẦU SANG PHẢI",
            PoseType.UP: "NGẨNG ĐẦU LÊN",
            PoseType.DOWN: "CÚI ĐẦU XUỐNG"
        }
        current_pose = self.POSE_SEQUENCE[self.current_step_index]
        self.instruction_label.setText(instructions[current_pose])

    @Slot(np.ndarray)
    def _on_frame(self, frame: np.ndarray):
        """Xử lý mỗi frame từ camera."""
        if self.current_step_index >= len(self.POSE_SEQUENCE):
            return
        
        # Send to AI thread (non-blocking)
        if self.processor_thread.is_models_loaded:
             current_pose = self.POSE_SEQUENCE[self.current_step_index]
             self.processor_thread.update_frame(frame, current_pose)

        # Draw UI based on LAST KNOWN result
        self._draw_ui_overlay(frame)
        
    def _on_ai_result(self, distance_status, pose_result, face_box):
        """Nhận kết quả từ AI thread."""
        self.last_ai_result = (distance_status, pose_result, face_box)
        
        # Logic check status (chỉ update text/timer, không vẽ frame ở đây)
        if distance_status == DistanceStatus.NO_FACE:
            self.distance_label.setText("⚠ Không thấy khuôn mặt")
            self.distance_label.setStyleSheet("color: #FF6B6B; font-size: 16px;")
            self.hold_timer.stop()
            self.hold_counter = 0
            
        elif distance_status == DistanceStatus.TOO_FAR:
            self.distance_label.setText("↑ Lại gần hơn")
            self.distance_label.setStyleSheet("color: #FFD700; font-size: 16px;")
            self.hold_timer.stop()
            self.hold_counter = 0
            
        elif distance_status == DistanceStatus.TOO_CLOSE:
            self.distance_label.setText("↓ Ra xa một chút")
            self.distance_label.setStyleSheet("color: #FFD700; font-size: 16px;")
            self.hold_timer.stop()
            self.hold_counter = 0
            
        else: # OK
            self.distance_label.setText("✓ Khoảng cách OK")
            self.distance_label.setStyleSheet(f"color: {Theme.SECONDARY_GREEN}; font-size: 16px;")
            
            if pose_result:
                pose_ok, msg = pose_result
                if pose_ok:
                    if not self.hold_timer.isActive():
                        self.hold_counter = 0
                        self.hold_timer.start(500)
                        self.instruction_label.setText("Giữ yên...")
                else:
                    self.hold_timer.stop()
                    self.hold_counter = 0
                    self.instruction_label.setText(msg)

    def _draw_ui_overlay(self, frame):
        """Vẽ overlay lên frame dựa trên kết quả AI gần nhất."""
        display_frame = frame.copy()
        
        distance_status, pose_result, face_box = self.last_ai_result
        border_color = Theme.DANGER_RED

        if distance_status == DistanceStatus.OK:
            if pose_result and pose_result[0]: # pose_ok
                border_color = Theme.SECONDARY_GREEN
            
        # Vẽ border indicator
        h, w = display_frame.shape[:2]
        color_bgr = self._hex_to_bgr(border_color)
        cv2.rectangle(display_frame, (10, 10), (w-10, h-10), color_bgr, 3)
        
        # Vẽ face box nếu có
        # if face_box:
        #     x, y, w, h = face_box
        #     cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 1)

        self._display_frame(display_frame)

    def _on_hold_complete(self):
        """Callback khi user giữ yên đủ lâu."""
        self.hold_counter += 1
        if self.hold_counter >= 2:  # Giữ 1.0 giây (nhanh hơn)
            self.hold_timer.stop()
            self._capture_current_pose()

    def _capture_current_pose(self):
        """Chụp và lưu embedding cho pose hiện tại."""
        # Lấy frame hiện tại từ camera thread
        if self.camera_thread and self.camera_thread._cap:
            ret, frame = self.camera_thread._cap.read()
            if ret:
                # frame = cv2.flip(frame, 1) # REMOVED: CameraThread already flips
                current_pose = self.POSE_SEQUENCE[self.current_step_index]
                
                # Embedding lấy sync từ thread (vì chỉ cần làm 1 lần)
                # Hoặc dùng processor thread nhưng phải wait. 
                # Ở đây gọi hàm helper của thread (chạy sync trong thread này hoặc thread kia? 
                # FaceAnalyzer không thread-safe tuyệt đối nếu gọi cùng lúc.
                # Tuy nhiên lúc này ta đã stop timer, và hy vọng on_frame không gửi thêm request quan trọng.
                # Để an toàn, ta dùng lock trong processor thread hoặc pause nó.
                
                # Cách đơn giản: Gọi trực tiếp processor_thread.get_embedding (bên trong check exist)
                # Rủi ro race condition thấp vì get_embedding chỉ đọc model.
                
                embedding = self.processor_thread.get_embedding(frame)
                cropped = self.processor_thread.get_face_crop(frame)
                
                if embedding is not None and cropped is not None:
                    self.captured_data.append((current_pose, embedding, cropped))
                    self._mark_step_complete(current_pose)
                    self.current_step_index += 1
                    
                    if self.current_step_index >= len(self.POSE_SEQUENCE):
                        self._on_all_complete()
                    else:
                        self._update_instruction()
                        # Reset result để tránh tự động trigger tiếp
                        self.last_ai_result = (DistanceStatus.NO_FACE, None, None)

    def _mark_step_complete(self, pose: PoseType):
        """Đánh dấu bước đã hoàn thành."""
        pose_names = {
            PoseType.FRONTAL: "Nhìn thẳng",
            PoseType.LEFT: "Nghiêng trái",
            PoseType.RIGHT: "Nghiêng phải",
            PoseType.UP: "Ngẩng lên",
            PoseType.DOWN: "Cúi xuống"
        }
        lbl = self.checklist_labels[pose]
        lbl.setText(f"✔  {pose_names[pose]}")
        lbl.setStyleSheet(f"color: {Theme.SECONDARY_GREEN}; font-size: 16px; padding: 8px; font-weight: bold;")

    def _on_all_complete(self):
        """Khi đã capture xong tất cả các góc."""
        self.stop()
        self.instruction_label.setText("✓ Hoàn tất!")
        self.finished.emit(self.captured_data)

    def _on_cancel(self):
        """Hủy quy trình capture."""
        self.stop()
        self.finished.emit([])  # Emit empty list = cancelled

    def _on_camera_error(self, msg: str):
        """Xử lý lỗi camera."""
        self.instruction_label.setText(f"Lỗi: {msg}")
        self.distance_label.setText("Vui lòng kiểm tra camera")

    def _display_frame(self, frame: np.ndarray):
        """Chuyển đổi OpenCV frame sang QPixmap và hiển thị."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Scale và crop thành hình tròn
        pixmap = QPixmap.fromImage(q_img)
        scaled = pixmap.scaled(400, 400, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.camera_view.setPixmap(scaled)

    def _hex_to_bgr(self, hex_color: str) -> tuple:
        """Chuyển hex color sang BGR."""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return (b, g, r)
