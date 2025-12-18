import random
import string
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QDateEdit, QHBoxLayout)
from PySide6.QtCore import Qt, Signal, QDate
from UI.styles import Theme

class ProfileStep(QWidget):
    next_step = Signal(dict) # Emits user_data dict

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Modal Container
        modal = QFrame()
        modal.setProperty("class", "glass_panel")
        modal.setFixedWidth(400)
        modal_layout = QVBoxLayout(modal)
        modal_layout.setSpacing(20)
        modal_layout.setContentsMargins(40, 40, 40, 40)
        
        # User Icon
        icon_label = QLabel("👤")
        icon_label.setAlignment(Qt.AlignCenter)
        # Using inline for icon size as it's specific here, or could move to style
        icon_label.setStyleSheet(f"font-size: 64px; color: {Theme.PRIMARY};")
        modal_layout.addWidget(icon_label)
        
        header = QLabel("New Profile")
        header.setProperty("class", "header_text")
        header.setAlignment(Qt.AlignCenter)
        modal_layout.addWidget(header)
        
        # Inputs
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("User ID")
        self.id_input.setReadOnly(True)
        self.id_input.setStyleSheet(f"background-color: rgba(255, 255, 255, 0.05); color: {Theme.TEXT_GRAY};")
        
        id_layout = QHBoxLayout()
        id_layout.addWidget(self.id_input)
        
        self.reg_id_btn = QPushButton("🔄")
        self.reg_id_btn.setFixedWidth(40)
        self.reg_id_btn.setCursor(Qt.PointingHandCursor)
        self.reg_id_btn.clicked.connect(self._generate_id)
        id_layout.addWidget(self.reg_id_btn)
        modal_layout.addLayout(id_layout)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Tên đầy đủ")
        modal_layout.addWidget(self.name_input)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        modal_layout.addWidget(self.email_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Số điện thoại")
        modal_layout.addWidget(self.phone_input)

        dob_label = QLabel("Ngày sinh:")
        dob_label.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 14px;")
        modal_layout.addWidget(dob_label)

        # Ô chọn ngày sinh dạng box với popup calendar
        self.dob_input = QDateEdit()
        self.dob_input.setCalendarPopup(True)
        self.dob_input.setDate(QDate(2000, 1, 1))
        self.dob_input.setDisplayFormat("dd/MM/yyyy")
        self.dob_input.setStyleSheet(f"""
            QDateEdit {{
                background-color: rgba(0, 0, 0, 50);
                border: 1px solid {Theme.BORDER_COLOR};
                border-radius: 6px;
                color: {Theme.TEXT_WHITE};
                font-size: 14px;
                padding: 10px;
            }}
            QDateEdit::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: right center;
                width: 20px;
                border: none;
                image: none;
            }}
            QDateEdit::down-arrow {{
                image: none;
                width: 0;
                height: 0;
            }}
        """)
        modal_layout.addWidget(self.dob_input)
        
        # Next Button
        self.start_btn = QPushButton("Tiếp tục (Chụp ảnh) ->")
        self.start_btn.setProperty("class", "cta_btn")
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self.on_next)
        modal_layout.addWidget(self.start_btn)
        
        layout.addWidget(modal)
        self._generate_id()

    def _generate_id(self):
        """Tự động sinh ID USR-XXXXXX"""
        rand_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        self.id_input.setText(f"USR-{rand_str}")

    def on_next(self):
        user_data = {
            "id": self.id_input.text(),
            "fullname": self.name_input.text().strip(),
            "email": self.email_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "dob": self.dob_input.date().toString("dd/MM/yyyy")
        }
        
        if user_data["fullname"] and user_data["id"]:
            self.next_step.emit(user_data)
            
    def clear_fields(self):
        self.name_input.clear()
        self.id_input.clear()
        self.email_input.clear()
        self.phone_input.clear()
        self.dob_input.setDate(QDate(2000, 1, 1))