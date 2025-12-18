"""
Success View - Hiển thị thông tin user sau khi authentication thành công
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from UI.styles import Theme


class SuccessView(QWidget):
    """UI hiển thị thông tin user sau authentication thành công"""
    
    # Signal để quay lại authentication
    back_to_auth = Signal()
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 600)
        self.init_ui()
    
    def init_ui(self):
        """Khởi tạo UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(30)
        
        # Frame chính
        main_frame = QFrame()
        main_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(5, 8, 22, 200);
                border: 2px solid {Theme.SECONDARY_GREEN};
                border-radius: 16px;
                padding: 40px;
            }}
        """)
        main_frame.setFixedSize(600, 450)
        
        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setAlignment(Qt.AlignCenter)
        frame_layout.setSpacing(25)
        
        # Icon success
        success_icon = QLabel("✓")
        success_icon.setAlignment(Qt.AlignCenter)
        success_icon.setStyleSheet(f"""
            color: {Theme.SECONDARY_GREEN};
            font-size: 80px;
            font-weight: bold;
        """)
        frame_layout.addWidget(success_icon)
        
        # Title
        title_label = QLabel("AUTHENTICATION SUCCESSFUL")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            color: {Theme.SECONDARY_GREEN};
            font-size: 28px;
            font-weight: bold;
            letter-spacing: 2px;
        """)
        frame_layout.addWidget(title_label)
        
        # Welcome message
        self.welcome_label = QLabel("Welcome!")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setStyleSheet(f"""
            color: {Theme.TEXT_WHITE};
            font-size: 24px;
            font-weight: 300;
            letter-spacing: 1px;
        """)
        frame_layout.addWidget(self.welcome_label)
        
        # User info Container
        self.info_container = QFrame()
        self.info_container.setProperty("class", "glass_panel")
        self.info_container.setMinimumHeight(150)
        self.info_grid = QVBoxLayout(self.info_container)
        self.info_grid.setSpacing(10)
        
        self.info_labels = {}
        for key in ["ID", "Email", "SĐT", "Ngày sinh"]:
            lbl = QLabel(f"{key}: -")
            lbl.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 16px;")
            self.info_grid.addWidget(lbl)
            self.info_labels[key] = lbl
            
        frame_layout.addWidget(self.info_container)
        
        # Access granted message
        access_label = QLabel("Access Granted")
        access_label.setAlignment(Qt.AlignCenter)
        access_label.setStyleSheet(f"""
            color: {Theme.PRIMARY};
            font-size: 18px;
            font-weight: bold;
            letter-spacing: 2px;
            margin-top: 10px;
        """)
        frame_layout.addWidget(access_label)
        
        frame_layout.addStretch()
        
        # Button quay lại
        back_button = QPushButton("Continue Authentication")
        back_button.setFixedHeight(50)
        back_button.setCursor(Qt.PointingHandCursor)
        back_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: {Theme.TEXT_WHITE};
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {Theme.SECONDARY_GREEN};
            }}
            QPushButton:pressed {{
                background-color: #00cc7a;
            }}
        """)
        back_button.clicked.connect(self.back_to_auth.emit)
        frame_layout.addWidget(back_button)
        
        layout.addWidget(main_frame, alignment=Qt.AlignCenter)
    
    def show_success(self, user_data: dict):
        """Hiển thị thông tin user thành công"""
        fullname = user_data.get("fullname", "Unknown")
        self.welcome_label.setText(f"Chào mừng, {fullname}!")
        
        self.info_labels["ID"].setText(f"ID: {user_data.get('id', 'N/A')}")
        self.info_labels["Email"].setText(f"Email: {user_data.get('email', 'N/A')}")
        self.info_labels["SĐT"].setText(f"SĐT: {user_data.get('phone', 'N/A')}")
        self.info_labels["Ngày sinh"].setText(f"Ngày sinh: {user_data.get('dob', 'N/A')}")
    
    def _get_current_time(self) -> str:
        """Lấy thời gian hiện tại"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Preview
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Mock Theme
    if not hasattr(Theme, 'PRIMARY'):
        class MockTheme:
            PRIMARY = "#00f4ff"
            SECONDARY_GREEN = "#00ff9d"
            TEXT_WHITE = "#ffffff"
            TEXT_GRAY = "#a0a0a0"
            BACKGROUND = "#050816"
        Theme = MockTheme
    
    app.setStyleSheet(f"QWidget {{ background-color: {Theme.BACKGROUND}; }}")
    
    window = SuccessView()
    window.show_success("USR001", "Nguyễn Văn A")
    window.show()
    
    sys.exit(app.exec())
