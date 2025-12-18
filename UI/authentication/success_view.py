"""
Success View - Hiển thị thông tin user sau khi authentication thành công
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt, Signal
from UI.styles import Theme


class SuccessView(QWidget):
    """UI hiển thị thông tin user sau authentication thành công"""
    
    back_to_auth = Signal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Khởi tạo UI - Đơn giản và trực tiếp"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(60, 40, 60, 40)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # === Success Icon ===
        success_icon = QLabel("✓")
        success_icon.setAlignment(Qt.AlignCenter)
        success_icon.setStyleSheet(f"color: {Theme.SECONDARY_GREEN}; font-size: 72px; font-weight: bold;")
        main_layout.addWidget(success_icon)
        
        # === Title ===
        title_label = QLabel("XÁC THỰC THÀNH CÔNG")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {Theme.SECONDARY_GREEN}; font-size: 32px; font-weight: bold; letter-spacing: 3px;")
        main_layout.addWidget(title_label)
        
        # === Welcome Message ===
        self.welcome_label = QLabel("Chào mừng!")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 28px; font-weight: 300;")
        main_layout.addWidget(self.welcome_label)
        
        main_layout.addSpacing(20)
        
        # === User Info Card ===
        info_card = QFrame()
        info_card.setFixedWidth(500)
        info_card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 243, 255, 15);
                border: 2px solid {Theme.PRIMARY};
                border-radius: 12px;
            }}
        """)
        
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(30, 25, 30, 25)
        info_layout.setSpacing(12)
        
        # Tạo labels trực tiếp (không dùng dict)
        self.id_label = QLabel("🆔  ID: -")
        self.id_label.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 18px;")
        info_layout.addWidget(self.id_label)
        
        self.email_label = QLabel("📧  Email: -")
        self.email_label.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 18px;")
        info_layout.addWidget(self.email_label)
        
        self.phone_label = QLabel("📱  SĐT: -")
        self.phone_label.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 18px;")
        info_layout.addWidget(self.phone_label)
        
        self.dob_label = QLabel("🎂  Ngày sinh: -")
        self.dob_label.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 18px;")
        info_layout.addWidget(self.dob_label)
        
        main_layout.addWidget(info_card, alignment=Qt.AlignCenter)
        
        main_layout.addSpacing(15)
        
        # === Access Granted ===
        access_label = QLabel("🔓 ACCESS GRANTED")
        access_label.setAlignment(Qt.AlignCenter)
        access_label.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 20px; font-weight: bold; letter-spacing: 2px;")
        main_layout.addWidget(access_label)
        
        main_layout.addStretch()
        
        # === Continue Button ===
        back_button = QPushButton("Tiếp tục xác thực")
        back_button.setFixedSize(300, 50)
        back_button.setCursor(Qt.PointingHandCursor)
        back_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: #000000;
                border: none;
                border-radius: 25px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Theme.SECONDARY_GREEN};
            }}
        """)
        back_button.clicked.connect(self.back_to_auth.emit)
        main_layout.addWidget(back_button, alignment=Qt.AlignCenter)
    
    def show_success(self, user_data: dict):
        """Hiển thị thông tin user thành công"""
        print(f"[SuccessView] show_success called with: {user_data}")
        
        fullname = user_data.get("fullname", "Unknown")
        self.welcome_label.setText(f"Chào mừng, {fullname}!")
        
        # Cập nhật từng label trực tiếp
        user_id = user_data.get('id') or 'N/A'
        email = user_data.get('email') or 'N/A'
        phone = user_data.get('phone') or 'N/A'
        dob = user_data.get('dob') or 'N/A'
        
        self.id_label.setText(f"🆔  ID: {user_id}")
        self.email_label.setText(f"📧  Email: {email}")
        self.phone_label.setText(f"📱  SĐT: {phone}")
        self.dob_label.setText(f"🎂  Ngày sinh: {dob}")
        
        # Force update UI
        self.update()
        
        print(f"[SuccessView] Labels updated - ID={user_id}, Email={email}, Phone={phone}, DOB={dob}")
    
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
