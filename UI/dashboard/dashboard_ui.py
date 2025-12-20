"""
Dashboard View - Hiển thị thống kê và logs hệ thống (WITH FAIL TRACKING)
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from UI.styles import Theme
from modules.database import DatabaseManager

class StatCard(QFrame):
    """Card hiển thị một thống kê"""
    
    def __init__(self, title: str, value: str, icon: str, color: str):
        super().__init__()
        self.setFixedSize(200, 120)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 243, 255, 10);
                border: 1px solid {color};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(5)
        
        # Icon + Title
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 24px; color: {color};")
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 12px;")
        header.addWidget(icon_label)
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: bold;")
        layout.addWidget(self.value_label)
        
        layout.addStretch()
    
    def set_value(self, value: str):
        self.value_label.setText(value)


class DashboardView(QWidget):
    """Dashboard chính - stats + logs + biểu đồ"""
    
    # NEW: Signal để nhận cập nhật fail count real-time
    fail_count_updated = Signal(int)
    
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        
        # NEW: Tracking live fail count
        self.current_fail_count = 0
        self.session_fail_count = 0  # Fail trong phiên hiện tại
        
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)
        
        # === Stats Cards ===
        stats_container = QHBoxLayout()
        stats_container.setSpacing(15)
        
        self.card_users = StatCard("Người dùng", "0", "👥", Theme.PRIMARY)
        self.card_enrolls = StatCard("Đăng ký", "0", "📝", Theme.SECONDARY_GREEN)
        self.card_auth_success = StatCard("Xác thực OK", "0", "✅", Theme.SECONDARY_GREEN)
        self.card_auth_fail = StatCard("Xác thực Fail", "0", "❌", Theme.SECONDARY_RED)
        
        # NEW: Card riêng cho fail count của session hiện tại
        self.card_session_fails = StatCard("Fails hiện tại", "0/3", "⚠️", "#FFD700")
        
        self.card_today = StatCard("Hôm nay", "0", "📅", Theme.PRIMARY)
        
        stats_container.addWidget(self.card_users)
        stats_container.addWidget(self.card_enrolls)
        stats_container.addWidget(self.card_auth_success)
        stats_container.addWidget(self.card_auth_fail)
        stats_container.addWidget(self.card_session_fails)  # NEW
        stats_container.addWidget(self.card_today)
        stats_container.addStretch()
        
        main_layout.addLayout(stats_container)
        
        # === NEW: Real-time Status Bar ===
        status_bar = QFrame()
        status_bar.setFixedHeight(50)
        status_bar.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 243, 255, 8);
                border: 1px solid {Theme.PRIMARY};
                border-radius: 8px;
            }}
        """)
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(20, 10, 20, 10)
        
        self.live_status_label = QLabel("🟢 Hệ thống sẵn sàng")
        self.live_status_label.setStyleSheet(f"color: {Theme.SECONDARY_GREEN}; font-size: 14px; font-weight: bold;")
        
        self.live_fail_label = QLabel("Fails: 0/3")
        self.live_fail_label.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 14px;")
        
        status_layout.addWidget(self.live_status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.live_fail_label)
        
        main_layout.addWidget(status_bar)
        
        # === Logs Table ===
        logs_frame = QFrame()
        logs_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 5);
                border: 1px solid {Theme.BORDER_COLOR};
                border-radius: 12px;
            }}
        """)
        logs_layout = QVBoxLayout(logs_frame)
        logs_layout.setContentsMargins(20, 15, 20, 15)
        
        logs_title = QLabel("📋 Lịch sử hoạt động")
        logs_title.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 18px; font-weight: bold;")
        logs_layout.addWidget(logs_title)
        
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(6)  # NEW: Thêm 1 cột cho fail count
        self.logs_table.setHorizontalHeaderLabels([
            "Thời gian", "Loại", "User ID", "Kết quả", "Fails", "Chi tiết"
        ])
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.logs_table.setAlternatingRowColors(True)
        self.logs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.logs_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.logs_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: transparent;
                border: none;
                color: {Theme.TEXT_WHITE};
                gridline-color: {Theme.BORDER_COLOR};
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background-color: rgba(0, 243, 255, 30);
            }}
            QHeaderView::section {{
                background-color: rgba(0, 243, 255, 20);
                color: {Theme.PRIMARY};
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
        """)
        logs_layout.addWidget(self.logs_table)
        
        main_layout.addWidget(logs_frame, stretch=2)
        
        # === Chart Placeholder ===
        chart_frame = QFrame()
        chart_frame.setFixedHeight(200)
        chart_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 5);
                border: 1px solid {Theme.BORDER_COLOR};
                border-radius: 12px;
            }}
        """)
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setAlignment(Qt.AlignCenter)
        
        chart_title = QLabel("📊 Biểu đồ hoạt động")
        chart_title.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 18px; font-weight: bold;")
        chart_layout.addWidget(chart_title, alignment=Qt.AlignTop | Qt.AlignLeft)
        
        chart_placeholder = QLabel("(Biểu đồ sẽ được thêm sau)")
        chart_placeholder.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 14px;")
        chart_layout.addWidget(chart_placeholder, alignment=Qt.AlignCenter)
        
        main_layout.addWidget(chart_frame)
    
    def update_live_fail_count(self, fail_count: int, max_fails: int = 3):
        """
        NEW: Cập nhật fail count real-time từ AuthenticationView
        
        Args:
            fail_count: Số lần fail hiện tại
            max_fails: Số lần fail tối đa (mặc định 3)
        """
        self.session_fail_count = fail_count
        
        # Cập nhật card
        self.card_session_fails.set_value(f"{fail_count}/{max_fails}")
        
        # Cập nhật status bar
        self.live_fail_label.setText(f"Fails: {fail_count}/{max_fails}")
        
        # Đổi màu dựa trên mức độ nguy hiểm
        if fail_count == 0:
            color = Theme.SECONDARY_GREEN
            status_text = "🟢 Hệ thống sẵn sàng"
        elif fail_count == 1:
            color = "#FFD700"  # Yellow
            status_text = "🟡 Cảnh báo: 1 lần thất bại"
        elif fail_count == 2:
            color = "#FFA500"  # Orange
            status_text = "🟠 Nguy hiểm: 2 lần thất bại"
        else:
            color = Theme.SECONDARY_RED
            status_text = "🔴 Khóa: Quá nhiều lần thất bại"
        
        self.live_fail_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
        self.live_status_label.setText(status_text)
        self.live_status_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
        
        # Emit signal
        self.fail_count_updated.emit(fail_count)
    
    def reset_session_fails(self):
        """NEW: Reset fail count khi bắt đầu phiên mới"""
        self.update_live_fail_count(0)
    
    def refresh_data(self):
        """Load lại dữ liệu từ DB"""
        # Load stats
        stats = self.db.get_stats()
        self.card_users.set_value(str(stats["total_users"]))
        self.card_enrolls.set_value(str(stats["total_enrolls"]))
        self.card_auth_success.set_value(str(stats["total_auth_success"]))
        self.card_auth_fail.set_value(str(stats["total_auth_fail"]))
        self.card_today.set_value(str(stats["auth_today"]))
        
        # Load logs
        events = self.db.get_events(limit=30)
        self.logs_table.setRowCount(len(events))
        
        for row, event in enumerate(events):
            # Thời gian
            self.logs_table.setItem(row, 0, QTableWidgetItem(str(event["created_at"] or "")))
            
            # Loại
            event_type = event["event_type"]
            type_item = QTableWidgetItem(event_type)
            if event_type == "auth":
                type_item.setForeground(QColor(Theme.SECONDARY_GREEN))
            elif event_type == "auth_fail":
                type_item.setForeground(QColor(Theme.SECONDARY_RED))
            elif event_type == "enroll":
                type_item.setForeground(QColor(Theme.PRIMARY))
            self.logs_table.setItem(row, 1, type_item)
            
            # User ID
            self.logs_table.setItem(row, 2, QTableWidgetItem(event["user_id"] or "-"))
            
            # Kết quả
            result = event["result"]
            result_item = QTableWidgetItem(result)
            if result == "success":
                result_item.setForeground(QColor(Theme.SECONDARY_GREEN))
            else:
                result_item.setForeground(QColor(Theme.SECONDARY_RED))
            self.logs_table.setItem(row, 3, result_item)
            
            # NEW: Fail count (extract từ details nếu có)
            details = event["details"] or ""
            fail_count = "-"
            if "fail_count:" in details.lower():
                # Parse fail_count từ details string
                try:
                    fail_part = [p for p in details.split(",") if "fail_count" in p.lower()]
                    if fail_part:
                        fail_count = fail_part[0].split(":")[-1].strip()
                except:
                    pass
            
            fail_item = QTableWidgetItem(fail_count)
            if fail_count != "-" and int(fail_count.split("/")[0]) >= 2:
                fail_item.setForeground(QColor(Theme.SECONDARY_RED))
            self.logs_table.setItem(row, 4, fail_item)
            
            # Chi tiết
            self.logs_table.setItem(row, 5, QTableWidgetItem(details))
    
    def showEvent(self, event):
        """Refresh data khi view được hiển thị"""
        super().showEvent(event)
        self.refresh_data()
