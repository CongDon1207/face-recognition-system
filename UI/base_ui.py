from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                               QPushButton, QLabel, QStackedWidget, QFrame)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon
from UI.styles import Theme
from UI.enrollment.enroll_ui import EnrollmentView
from UI.authentication.auth_ui import AuthenticationView
from UI.authentication.success_view import SuccessView
from UI.dashboard.dashboard_ui import DashboardView
from UI.profile.profile_ui import ProfileView
from UI.about.about_ui import AboutView
from UI.components.sidebar import Sidebar

class BaseWindow(QMainWindow):
    """
    Cửa sổ chính với 2 chế độ:
    - Guest mode: chỉ Authentication + Enrollment
    - Authenticated mode: Dashboard + Profile + About + Logout
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NEONGLASS - Biometric Security")
        self.resize(1280, 800)
        
        # === Trạng thái phiên ===
        self.is_authenticated = False
        self.current_user = None
        
        # Central Widget & Main Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Apply Theme
        self.setStyleSheet(Theme.get_stylesheet())
        
        # Initialize UI Components
        from modules.database import DatabaseManager
        self.db = DatabaseManager()
        self.setup_sidebar()
        self.setup_content_area()
        
        # Mặc định: hiển thị trang Authentication
        self.switch_to_page("auth")

    def setup_sidebar(self):
        self.sidebar = Sidebar()
        self.sidebar.nav_clicked.connect(self.on_nav_clicked)
        self.sidebar.logout_clicked.connect(self.on_logout)
        self.main_layout.addWidget(self.sidebar)

    def setup_content_area(self):
        # Container for main content
        self.content_area = QWidget()
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(30, 30, 30, 30)
        
        # Title of current view
        self.page_title = QLabel("Authentication")
        self.page_title.setStyleSheet(f"color: {Theme.TEXT_WHITE}; font-size: 28px; font-weight: 300;")
        content_layout.addWidget(self.page_title)
        
        # Stacked Widget for pages
        self.pages = QStackedWidget()
        
        # === GUEST MODE PAGES ===
        # 0: Authentication
        self.auth_view = AuthenticationView()
        self.auth_view.authentication_success.connect(self.on_authentication_success)
        self.pages.addWidget(self.auth_view)
        
        # 1: Enrollment
        self.enroll_view = EnrollmentView()
        self.enroll_view.go_to_auth.connect(self.switch_to_auth)
        self.pages.addWidget(self.enroll_view)
        
        # === AUTHENTICATED MODE PAGES ===
        # 2: Dashboard
        self.dashboard_view = DashboardView()
        self.pages.addWidget(self.dashboard_view)
        
        # 3: Profile
        self.profile_view = ProfileView()
        self.pages.addWidget(self.profile_view)
        
        # 4: About
        self.about_view = AboutView()
        self.pages.addWidget(self.about_view)
        
        content_layout.addWidget(self.pages)
        self.main_layout.addWidget(self.content_area)
        
        # Mapping nav_key -> (page_index, page_title)
        self.page_map = {
            # Guest mode
            "auth": (0, "Authentication"),
            "enroll": (1, "Enrollment"),
            # Authenticated mode
            "dashboard": (2, "Dashboard"),
            "profile": (3, "Profile"),
            "about": (4, "About"),
        }

    def switch_to_page(self, nav_key: str):
        """Chuyển đến trang theo key"""
        if nav_key not in self.page_map:
            return
        
        page_idx, title = self.page_map[nav_key]
        self.pages.setCurrentIndex(page_idx)
        self.page_title.setText(title)
        self.sidebar.set_active_by_key(nav_key)
        
        # Xử lý đặc biệt cho từng trang
        if nav_key == "auth":
            pass  # Không auto-start, user nhấn nút Start
        elif nav_key == "dashboard":
            self.dashboard_view.refresh_data()
        elif nav_key == "profile" and self.current_user:
            self.profile_view.set_user(self.current_user)

    def switch_to_auth(self):
        """Programmatically switch to Auth từ Enrollment success"""
        self.switch_to_page("auth")
        self.auth_view.start_authentication()

    def on_nav_clicked(self, idx: int, nav_key: str):
        """Xử lý khi click menu item"""
        # Dừng authentication nếu đang chạy và chuyển đi
        if nav_key != "auth" and hasattr(self, 'auth_view'):
            if self.auth_view.camera_thread or self.auth_view.is_checking:
                QTimer.singleShot(100, self.auth_view.stop_authentication)
        
        self.switch_to_page(nav_key)
    
    def on_authentication_success(self, user_id: str, fullname: str):
        """Xử lý khi authentication thành công - unlock menu và chuyển Dashboard"""
        # Lấy đầy đủ thông tin từ DB
        user_data = self.db.get_user(user_id)
        print(f"[BaseWindow] Auth success for {user_id}: {user_data}")
        
        # Dừng camera
        self.auth_view.stop_authentication()
        
        # Lưu trạng thái authenticated
        self.is_authenticated = True
        self.current_user = user_data if user_data else {"id": user_id, "fullname": fullname}
        
        # Ghi event vào DB
        self.db.add_event(
            event_type="auth",
            user_id=user_id,
            result="success",
            details=f"Xác thực thành công: {fullname}"
        )
        
        # Rebuild sidebar với menu authenticated
        self.sidebar.build_menu(authenticated=True)
        
        # Cập nhật profile view
        self.profile_view.set_user(self.current_user)
        
        # Chuyển sang Dashboard
        self.switch_to_page("dashboard")
        self.page_title.setText(f"Dashboard - Xin chào, {fullname}!")

    def on_logout(self):
        """Xử lý logout - quay về guest mode"""
        print(f"[BaseWindow] Logout: {self.current_user}")
        
        # Ghi event
        if self.current_user:
            self.db.add_event(
                event_type="logout",
                user_id=self.current_user.get("id"),
                result="success"
            )
        
        # Reset trạng thái
        self.is_authenticated = False
        self.current_user = None
        
        # Rebuild sidebar về guest mode
        self.sidebar.build_menu(authenticated=False)
        
        # Chuyển về trang Authentication
        self.switch_to_page("auth")
    
    def closeEvent(self, event):
        """Cleanup khi đóng cửa sổ."""
        if hasattr(self, 'auth_view') and self.auth_view:
            self.auth_view.stop_authentication()
        event.accept()
