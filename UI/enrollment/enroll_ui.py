"""
Enrollment View Manager - Quản lý 3 bước của quy trình đăng ký khuôn mặt.
Tích hợp DatabaseManager để lưu dữ liệu.
"""
from PySide6.QtWidgets import QWidget, QStackedLayout
from PySide6.QtCore import Signal

from UI.enrollment.steps.profile_step import ProfileStep
from UI.enrollment.steps.capture_step import CaptureStep
from UI.enrollment.steps.success_step import SuccessStep
from modules.database import DatabaseManager
from modules.ai.face_analyzer import PoseType


class EnrollmentView(QWidget):
    """Quản lý luồng Enrollment 3 bước."""

    go_to_auth = Signal()

    def __init__(self):
        super().__init__()
        self.user_profile = {}
        self.db = DatabaseManager()

        # Main Layout: Stacked for Wizard Steps
        self.wizard_layout = QStackedLayout(self)

        # --- Step 1: Profile Input ---
        self.step1 = ProfileStep()
        self.step1.next_step.connect(self.on_profile_complete)
        self.wizard_layout.addWidget(self.step1)

        # --- Step 2: Capture Sequence ---
        self.step2 = CaptureStep()
        self.step2.finished.connect(self.on_capture_complete)
        self.wizard_layout.addWidget(self.step2)

        # --- Step 3: Success ---
        self.step3 = SuccessStep()
        self.step3.restart.connect(self.reset_wizard)
        self.step3.goto_auth.connect(self.go_to_auth.emit)
        self.wizard_layout.addWidget(self.step3)

        # Start at Step 1
        self.wizard_layout.setCurrentIndex(0)

    def on_profile_complete(self, user_data: dict):
        """Xử lý khi nhập xong thông tin profile."""
        self.user_profile = user_data
        emp_id = user_data["id"]

        # Kiểm tra user đã tồn tại chưa
        if self.db.user_exists(emp_id):
            print(f"[Enrollment] User ID {emp_id} đã tồn tại!")
            return

        # Pass to Step 3 for display later
        self.step3.set_data(user_data["fullname"], emp_id)

        # Move to Step 2
        self.wizard_layout.setCurrentIndex(1)
        self.step2.start_capture(user_id=emp_id)

    def on_capture_complete(self, captured_data: list):
        """Xử lý khi capture xong tất cả các góc."""
        if not captured_data:
            # User đã hủy
            self.reset_wizard()
            return

        user_id = self.user_profile["id"]
        fullname = self.user_profile["fullname"]
        email = self.user_profile.get("email")
        phone = self.user_profile.get("phone")
        dob = self.user_profile.get("dob")

        # Lưu ảnh trước, gom dữ liệu embedding để ghi DB theo transaction
        avatar_path = None
        embeddings_data: list[tuple] = []
        for pose_type, embedding, cropped_img in captured_data:
            img_path = self.db.save_face_image(user_id, pose_type.value, cropped_img)
            if pose_type == PoseType.FRONTAL:
                avatar_path = img_path
            embeddings_data.append((embedding, pose_type.value, img_path))

        success = self.db.enroll_user_with_embeddings(
            user_id=user_id,
            fullname=fullname,
            email=email,
            phone=phone,
            dob=dob,
            avatar_path=avatar_path,
            embeddings_data=embeddings_data,
        )
        if not success:
            # TODO: Hiển thị lỗi trên UI
            print(f"[Enrollment] Không thể lưu user/embeddings cho ID {user_id}")
            self.reset_wizard()
            return

        # Move to Step 3
        self.wizard_layout.setCurrentIndex(2)

    def reset_wizard(self):
        """Reset về bước 1."""
        self.step1.clear_fields()
        self.step2.reset_ui()
        self.user_profile = {}
        self.wizard_layout.setCurrentIndex(0)

