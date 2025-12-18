"""
About View - Thông tin về ứng dụng
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt
from UI.styles import Theme


class AboutView(QWidget):
    """Trang thông tin về ứng dụng"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(60, 40, 60, 40)
        main_layout.setSpacing(30)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # === Logo & Title ===
        logo_label = QLabel("🔐")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("font-size: 80px;")
        main_layout.addWidget(logo_label)
        
        title_label = QLabel("NEONGLASS")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            color: {Theme.PRIMARY}; 
            font-size: 48px; 
            font-weight: bold;
            letter-spacing: 5px;
        """)
        main_layout.addWidget(title_label)
        
        subtitle = QLabel("Biometric Security System")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 18px; letter-spacing: 2px;")
        main_layout.addWidget(subtitle)
        
        main_layout.addSpacing(20)
        
        # === Info Card ===
        info_card = QFrame()
        info_card.setFixedWidth(600)
        info_card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 243, 255, 10);
                border: 1px solid {Theme.BORDER_COLOR};
                border-radius: 16px;
            }}
        """)
        
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(40, 30, 40, 30)
        info_layout.setSpacing(15)
        
        # Version
        version_row = self._create_info_row("📦 Phiên bản", "1.0.0")
        info_layout.addLayout(version_row)
        
        # Description
        desc_label = QLabel("📝 Mô tả")
        desc_label.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 14px;")
        info_layout.addWidget(desc_label)
        
        desc_content = QLabel(
            "Hệ thống nhận diện khuôn mặt sử dụng công nghệ AI tiên tiến.\n"
            "Hỗ trợ đăng ký khuôn mặt đa góc và xác thực nhanh chóng."
        )
        desc_content.setWordWrap(True)
        desc_content.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 14px; line-height: 1.5;")
        info_layout.addWidget(desc_content)
        
        info_layout.addSpacing(10)
        
        # Tech stack
        tech_label = QLabel("🛠️ Công nghệ")
        tech_label.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 14px;")
        info_layout.addWidget(tech_label)
        
        tech_content = QLabel(
            "• PySide6 (Qt6) - Giao diện người dùng\n"
            "• InsightFace - Nhận diện khuôn mặt\n"
            "• MediaPipe - Phát hiện góc đầu\n"
            "• SQLite - Cơ sở dữ liệu\n"
            "• OpenCV - Xử lý hình ảnh"
        )
        tech_content.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 14px;")
        info_layout.addWidget(tech_content)
        
        info_layout.addSpacing(10)
        
        # Models
        models_row = self._create_info_row("🤖 AI Models", "buffalo_l / buffalo_s")
        info_layout.addLayout(models_row)
        
        main_layout.addWidget(info_card, alignment=Qt.AlignCenter)
        
        main_layout.addStretch()
        
        # === Footer ===
        footer = QLabel("© 2025 Digital Image Processing Project")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 12px;")
        main_layout.addWidget(footer)
    
    def _create_info_row(self, label: str, value: str) -> QHBoxLayout:
        row = QHBoxLayout()
        
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 14px;")
        row.addWidget(lbl)
        
        val = QLabel(value)
        val.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 14px; font-weight: bold;")
        row.addWidget(val)
        
        row.addStretch()
        return row
