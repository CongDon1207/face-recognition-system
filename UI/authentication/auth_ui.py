from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from UI.styles import Theme

class AuthenticationView(QWidget):
    """
    Authentication UI - Camera-based face recognition with liveness detection
    Layout: Camera panel ngang → Viewport đứng ở giữa → HUD góc dưới-trái
    """
    
    def __init__(self):
        super().__init__()
        self.is_checking = False
        self.ear_value = 0.0
        self.fps_value = 0.0
        
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
        
        return panel
        
    # --- Public Methods for Integration ---
    
    def start_authentication(self):
        """Bắt đầu quá trình xác thực"""
        self.is_checking = True
        self.camera_status.setText("Initializing camera...")
        self.camera_status.setStyleSheet(f"""
            color: rgba(160, 160, 160, 100);
            font-size: 13px;
            letter-spacing: 1px;
        """)
        self.liveness_label.setText("LIVENESS: CHECKING...")
        self.update_hud_style(Theme.PRIMARY)
        
    def stop_authentication(self):
        """Dừng xác thực"""
        self.is_checking = False
        self.camera_status.setText("Camera Feed Inactive")
        self.camera_status.setStyleSheet(f"""
            color: rgba(160, 160, 160, 60);
            font-size: 13px;
            letter-spacing: 1px;
        """)
        
    def update_camera_frame(self, frame):
        """Cập nhật frame từ camera (sẽ implement khi có camera service)"""
        # TODO: Convert frame to QPixmap and display in self.camera_viewport
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