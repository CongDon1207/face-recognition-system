from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QMessageBox)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap, QImage
from UI.styles import Theme
import cv2
import numpy as np
from common.camera import CameraThread
from modules.face_analyzer import FaceAnalyzer
from modules.authenticator import Authenticator
import time

class AuthenticationView(QWidget):
    """
    Authentication UI - Camera-based face recognition with liveness detection
    Layout: Camera panel ngang → Viewport đứng ở giữa → HUD góc dưới-trái
    """
    
    # Signal phát ra khi authentication thành công
    authentication_success = Signal(str, str)  # (user_id, fullname)
    
    def __init__(self):
        super().__init__()
        self.is_checking = False
        self.ear_value = 0.0
        self.fps_value = 0.0
        
        # Backend components
        self.camera_thread = None
        # Auto-detect GPU (giống enrollment)
        self.face_analyzer = FaceAnalyzer()
        self.authenticator = Authenticator(threshold=0.4)
        
        # Authentication state
        self.last_frame_time = 0
        self.auth_cooldown = 2.0  # 2 giây giữa các lần thử authentication
        self.last_auth_time = 0
        self.frame_counter = 0
        self.PROCESS_EVERY_N_FRAMES = 5  # Chỉ xử lý 1/5 frames để giảm lag CPU
        self.last_ai_result = {}  # Lưu kết quả AI để vẽ overlay (giống enrollment)
        
        # Đặt kích thước tối thiểu để tránh widget bị chồng lên nhau
        self.setMinimumSize(900, 650)
        
        self.init_ui()
        
    def init_ui(self):
        # Main Layout - Vertical: Camera panel trên, Title dưới
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 50, 40, 50)
        main_layout.setSpacing(0)  # Không dùng spacing mặc định
        main_layout.setAlignment(Qt.AlignCenter)
        
        # --- Camera Panel (khung lớn nằm ngang) ---
        camera_panel = self.create_camera_panel()
        main_layout.addWidget(camera_panel, alignment=Qt.AlignCenter)
        
        # Khoảng cách cố định giữa panel và title
        main_layout.addSpacing(10)
        
        # --- Title: IDENTIFICATION (nằm BÊN NGOÀI camera panel) ---
        title_label = QLabel("IDENTIFICATION")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            color: {Theme.TEXT_WHITE};
            font-size: 28px;
            font-weight: 300;
            letter-spacing: 3px;
        """)
        main_layout.addWidget(title_label, alignment=Qt.AlignCenter)
        
        
        # --- Instruction Text ---
        instruction_label = QLabel("Please look directly at the camera")
        instruction_label.setAlignment(Qt.AlignCenter)
        instruction_label.setStyleSheet(f"""
            color: {Theme.TEXT_GRAY};
            font-size: 15px;
            letter-spacing: 0.5px;
        """)
        main_layout.addWidget(instruction_label, alignment=Qt.AlignCenter)
        
    def create_camera_panel(self):
        """
        Tạo camera panel lớn với:
        - Camera viewport ở TRUNG TÂM
        - HUD Liveness ở góc dưới-trái PANEL (không đụng camera)
        """
        # Outer panel - nằm ngang, viền neon cyan
        panel = QFrame()
        panel.setFixedSize(900, 420)
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(5, 8, 22, 200);
                border: 2px solid {Theme.PRIMARY};
                border-radius: 12px;
            }}
        """)
        
        # --- Camera Viewport (ở TRUNG TÂM panel) ---
        self.camera_viewport = QFrame(panel)
        self.camera_viewport.setFixedSize(400, 360)
        self.camera_viewport.setStyleSheet(f"""
            QFrame {{
                background-color: #000000;
                border: 2px solid {Theme.PRIMARY};
                border-radius: 10px;
            }}
        """)
        
        # Position viewport ở chính giữa panel
        viewport_x = (900 - 400) // 2  # Center horizontally
        viewport_y = (420 - 360) // 2  # Center vertically
        self.camera_viewport.move(viewport_x, viewport_y)
        
        # Viewport content - watermark text
        viewport_layout = QVBoxLayout(self.camera_viewport)
        viewport_layout.setAlignment(Qt.AlignCenter)
        
        self.camera_status = QLabel("Camera Feed Inactive")
        self.camera_status.setAlignment(Qt.AlignCenter)
        self.camera_status.setStyleSheet(f"""
            color: rgba(160, 160, 160, 60);
            font-size: 13px;
            letter-spacing: 1px;
        """)
        viewport_layout.addWidget(self.camera_status)
        
        # --- HUD Liveness (góc TRÁI-DƯỚI của PANEL, không đụng camera) ---
        self.hud_frame = QFrame(panel)
        self.hud_frame.setFixedSize(200, 90)
        self.hud_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 0, 0, 230);
                border: 1px solid {Theme.PRIMARY};
                border-radius: 6px;
            }}
        """)
        
        # Position HUD ở góc trái-dưới panel (không đè lên camera)
        hud_x = 20  # 20px từ cạnh trái panel
        hud_y = 420 - 90 - 20  # 20px từ đáy panel
        self.hud_frame.move(hud_x, hud_y)
        
        # HUD content - 3 dòng text
        hud_layout = QVBoxLayout(self.hud_frame)
        hud_layout.setContentsMargins(15, 12, 15, 12)
        hud_layout.setSpacing(6)
        hud_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        hud_style = f"""
            color: {Theme.PRIMARY};
            font-size: 11px;
            font-weight: bold;
            font-family: 'Consolas', 'Courier New', monospace;
            letter-spacing: 1px;
        """
        
        self.liveness_label = QLabel("LIVENESS: CHECKING...")
        self.liveness_label.setStyleSheet(hud_style)
        hud_layout.addWidget(self.liveness_label)
        
        self.ear_label = QLabel("EAR: 0.28")
        self.ear_label.setStyleSheet(hud_style)
        hud_layout.addWidget(self.ear_label)
        
        self.fps_label = QLabel("FPS: 30.0")
        self.fps_label.setStyleSheet(hud_style)
        hud_layout.addWidget(self.fps_label)
        
        # --- Message Status (Ở DƯỚI camera, hiển thị trạng thái detected) ---
        self.status_message = QLabel("")
        self.status_message.setParent(panel)
        self.status_message.setFixedSize(400, 60)
        self.status_message.setAlignment(Qt.AlignCenter)
        self.status_message.setWordWrap(True)
        self.status_message.setStyleSheet(f"""
            color: {Theme.PRIMARY};
            font-size: 16px;
            font-weight: bold;
            letter-spacing: 1px;
            background-color: transparent;
            border: none;
            padding: 5px;
        """)
        # Position DƯỚI camera (cùng x với camera, y = camera.bottom + spacing)
        msg_x = viewport_x
        msg_y = viewport_y + 360 + 5  # 5px dưới camera
        self.status_message.move(msg_x, msg_y)
        self.status_message.hide()  # Ẩn ban đầu
        
        return panel
        
    # --- Public Methods for Integration ---
    
    def start_authentication(self):
        """Bắt đầu quá trình xác thực"""
        if self.camera_thread and self.camera_thread.isRunning():
            return  # Camera đã chạy
        
        self.is_checking = True
        self.camera_status.setText("Initializing camera...")
        self.camera_status.setStyleSheet(f"""
            color: rgba(160, 160, 160, 100);
            font-size: 13px;
            letter-spacing: 1px;
        """)
        self.liveness_label.setText("LIVENESS: READY")
        self.update_hud_style(Theme.PRIMARY)
        
        print("Authentication started - Initializing models...")
        
        # Khởi tạo models trước (để không block UI thread)
        try:
            self.face_analyzer._ensure_models()
            print("Face analyzer models loaded successfully")
        except Exception as e:
            print(f"Warning: Could not pre-load models: {e}")
        
        # Khởi động camera thread
        self.camera_thread = CameraThread(camera_id=0)
        self.camera_thread.frame_captured.connect(self._on_frame_captured)
        self.camera_thread.error_occurred.connect(self._on_camera_error)
        self.camera_thread.start()
        
        print("Camera thread started")
        
    def stop_authentication(self):
        """Dừng xác thực"""
        self.is_checking = False
        
        # Dừng camera thread
        if self.camera_thread and self.camera_thread.isRunning():
            self.camera_thread.stop()
            self.camera_thread.wait(2000)  # Đợi tối đa 2 giây
            if self.camera_thread.isRunning():
                print("Warning: Camera thread did not stop gracefully")
                self.camera_thread.terminate()
            self.camera_thread = None
        
        self.camera_status.setText("Camera Feed Inactive")
        self.camera_status.setStyleSheet(f"""
            color: rgba(160, 160, 160, 60);
            font-size: 13px;
            letter-spacing: 1px;
        """)
        print("Authentication stopped")
        
    def _on_frame_captured(self, frame: np.ndarray):
        """Xử lý frame mới từ camera."""
        current_time = time.time()
        
        # Tính FPS - FIX: check để tránh division by zero
        if self.last_frame_time > 0:
            time_diff = current_time - self.last_frame_time
            fps = 1.0 / time_diff if time_diff > 0 else 0.0
        else:
            fps = 0.0
        self.last_frame_time = current_time
        
        # Tăng frame counter
        self.frame_counter += 1
        
        # CHỈ PROCESS FACE DETECTION trên 1/5 frames để giảm lag CPU
        should_process = (self.frame_counter % self.PROCESS_EVERY_N_FRAMES == 0)
        
        # Run face detection và authentication (chỉ trên frame được chọn)
        if should_process:
            try:
                # Đảm bảo face_analyzer đã được init
                self.face_analyzer._ensure_models()
                
                # Sử dụng analyze_frame để có distance status (như enrollment)
                from modules.face_analyzer import PoseType
                result = self.face_analyzer.analyze_frame(frame, PoseType.FRONTAL)
                
                # Lưu result để vẽ overlay (ngay cả khi không có face)
                self.last_ai_result = result
                
                if result["has_face"]:
                    embedding = result["embedding"]
                    distance_status = result["distance_status"]
                    
                    # CHECK KHOẢNG CÁCH VÀ AUTHENTICATION
                    from modules.face_analyzer import DistanceStatus
                    if distance_status == DistanceStatus.TOO_FAR:
                        self._show_instruction("Lại gần hơn!")
                        self.update_liveness_info(ear=0.0, fps=fps, is_live=False)
                        
                    elif distance_status == DistanceStatus.TOO_CLOSE:
                        self._show_instruction("Lùi xa hơn!")
                        self.update_liveness_info(ear=0.0, fps=fps, is_live=False)
                        
                    elif distance_status == DistanceStatus.OK:
                        # Khoảng cách OK - Thử authentication nếu đủ cooldown
                        if current_time - self.last_auth_time > self.auth_cooldown:
                            success, user_id, auth_distance = self.authenticator.authenticate(embedding)
                            
                            if success:
                                # AUTHENTICATED
                                user_info = self.authenticator.get_user_info(user_id)
                                if user_info:
                                    self._show_success(user_info['fullname'], auth_distance)
                                    self.authentication_success.emit(user_id, user_info['fullname'])
                            else:
                                # FAILED
                                self._show_failed(auth_distance)
                            
                            self.last_auth_time = current_time
                        else:
                            # Cooldown
                            self._show_instruction("Đang xử lý...")
                        
                        # Update HUD
                        self.update_liveness_info(ear=0.0, fps=fps, is_live=True)
                else:
                    # Không có khuôn mặt
                    self._show_instruction("Không tìm thấy khuôn mặt")
                    self.update_liveness_info(ear=0.0, fps=fps, is_live=False)
            
            except Exception as e:
                # Lỗi xử lý
                print(f"Error processing frame: {e}")
                import traceback
                traceback.print_exc()
                self.last_ai_result = {}
        
        # LUÔN vẽ overlay (giống enrollment) - dù có process hay không
        self._draw_ui_overlay(frame)
    
    def _draw_ui_overlay(self, frame: np.ndarray):
        """Vẽ circle overlay dựa trên AI result (giống enrollment)."""
        if not self.last_ai_result:
            # Chưa có result - hiển thị frame gốc
            self._display_frame(frame)
            return
        
        display_frame = frame.copy()
        from modules.face_analyzer import DistanceStatus
        
        dist_status = self.last_ai_result.get("distance_status", DistanceStatus.NO_FACE)
        has_face = self.last_ai_result.get("has_face", False)
        
        # Xác định màu circle dựa trên trạng thái
        if not has_face:
            # Đỏ khi không có face
            border_color = Theme.DANGER_RED
        elif dist_status == DistanceStatus.TOO_FAR or dist_status == DistanceStatus.TOO_CLOSE:
            # Vàng khi quá xa/quá gần
            border_color = "#FFD700"
        elif dist_status == DistanceStatus.OK:
            # Xanh lá khi OK (sẽ thay đổi sau khi authenticate)
            # Kiểm tra xem có đang cooldown không
            import time
            if time.time() - self.last_auth_time <= self.auth_cooldown:
                # Nếu vừa auth xong - giữ màu result (xanh/đỏ tùy success/fail)
                # Check message để biết success hay fail
                current_msg = self.camera_status.text()
                if "AUTHENTICATED" in current_msg:
                    border_color = Theme.SECONDARY_GREEN
                elif "FAILED" in current_msg:
                    border_color = Theme.DANGER_RED
                else:
                    border_color = "#FFD700"
            else:
                border_color = Theme.SECONDARY_GREEN
        else:
            border_color = Theme.DANGER_RED
        
        # Vẽ circle (giống enrollment - dùng ellipse)
        h, w = display_frame.shape[:2]
        color_bgr = self._hex_to_bgr(border_color)
        
        min_dim = min(h, w)
        center = (w // 2, h // 2)
        axes = (int(min_dim * 0.36), int(min_dim * 0.48))
        cv2.ellipse(display_frame, center, axes, 0, 0, 360, color_bgr, 4)
        
        # Hiển thị frame với overlay
        self._display_frame(display_frame)
    
    def _hex_to_bgr(self, hex_color: str) -> tuple[int, int, int]:
        """Convert hex color to BGR tuple (giống enrollment)."""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return b, g, r
    
    def _display_frame(self, frame: np.ndarray):
        """Hiển thị frame lên camera viewport."""
        try:
            # Resize frame to fit viewport (400x360)
            frame_resized = cv2.resize(frame, (400, 360))
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            
            # Convert to QImage - Copy array để đảm bảo data stability
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            # Sử dụng tobytes() thay vì .data.copy()
            q_image = QImage(frame_rgb.tobytes(), w, h, bytes_per_line, QImage.Format_RGB888).copy()
            
            # Convert to QPixmap và hiển thị
            pixmap = QPixmap.fromImage(q_image)
            
            # Tạo QLabel để hiển thị nếu chưa có
            if not hasattr(self, 'camera_label'):
                print("[DEBUG] Creating camera_label for first time")
                self.camera_label = QLabel(self.camera_viewport)
                self.camera_label.setFixedSize(400, 360)
                self.camera_label.setAlignment(Qt.AlignCenter)
                self.camera_label.setScaledContents(False)
                # QUAN TRỌNG: Hiển thị label và đưa lên trên cùng
                self.camera_label.show()
                self.camera_label.raise_()
                # ẨN text "Camera Feed Inactive" khi camera đã hoạt động
                self.camera_status.hide()
            
            self.camera_label.setPixmap(pixmap)
            self.camera_label.update()  # Force update
            # print(f"[DEBUG] Frame displayed successfully")  # Bỏ log để giảm spam
        except Exception as e:
            print(f"[ERROR] Failed to display frame: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_camera_error(self, error_msg: str):
        """Xử lý lỗi camera."""
        self.camera_status.setText(f"Camera Error: {error_msg}")
        self.camera_status.setStyleSheet(f"""
            color: {Theme.SECONDARY_RED};
            font-size: 12px;
            letter-spacing: 1px;
        """)
        print(f"Camera error: {error_msg}")
    
    def _show_success(self, fullname: str, distance: float):
        """Hiển thị kết quả authentication thành công (dưới camera)."""
        self.status_message.show()
        self.status_message.raise_()
        self.status_message.setText(f"✓ AUTHENTICATED - Access Granted: {fullname}")
        self.status_message.setStyleSheet(f"""
            color: {Theme.SECONDARY_GREEN};
            font-size: 16px;
            font-weight: bold;
            letter-spacing: 1px;
            background-color: transparent;
            border: none;
            padding: 5px;
        """)
        print(f"✓ AUTHENTICATION SUCCESS: {fullname} (distance: {distance:.3f})")
    
    def _show_failed(self, distance: float):
        """Hiển thị kết quả authentication thất bại (dưới camera)."""
        self.status_message.show()
        self.status_message.raise_()
        self.status_message.setText(f"✗ AUTHENTICATION FAILED - Unauthorized Access")
        self.status_message.setStyleSheet(f"""
            color: {Theme.SECONDARY_RED};
            font-size: 16px;
            font-weight: bold;
            letter-spacing: 1px;
            background-color: transparent;
            border: none;
            padding: 5px;
        """)
        print(f"✗ AUTHENTICATION FAILED: Unknown person (distance: {distance:.3f})")
    
    def _show_instruction(self, message: str):
        """Hiển thị hướng dẫn lên UI (dưới camera)."""
        self.status_message.show()
        self.status_message.raise_()
        self.status_message.setText(message)
        self.status_message.setStyleSheet(f"""
            color: {Theme.PRIMARY};
            font-size: 16px;
            font-weight: bold;
            letter-spacing: 1px;
            background-color: transparent;
            border: none;
            padding: 5px;
        """)
    
    def _show_checking(self, distance: float):
        """Hiển thị trạng thái checking (DEPRECATED - dùng _show_failed thay thế)."""
        self._show_failed(distance)
    
    def update_camera_frame(self, frame):
        """DEPRECATED: Sử dụng _on_frame_captured() thay thế."""
        pass
        
    def update_liveness_info(self, ear: float, fps: float, is_live: bool):
        """
        Cập nhật thông tin liveness detection
        
        Args:
            ear: Eye Aspect Ratio
            fps: Frames per second
            is_live: Trạng thái phát hiện người thật
        """
        self.ear_value = ear
        self.fps_value = fps
        
        self.ear_label.setText(f"EAR: {ear:.2f}")
        self.fps_label.setText(f"FPS: {fps:.1f}")
        
        if is_live:
            self.liveness_label.setText("LIVENESS: VERIFIED")
            self.update_hud_style(Theme.SECONDARY_GREEN)
        else:
            self.liveness_label.setText("LIVENESS: CHECKING...")
            self.update_hud_style(Theme.PRIMARY)
    
    def update_hud_style(self, color: str):
        """Cập nhật màu cho HUD labels"""
        hud_style = f"""
            color: {color};
            font-size: 11px;
            font-weight: bold;
            font-family: 'Consolas', 'Courier New', monospace;
            letter-spacing: 1px;
        """
        self.liveness_label.setStyleSheet(hud_style)
        self.ear_label.setStyleSheet(hud_style)
        self.fps_label.setStyleSheet(hud_style)
            
    def show_authentication_result(self, success: bool, user_name: str = None):
        """
        Hiển thị kết quả xác thực
        
        Args:
            success: Xác thực thành công hay không
            user_name: Tên người dùng được nhận diện
        """
        if success and user_name:
            self.camera_status.setText(f"Welcome, {user_name}!")
            self.camera_status.setStyleSheet(f"""
                color: {Theme.SECONDARY_GREEN};
                font-size: 15px;
                font-weight: bold;
                letter-spacing: 1px;
            """)
        else:
            self.camera_status.setText("Authentication Failed")
            self.camera_status.setStyleSheet(f"""
                color: {Theme.SECONDARY_RED};
                font-size: 15px;
                font-weight: bold;
                letter-spacing: 1px;
            """)


# --- Standalone Preview ---
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    # Mock Theme if running standalone
    if not hasattr(Theme, 'PRIMARY'):
        class MockTheme:
            PRIMARY = "#00f4ff"
            SECONDARY_GREEN = "#00ff9d"
            SECONDARY_RED = "#ff4d4d"
            TEXT_WHITE = "#ffffff"
            TEXT_GRAY = "#a0a0a0"
            BACKGROUND = "#050816"
        Theme = MockTheme
    
    app = QApplication(sys.argv)
    
    # Apply dark background
    app.setStyleSheet(f"""
        QWidget {{
            background-color: {Theme.BACKGROUND};
        }}
    """)
    
    window = AuthenticationView()
    window.setWindowTitle("Authentication Preview")
    window.resize(1000, 700)
    window.show()
    
    # Simulate liveness update after 2s
    from PySide6.QtCore import QTimer
    def simulate_liveness():
        window.update_liveness_info(ear=0.32, fps=28.5, is_live=True)
    QTimer.singleShot(2000, simulate_liveness)
    
    sys.exit(app.exec())
