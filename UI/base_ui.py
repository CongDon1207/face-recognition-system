from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                               QPushButton, QLabel, QStackedWidget, QFrame)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from UI.styles import Theme
from UI.enrollment.enroll_ui import EnrollmentView
from UI.authentication.auth_ui import AuthenticationView
from UI.components.sidebar import Sidebar

class BaseWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NEONGLASS - Biometric Security")
        self.resize(1280, 800)
        
        # Central Widget & Main Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Apply Theme
        self.setStyleSheet(Theme.get_stylesheet())
        
        # Initialize UI Components
        self.setup_sidebar()
        self.setup_content_area()

    def setup_content_area(self):
        # Container for main content
        self.content_area = QWidget()
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(30, 30, 30, 30)
        
        # Title of current view
        self.page_title = QLabel("Dashboard")
        self.page_title.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 28px; font-weight: 300;")
        content_layout.addWidget(self.page_title)
        
        # Stacked Widget for pages
        self.pages = QStackedWidget()
        
        # 0: Dashboard
        self.pages.addWidget(self.create_placeholder_page("Dashboard View"))
        
        # 1: Authentication (Real UI)
        self.auth_view = AuthenticationView()
        self.pages.addWidget(self.auth_view)
        
        # 2: Enrollment (Real UI)
        self.enroll_view = EnrollmentView()
        self.enroll_view.go_to_auth.connect(self.switch_to_auth)
        self.pages.addWidget(self.enroll_view)
        
        # 3: Settings
        self.pages.addWidget(self.create_placeholder_page("Settings View"))
        
        content_layout.addWidget(self.pages)
        
        self.main_layout.addWidget(self.content_area)
        
    def switch_to_auth(self):
        # Programmatically switch to Auth
        self.sidebar.set_active_index(1)
        self.pages.setCurrentIndex(1)
        self.page_title.setText("Authentication")
        # Start authentication when switching to this view
        self.auth_view.start_authentication()

    def setup_sidebar(self):
        self.sidebar = Sidebar()
        self.sidebar.nav_clicked.connect(self.on_nav_clicked)
        self.main_layout.addWidget(self.sidebar)

    def on_nav_clicked(self, idx, text):
        self.pages.setCurrentIndex(idx)
        self.page_title.setText(text)
        
    def create_placeholder_page(self, text):
        page = QFrame()
        page.setProperty("class", "glass_panel") # Use glass panel style
        
        # Manual QSS application for ensuring glass style shows up on placeholder
        page.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 5);
                border: 1px solid {Theme.BORDER_COLOR};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(page)
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 18px;")
        layout.addWidget(label)
        return page
