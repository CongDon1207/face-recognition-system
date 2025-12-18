"""
Profile View - Hiển thị thông tin người dùng hiện tại
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from UI.styles import Theme


class ProfileView(QWidget):
    """Trang thông tin cá nhân của user đang đăng nhập"""
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 20, 40, 20)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignTop)
        
        # === Profile Card ===
        profile_card = QFrame()
        profile_card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 243, 255, 10);
                border: 2px solid {Theme.PRIMARY};
                border-radius: 16px;
            }}
        """)
        
        card_layout = QHBoxLayout(profile_card)
        card_layout.setContentsMargins(40, 30, 40, 30)
        card_layout.setSpacing(40)
        
        # Avatar
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(150, 150)
        self.avatar_label.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(0, 243, 255, 20);
                border: 3px solid {Theme.PRIMARY};
                border-radius: 75px;
            }}
        """)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setText("👤")
        self.avatar_label.setStyleSheet(self.avatar_label.styleSheet() + "font-size: 60px;")
        card_layout.addWidget(self.avatar_label)
        
        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(15)
        
        self.name_label = QLabel("Chưa đăng nhập")
        self.name_label.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 32px; font-weight: bold;")
        info_layout.addWidget(self.name_label)
        
        self.id_label = QLabel("🆔 ID: -")
        self.id_label.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 16px;")
        info_layout.addWidget(self.id_label)
        
        info_layout.addSpacing(10)
        
        # Details grid
        details_layout = QVBoxLayout()
        details_layout.setSpacing(8)
        
        self.email_label = QLabel("📧 Email: -")
        self.email_label.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 16px;")
        details_layout.addWidget(self.email_label)
        
        self.phone_label = QLabel("📱 SĐT: -")
        self.phone_label.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 16px;")
        details_layout.addWidget(self.phone_label)
        
        self.dob_label = QLabel("🎂 Ngày sinh: -")
        self.dob_label.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 16px;")
        details_layout.addWidget(self.dob_label)
        
        self.created_label = QLabel("📅 Ngày tạo: -")
        self.created_label.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 16px;")
        details_layout.addWidget(self.created_label)
        
        info_layout.addLayout(details_layout)
        info_layout.addStretch()
        
        card_layout.addLayout(info_layout, stretch=1)
        
        main_layout.addWidget(profile_card)
        
        # === Status Badge ===
        status_frame = QFrame()
        status_frame.setFixedHeight(60)
        status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 255, 157, 15);
                border: 1px solid {Theme.SECONDARY_GREEN};
                border-radius: 12px;
            }}
        """)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(20, 10, 20, 10)
        
        status_icon = QLabel("✅")
        status_icon.setStyleSheet("font-size: 24px;")
        status_layout.addWidget(status_icon)
        
        status_text = QLabel("Đã xác thực thành công - Quyền truy cập đầy đủ")
        status_text.setStyleSheet(f"color: {Theme.SECONDARY_GREEN}; font-size: 16px; font-weight: bold;")
        status_layout.addWidget(status_text)
        status_layout.addStretch()
        
        main_layout.addWidget(status_frame)
        
        main_layout.addStretch()
    
    def set_user(self, user_data: dict):
        """Cập nhật thông tin user hiển thị"""
        if not user_data:
            return
        
        self.current_user = user_data
        
        fullname = user_data.get("fullname", "Unknown")
        self.name_label.setText(fullname)
        
        self.id_label.setText(f"🆔 ID: {user_data.get('id', '-')}")
        self.email_label.setText(f"📧 Email: {user_data.get('email') or 'Chưa cập nhật'}")
        self.phone_label.setText(f"📱 SĐT: {user_data.get('phone') or 'Chưa cập nhật'}")
        self.dob_label.setText(f"🎂 Ngày sinh: {user_data.get('dob') or 'Chưa cập nhật'}")
        self.created_label.setText(f"📅 Ngày tạo: {user_data.get('created_at') or '-'}")
        
        # Load avatar nếu có
        avatar_path = user_data.get("avatar_path")
        if avatar_path:
            try:
                pixmap = QPixmap(avatar_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(150, 150, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    self.avatar_label.setPixmap(scaled)
                    self.avatar_label.setScaledContents(True)
            except Exception:
                pass
