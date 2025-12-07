from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame)
from PySide6.QtCore import Qt, Signal
from UI.styles import Theme

class SuccessStep(QWidget):
    restart = Signal()
    goto_auth = Signal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Success Icon
        success_icon = QLabel("✔")
        success_icon.setAlignment(Qt.AlignCenter)
        success_icon.setStyleSheet(f"""
            font-size: 80px; 
            color: {Theme.SECONDARY_GREEN};
            background-color: rgba(0, 255, 157, 20);
            border-radius: 60px;
            padding: 20px;
        """)
        success_icon.setFixedSize(120, 120)
        layout.addWidget(success_icon, alignment=Qt.AlignCenter)
        
        # Text
        success_msg = QLabel("Enrollment Successful")
        success_msg.setProperty("class", "header_text")
        layout.addWidget(success_msg, alignment=Qt.AlignCenter)
        
        # Summary Card
        card = QFrame()
        card.setProperty("class", "glass_panel")
        card.setFixedWidth(300)
        card_layout = QVBoxLayout(card)
        
        self.summary_name = QLabel("Name Here")
        self.summary_name.setAlignment(Qt.AlignCenter)
        self.summary_name.setStyleSheet("font-size: 20px; font-weight: bold;")
        
        self.summary_id = QLabel("ID: 12345")
        self.summary_id.setAlignment(Qt.AlignCenter)
        self.summary_id.setStyleSheet(f"color: {Theme.TEXT_GRAY};")
        
        card_layout.addWidget(self.summary_name)
        card_layout.addWidget(self.summary_id)
        
        layout.addWidget(card, alignment=Qt.AlignCenter)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        btn_layout.setContentsMargins(0, 30, 0, 0)
        
        enroll_another_btn = QPushButton("Enroll Another")
        enroll_another_btn.setProperty("class", "outline_btn")
        enroll_another_btn.setCursor(Qt.PointingHandCursor)
        enroll_another_btn.clicked.connect(self.restart.emit)
        
        go_auth_btn = QPushButton("Go to Auth")
        go_auth_btn.setProperty("class", "cta_btn")
        go_auth_btn.setCursor(Qt.PointingHandCursor)
        go_auth_btn.clicked.connect(self.goto_auth.emit)
        
        btn_layout.addWidget(enroll_another_btn)
        btn_layout.addWidget(go_auth_btn)
        
        layout.addLayout(btn_layout)

    def set_data(self, name, emp_id):
        self.summary_name.setText(name)
        self.summary_id.setText(f"ID: {emp_id}")
