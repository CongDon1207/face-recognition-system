from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame)
from PySide6.QtCore import Qt, Signal, QTimer
from UI.styles import Theme

class CaptureStep(QWidget):
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.checklist_labels = {}
        self.angles = ["Frontal", "Left Profile", "Right Profile", "Upward", "Downward"]
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(30)
        
        # -- Left: Camera Area --
        camera_container = QFrame()
        camera_container.setProperty("class", "glass_panel")
        camera_layout = QVBoxLayout(camera_container)
        camera_layout.setAlignment(Qt.AlignCenter)
        
        self.camera_view = QLabel("Camera Feed\n(Scanning...)")
        self.camera_view.setAlignment(Qt.AlignCenter)
        self.camera_view.setFixedSize(400, 400)
        # Specific style for circular camera
        self.camera_view.setStyleSheet(f"""
            background-color: #000; 
            border: 2px solid {Theme.PRIMARY};
            border-radius: 200px;
            color: #fff;
        """)
        camera_layout.addWidget(self.camera_view)
        
        self.instruction_label = QLabel("FRONTAL - Look straight ahead")
        self.instruction_label.setProperty("class", "instruction_text")
        self.instruction_label.setAlignment(Qt.AlignCenter)
        camera_layout.addWidget(self.instruction_label)
        
        layout.addWidget(camera_container, 2)
        
        # -- Right: Checklist --
        checklist_container = QFrame()
        checklist_container.setProperty("class", "glass_panel")
        checklist_layout = QVBoxLayout(checklist_container)
        checklist_layout.setContentsMargins(20, 20, 20, 20)
        
        checklist_header = QLabel("Scanning Angles")
        checklist_header.setProperty("class", "subheader_text")
        checklist_layout.addWidget(checklist_header)
        
        for angle in self.angles:
            lbl = QLabel(f"○  {angle}")
            lbl.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 16px; padding: 5px;")
            self.checklist_labels[angle] = lbl
            checklist_layout.addWidget(lbl)
            
        checklist_layout.addStretch()
        
        # Debug/Dev Button
        skip_btn = QPushButton("Dev: Finish Capture")
        skip_btn.clicked.connect(self.finished.emit)
        checklist_layout.addWidget(skip_btn)
        
        layout.addWidget(checklist_container, 1)

    def start_capture(self):
        # NOTE: This replaces the previous internal simulation with a public method
        # that the Manager or Service can call. For now, we simulate simply.
        self.reset_ui()
        self.simulate_logic()

    def reset_ui(self):
        for angle in self.angles:
            lbl = self.checklist_labels[angle]
            lbl.setText(f"○  {angle}")
            lbl.setStyleSheet(f"color: {Theme.TEXT_GRAY}; font-size: 16px; padding: 5px;")
        self.instruction_label.setText("FRONTAL - Look straight ahead")

    def simulate_logic(self):
        # Temporary simulation logic kept here until backend service is ready
        self.capture_step = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_step_logic)
        self.timer.start(1500)

    def next_step_logic(self):
        if self.capture_step < len(self.angles):
            angle = self.angles[self.capture_step]
            lbl = self.checklist_labels[angle]
            lbl.setText(f"✔  {angle}")
            lbl.setStyleSheet(f"color: {Theme.SECONDARY_GREEN}; font-size: 16px; padding: 5px; font-weight: bold;")
            
            if self.capture_step + 1 < len(self.angles):
                next_angle = self.angles[self.capture_step + 1]
                self.instruction_label.setText(f"{next_angle.upper()} - Move head...")
            
            self.capture_step += 1
        else:
            self.timer.stop()
            self.finished.emit()
            
    def stop(self):
        if hasattr(self, 'timer'):
            self.timer.stop()
