"""
Dashboard View - Hiển thị thống kê và logs hệ thống
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea
)
from PySide6.QtCore import Qt
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
    
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
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
        self.card_today = StatCard("Hôm nay", "0", "📅", Theme.PRIMARY)
        
        stats_container.addWidget(self.card_users)
        stats_container.addWidget(self.card_enrolls)
        stats_container.addWidget(self.card_auth_success)
        stats_container.addWidget(self.card_auth_fail)
        stats_container.addWidget(self.card_today)
        stats_container.addStretch()
        
        main_layout.addLayout(stats_container)
        
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
        self.logs_table.setColumnCount(5)
        self.logs_table.setHorizontalHeaderLabels(["Thời gian", "Loại", "User ID", "Kết quả", "Chi tiết"])
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
            self.logs_table.setItem(row, 0, QTableWidgetItem(str(event["created_at"] or "")))
            
            event_type = event["event_type"]
            type_item = QTableWidgetItem(event_type)
            if event_type == "auth":
                type_item.setForeground(QColor(Theme.SECONDARY_GREEN))
            elif event_type == "auth_fail":
                type_item.setForeground(QColor(Theme.SECONDARY_RED))
            elif event_type == "enroll":
                type_item.setForeground(QColor(Theme.PRIMARY))
            self.logs_table.setItem(row, 1, type_item)
            
            self.logs_table.setItem(row, 2, QTableWidgetItem(event["user_id"] or "-"))
            
            result = event["result"]
            result_item = QTableWidgetItem(result)
            if result == "success":
                result_item.setForeground(QColor(Theme.SECONDARY_GREEN))
            else:
                result_item.setForeground(QColor(Theme.SECONDARY_RED))
            self.logs_table.setItem(row, 3, result_item)
            
            self.logs_table.setItem(row, 4, QTableWidgetItem(event["details"] or "-"))
    
    def showEvent(self, event):
        """Refresh data khi view được hiển thị"""
        super().showEvent(event)
        self.refresh_data()
