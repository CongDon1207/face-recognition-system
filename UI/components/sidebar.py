from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QButtonGroup, QWidget
from PySide6.QtCore import Qt, Signal
from UI.styles import Theme

class Sidebar(QFrame):
    nav_clicked = Signal(int, str)  # Emits (id, label)
    logout_clicked = Signal()  # Emits khi user click Logout

    # Menu items cho từng mode
    GUEST_MENU = [
        ("auth", "Authentication"),
        ("enroll", "Enrollment"),
    ]
    
    AUTH_MENU = [
        ("dashboard", "Dashboard"),
        ("profile", "Profile"),
        ("about", "About"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(280)
        self.is_authenticated = False
        self.nav_buttons = {}  # Lưu reference đến buttons
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # 1. Header
        self.setup_header()
        
        # 2. Navigation container
        self.nav_container = QFrame()
        self.nav_layout = QVBoxLayout(self.nav_container)
        self.nav_layout.setAlignment(Qt.AlignTop)
        self.nav_layout.setContentsMargins(0, 20, 0, 20)
        self.nav_layout.setSpacing(10)
        self.layout.addWidget(self.nav_container)
        
        # Button group cho navigation
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_group.buttonClicked.connect(self.on_btn_clicked)
        
        # Build menu mặc định (guest mode)
        self.build_menu(authenticated=False)
        
        # Spacer
        self.layout.addStretch()
        
        # 3. Footer
        self.setup_footer()

    def setup_header(self):
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
        self.layout.addWidget(header_frame)

    def setup_footer(self):
        footer_frame = QFrame()
        footer_frame.setObjectName("status_bar")
        footer_frame.setFixedHeight(180)  # Tăng thêm chút chiều cao cho chữ to
        layout = QVBoxLayout(footer_frame)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)
        
        # Status
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)
        
        status_dot = QLabel("●")
        status_dot.setObjectName("status_dot")
        status_dot.setStyleSheet("font-size: 14px;") # Dot to hơn
        
        status_label = QLabel("SYSTEM ONLINE")
        status_label.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 11px; font-weight: bold; letter-spacing: 1.5px;")
        
        status_layout.addWidget(status_dot)
        status_layout.addWidget(status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Separator line
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color: {Theme.BORDER_COLOR}; margin: 5px 0px;")
        layout.addWidget(line)
        
        # Members Title
        members_title = QLabel("NHÓM THỰC HIỆN - NHÓM 4")
        members_title.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 12px; font-weight: bold;")
        layout.addWidget(members_title)
        
        # Members List from Proposal.md
        members = [
            ("Nguyễn Thị Hồng Thơ", "22151305"),
            ("Nguyễn Công Đôn", "22133013"),
            ("Nguyễn Như Hoàng Tiến", "22133061")
        ]
        
        for name, mssv in members:
            m_container = QWidget()
            m_vbox = QVBoxLayout(m_container)
            m_vbox.setContentsMargins(0, 0, 0, 0)
            m_vbox.setSpacing(2)
            
            # Line 1: Name and MSSV
            m_top_layout = QHBoxLayout()
            m_label = QLabel(name)
            m_label.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 14px; font-weight: 700;")
            m_mssv = QLabel(mssv)
            m_mssv.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 14px; opacity: 0.8;")
            
            m_top_layout.addWidget(m_label)
            m_top_layout.addStretch()
            m_top_layout.addWidget(m_mssv)
            m_vbox.addLayout(m_top_layout)
            
            layout.addWidget(m_container)
        
        self.layout.addWidget(footer_frame)

    def build_menu(self, authenticated: bool):
        """Xây dựng lại menu dựa trên trạng thái authentication."""
        self.is_authenticated = authenticated
        
        # Xóa tất cả buttons cũ
        for btn in list(self.nav_buttons.values()):
            self.nav_group.removeButton(btn)
            self.nav_layout.removeWidget(btn)
            btn.deleteLater()
        self.nav_buttons.clear()
        
        # Xóa logout button nếu có
        if hasattr(self, 'logout_btn') and self.logout_btn:
            self.nav_layout.removeWidget(self.logout_btn)
            self.logout_btn.deleteLater()
            self.logout_btn = None
        
        # Chọn menu items dựa trên mode
        menu_items = self.AUTH_MENU if authenticated else self.GUEST_MENU
        
        # Tạo buttons mới
        for idx, (key, label) in enumerate(menu_items):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setObjectName("nav_btn")
            btn.setProperty("class", "nav_btn")
            btn.setProperty("nav_key", key)
            btn.setCursor(Qt.PointingHandCursor)
            
            if idx == 0:
                btn.setChecked(True)
            
            self.nav_group.addButton(btn, idx)
            self.nav_layout.addWidget(btn)
            self.nav_buttons[key] = btn
        
        # Thêm Logout button nếu authenticated
        if authenticated:
            self.nav_layout.addSpacing(20)
            self.logout_btn = QPushButton("🚪 Logout")
            self.logout_btn.setObjectName("nav_btn")
            self.logout_btn.setProperty("class", "nav_btn")
            self.logout_btn.setCursor(Qt.PointingHandCursor)
            self.logout_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    color: {Theme.SECONDARY_RED};
                    text-align: left;
                    padding: 15px 20px;
                    font-size: 14px;
                    border-left: 3px solid transparent;
                }}
                QPushButton:hover {{
                    color: {Theme.TEXT_WHITE};
                    background-color: rgba(255, 77, 77, 20);
                    border-left: 3px solid {Theme.SECONDARY_RED};
                }}
            """)
            self.logout_btn.clicked.connect(self.logout_clicked.emit)
            self.nav_layout.addWidget(self.logout_btn)
        else:
            self.logout_btn = None

    def on_btn_clicked(self, btn):
        idx = self.nav_group.id(btn)
        nav_key = btn.property("nav_key")
        self.nav_clicked.emit(idx, nav_key)

    def set_active_index(self, index):
        btn = self.nav_group.button(index)
        if btn:
            btn.setChecked(True)

    def set_active_by_key(self, key: str):
        """Set active button bằng key thay vì index."""
        if key in self.nav_buttons:
            self.nav_buttons[key].setChecked(True)
