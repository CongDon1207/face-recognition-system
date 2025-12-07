from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QButtonGroup
from PySide6.QtCore import Qt, Signal
from UI.styles import Theme

class Sidebar(QFrame):
    nav_clicked = Signal(int, str) # Emits (id, label)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(280)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 1. Header
        self.setup_header(layout)
        
        # 2. Navigation
        self.setup_nav(layout)
        
        # Spacer
        layout.addStretch()
        
        # 3. Footer
        self.setup_footer(layout)

    def setup_header(self, parent_layout):
        header_frame = QFrame()
        header_frame.setFixedHeight(120)
        layout = QVBoxLayout(header_frame)
        layout.setAlignment(Qt.AlignCenter)
        
        logo = QLabel("NEONGLASS")
        logo.setObjectName("logo_text")
        logo.setAlignment(Qt.AlignCenter)
        
        slogan = QLabel("Biometric Security")
        slogan.setObjectName("slogan_text")
        slogan.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(logo)
        layout.addWidget(slogan)
        parent_layout.addWidget(header_frame)

    def setup_nav(self, parent_layout):
        nav_frame = QFrame()
        layout = QVBoxLayout(nav_frame)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(10)
        
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_group.buttonClicked.connect(self.on_btn_clicked)
        
        menu_items = [
            (0, "Dashboard"),
            (1, "Authentication"),
            (2, "Enrollment"),
            (3, "Settings")
        ]
        
        for idx, label in menu_items:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setObjectName("nav_btn")
            btn.setProperty("class", "nav_btn")
            btn.setCursor(Qt.PointingHandCursor)
            
            if idx == 0:
                btn.setChecked(True)
                
            self.nav_group.addButton(btn, idx)
            layout.addWidget(btn)
            
        parent_layout.addWidget(nav_frame)

    def setup_footer(self, parent_layout):
        footer_frame = QFrame()
        footer_frame.setObjectName("status_bar")
        footer_frame.setFixedHeight(60)
        layout = QHBoxLayout(footer_frame)
        layout.setContentsMargins(20, 10, 20, 10)
        
        status_dot = QLabel("●")
        status_dot.setObjectName("status_dot")
        
        status_label = QLabel("SYSTEM ONLINE")
        status_label.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 11px; font-weight: bold;")
        
        layout.addWidget(status_dot)
        layout.addWidget(status_label)
        layout.addStretch()
        
        parent_layout.addWidget(footer_frame)

    def on_btn_clicked(self, btn):
        idx = self.nav_group.id(btn)
        self.nav_clicked.emit(idx, btn.text())

    def set_active_index(self, index):
        btn = self.nav_group.button(index)
        if btn:
            btn.setChecked(True)
