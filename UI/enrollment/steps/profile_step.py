from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFrame)
from PySide6.QtCore import Qt, Signal
from UI.styles import Theme

class ProfileStep(QWidget):
    next_step = Signal(str, str) # Emits (name, id)

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
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Full Name")
        modal_layout.addWidget(self.name_input)
        
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Employee ID")
        modal_layout.addWidget(self.id_input)
        
        # Next Button
        self.start_btn = QPushButton("Start Capture Sequence ->")
        self.start_btn.setProperty("class", "cta_btn")
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self.on_next)
        modal_layout.addWidget(self.start_btn)
        
        layout.addWidget(modal)

    def on_next(self):
        name = self.name_input.text().strip()
        emp_id = self.id_input.text().strip()
        
        if name and emp_id:
            self.next_step.emit(name, emp_id)
            
    def clear_fields(self):
        self.name_input.clear()
        self.id_input.clear()