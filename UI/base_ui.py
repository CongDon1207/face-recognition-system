from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                               QPushButton, QLabel, QStackedWidget, QFrame)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon
from UI.styles import Theme
from UI.enrollment.enroll_ui import EnrollmentView
from UI.authentication.auth_ui import AuthenticationView
from UI.authentication.success_view import SuccessView
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
        self.auth_view.authentication_success.connect(self.on_authentication_success)
        self.pages.addWidget(self.auth_view)
        
        # 2: Enrollment (Real UI)
        self.enroll_view = EnrollmentView()
        self.enroll_view.go_to_auth.connect(self.switch_to_auth)
        self.pages.addWidget(self.enroll_view)
        
        # 3: Settings
        self.pages.addWidget(self.create_placeholder_page("Settings View"))
        
        # 4: Success View (hiển thị sau authentication thành công)
        self.success_view = SuccessView()
        self.success_view.back_to_auth.connect(self.back_to_authentication)
        self.pages.addWidget(self.success_view)
        
        content_layout.addWidget(self.pages)
        
        self.main_layout.addWidget(self.content_area)
        
    def switch_to_auth(self):
        # Programmatically switch to Auth
        self.sidebar.set_active_index(1)
        self.pages.setCurrentIndex(1)
        self.page_title.setText("Authentication")
        # Start authentication when switching to this view
        self.auth_view.start_authentication()
    
    def on_authentication_success(self, user_id: str, fullname: str):
        """Xử lý khi authentication thành công - chuyển sang Success View"""
        print(f"Authentication success: {fullname} ({user_id})")
        
        # Dừng camera
        self.auth_view.stop_authentication()
        
        # Hiển thị success view
        self.success_view.show_success(user_id, fullname)
        self.pages.setCurrentIndex(4)  # Index 4 là SuccessView
        self.page_title.setText("Access Granted")
    
    def back_to_authentication(self):
        """Quay lại authentication view"""
        self.sidebar.set_active_index(1)
        self.pages.setCurrentIndex(1)
        self.page_title.setText("Authentication")
        # Restart authentication
        QTimer.singleShot(100, self.auth_view.start_authentication)

    def setup_sidebar(self):
        self.sidebar = Sidebar()
        self.sidebar.nav_clicked.connect(self.on_nav_clicked)
        self.main_layout.addWidget(self.sidebar)

    def on_nav_clicked(self, idx, text):
        self.pages.setCurrentIndex(idx)
        self.page_title.setText(text)
        
        # Nếu chuyển sang Authentication view (idx=1), khởi động camera
        if idx == 1 and hasattr(self, 'auth_view'):
            self.auth_view.start_authentication()
        # Nếu chuyển đi khỏi Authentication, dừng camera sau 100ms
        elif hasattr(self, 'auth_view') and self.auth_view.camera_thread:
            # Dùng QTimer để đảm bảo stop sau khi frame processing xong
            QTimer.singleShot(100, self.auth_view.stop_authentication)
        
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
    
    def closeEvent(self, event):
        """Cleanup khi đóng cửa sổ."""
        # Dừng authentication để cleanup camera thread
        if hasattr(self, 'auth_view') and self.auth_view:
            self.auth_view.stop_authentication()
        event.accept()
