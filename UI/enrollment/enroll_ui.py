from PySide6.QtWidgets import (QWidget, QStackedLayout)
from PySide6.QtCore import Signal
from UI.enrollment.steps.profile_step import ProfileStep
from UI.enrollment.steps.capture_step import CaptureStep
from UI.enrollment.steps.success_step import SuccessStep

class EnrollmentView(QWidget):
    go_to_auth = Signal()

    def __init__(self):
        super().__init__()
        self.user_profile = {}
        
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

    def on_profile_complete(self, name, emp_id):
        self.user_profile = {"name": name, "id": emp_id}
        # Pass to Step 3 for display later
        self.step3.set_data(name, emp_id)
        
        # Move to Step 2
        self.wizard_layout.setCurrentIndex(1)
        self.step2.start_capture()

    def on_capture_complete(self):
        # Move to Step 3
        self.wizard_layout.setCurrentIndex(2)

    def reset_wizard(self):
        self.step1.clear_fields()
        self.step2.reset_ui()
        self.wizard_layout.setCurrentIndex(0)
