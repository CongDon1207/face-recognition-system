""" 
Panel hiển thị các chỉ số và tiến trình kiểm tra liveness.
Bao gồm: EAR, Pose angles, Texture analysis, các frame xử lý.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QGridLayout, QScrollArea)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QImage
from UI.styles import Theme
import cv2
import numpy as np


class LivenessPanel(QWidget):
    """
    Panel hiển thị chi tiết các bước xử lý chống giả mạo
    Bao gồm: EAR, Pose angles, Texture analysis, các frame xử lý
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Liveness Verification")
        self.setMinimumSize(1200, 800)
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header
        header = QLabel("🔍 LIVENESS VERIFICATION")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(f"""
            color: {Theme.PRIMARY};
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 2px;
            padding: 15px;
            background-color: rgba(0, 244, 255, 10);
            border-radius: 8px;
        """)
        main_layout.addWidget(header)
        
        # Scroll Area cho nội dung
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {Theme.PRIMARY};
                border-radius: 8px;
                background-color: rgba(5, 8, 22, 150);
            }}
        """)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # === SECTION 1: METRICS OVERVIEW ===
        metrics_section = self.create_metrics_section()
        content_layout.addWidget(metrics_section)
        
        # === SECTION 2: PROCESSED FRAMES ===
        frames_section = self.create_frames_section()
        content_layout.addWidget(frames_section)
        
        # === SECTION 3: LIVENESS STEPS ===
        steps_section = self.create_steps_section()
        content_layout.addWidget(steps_section)
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
    def create_metrics_section(self):
        """Phần hiển thị các chỉ số real-time"""
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 0, 0, 200);
                border: 2px solid {Theme.PRIMARY};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        
        # Title
        title = QLabel("📊 REAL-TIME METRICS")
        title.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Grid layout cho các metrics
        grid = QGridLayout()
        grid.setSpacing(15)
        
        metric_style = f"""
            QLabel {{
                color: {Theme.TEXT_WHITE};
                font-size: 14px;
                padding: 8px;
                background-color: rgba(0, 244, 255, 5);
                border-radius: 5px;
            }}
        """
        
        # Row 1: Eye Aspect Ratio
        self.label_ear_left = self._create_metric_label("Left EAR: --", metric_style)
        self.label_ear_right = self._create_metric_label("Right EAR: --", metric_style)
        self.label_ear_avg = self._create_metric_label("Average EAR: --", metric_style)
        grid.addWidget(self.label_ear_left, 0, 0)
        grid.addWidget(self.label_ear_right, 0, 1)
        grid.addWidget(self.label_ear_avg, 0, 2)
        
        # Row 2: Head Pose
        self.label_yaw = self._create_metric_label("Yaw: --°", metric_style)
        self.label_pitch = self._create_metric_label("Pitch: --°", metric_style)
        self.label_roll = self._create_metric_label("Roll: --°", metric_style)
        grid.addWidget(self.label_yaw, 1, 0)
        grid.addWidget(self.label_pitch, 1, 1)
        grid.addWidget(self.label_roll, 1, 2)
        
        # Row 3: Texture Analysis
        self.label_texture = self._create_metric_label("Texture Score: --", metric_style)
        self.label_color_div = self._create_metric_label("Color Diversity: --", metric_style)
        self.label_edge_density = self._create_metric_label("Edge Density: --", metric_style)
        grid.addWidget(self.label_texture, 2, 0)
        grid.addWidget(self.label_color_div, 2, 1)
        grid.addWidget(self.label_edge_density, 2, 2)
        
        # Row 4: Liveness Score
        self.label_liveness_score = self._create_metric_label("Liveness Score: --", metric_style)
        self.label_liveness_status = self._create_metric_label("Status: READY", metric_style)
        self.label_confidence = self._create_metric_label("Confidence: --", metric_style)
        grid.addWidget(self.label_liveness_score, 3, 0)
        grid.addWidget(self.label_liveness_status, 3, 1)
        grid.addWidget(self.label_confidence, 3, 2)
        
        layout.addLayout(grid)
        
        return section
    
    def create_frames_section(self):
        """Phần hiển thị các frame đã xử lý"""
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 0, 0, 200);
                border: 2px solid {Theme.PRIMARY};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        
        title = QLabel("🖼️ PROCESSED FRAMES")
        title.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Grid cho các frames
        frames_grid = QGridLayout()
        frames_grid.setSpacing(10)
        
        frame_style = f"""
            QLabel {{
                background-color: #000000;
                border: 1px solid {Theme.PRIMARY};
                border-radius: 5px;
            }}
        """
        
        # Original Frame
        self.frame_original = self._create_frame_display("Original", frame_style)
        frames_grid.addWidget(self.frame_original, 0, 0)
        
        # Gray Frame
        self.frame_gray = self._create_frame_display("Grayscale", frame_style)
        frames_grid.addWidget(self.frame_gray, 0, 1)
        
        # Face ROI
        self.frame_face_roi = self._create_frame_display("Face ROI", frame_style)
        frames_grid.addWidget(self.frame_face_roi, 0, 2)
        
        # Edges
        self.frame_edges = self._create_frame_display("Edge Detection", frame_style)
        frames_grid.addWidget(self.frame_edges, 1, 0)
        
        # Texture Map
        self.frame_texture = self._create_frame_display("Texture Analysis", frame_style)
        frames_grid.addWidget(self.frame_texture, 1, 1)
        
        # Frequency Domain
        self.frame_frequency = self._create_frame_display("Frequency Domain", frame_style)
        frames_grid.addWidget(self.frame_frequency, 1, 2)
        
        layout.addLayout(frames_grid)
        
        return section
    
    def create_steps_section(self):
        """Phần hiển thị các bước liveness đã hoàn thành"""
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(0, 0, 0, 200);
                border: 2px solid {Theme.PRIMARY};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        
        title = QLabel("✅ LIVENESS VERIFICATION STEPS")
        title.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Progress Grid
        progress_grid = QGridLayout()
        progress_grid.setSpacing(15)
        
        step_style = f"""
            QLabel {{
                color: {Theme.TEXT_GRAY};
                font-size: 14px;
                padding: 10px;
                background-color: rgba(50, 50, 50, 100);
                border: 2px solid {Theme.TEXT_GRAY};
                border-radius: 8px;
            }}
        """
        
        self.step_blink = self._create_step_label("👁️ Eye Blink", "Pending", step_style)
        self.step_left = self._create_step_label("◀️ Turn Left", "Pending", step_style)
        self.step_right = self._create_step_label("▶️ Turn Right", "Pending", step_style)
        self.step_texture = self._create_step_label("🔍 Texture Check", "Pending", step_style)
        
        progress_grid.addWidget(self.step_blink, 0, 0)
        progress_grid.addWidget(self.step_left, 0, 1)
        progress_grid.addWidget(self.step_right, 0, 2)
        progress_grid.addWidget(self.step_texture, 0, 3)
        
        layout.addLayout(progress_grid)
        
        # Instruction Label
        self.instruction_label = QLabel("Hướng dẫn: Nhìn thẳng vào camera")
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.instruction_label.setStyleSheet(f"""
            color: {Theme.PRIMARY};
            font-size: 16px;
            font-weight: bold;
            padding: 15px;
            background-color: rgba(0, 244, 255, 10);
            border-radius: 8px;
            margin-top: 10px;
        """)
        layout.addWidget(self.instruction_label)
        
        return section
    
    def _create_metric_label(self, text, style):
        label = QLabel(text)
        label.setStyleSheet(style)
        label.setAlignment(Qt.AlignCenter)
        return label
    
    def _create_frame_display(self, title, style):
        container = QFrame()
        container.setFixedSize(280, 240)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(5)
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 12px; font-weight: bold;")
        container_layout.addWidget(title_label)
        
        frame_label = QLabel()
        frame_label.setFixedSize(260, 195)
        frame_label.setStyleSheet(style)
        frame_label.setAlignment(Qt.AlignCenter)
        frame_label.setText("No Frame")
        container_layout.addWidget(frame_label)
        
        setattr(self, f"display_{title.replace(' ', '_').lower()}", frame_label)
        
        return container
    
    def _create_step_label(self, icon_text, status, style):
        label = QLabel(f"{icon_text}\n{status}")
        label.setStyleSheet(style)
        label.setAlignment(Qt.AlignCenter)
        return label
    
    # === UPDATE METHODS ===
    
    def update_metrics(self, metrics_data: dict):
        """Cập nhật các chỉ số từ liveness detector"""
        
        # Eye Aspect Ratio
        if "ear_left" in metrics_data:
            self.label_ear_left.setText(f"Left EAR: {metrics_data['ear_left']:.3f}")
        if "ear_right" in metrics_data:
            self.label_ear_right.setText(f"Right EAR: {metrics_data['ear_right']:.3f}")
        if "ear_avg" in metrics_data:
            ear_avg = metrics_data['ear_avg']
            color = Theme.SECONDARY_GREEN if ear_avg > 0.2 else Theme.SECONDARY_RED
            self.label_ear_avg.setText(f"Average EAR: {ear_avg:.3f}")
            self.label_ear_avg.setStyleSheet(f"""
                color: {color};
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                background-color: rgba(0, 244, 255, 5);
                border-radius: 5px;
            """)
        
        # Head Pose
        if "yaw" in metrics_data:
            self.label_yaw.setText(f"Yaw: {metrics_data['yaw']:.1f}°")
        if "pitch" in metrics_data:
            self.label_pitch.setText(f"Pitch: {metrics_data['pitch']:.1f}°")
        if "roll" in metrics_data:
            self.label_roll.setText(f"Roll: {metrics_data['roll']:.1f}°")
        
        # Texture Analysis
        if "texture_score" in metrics_data:
            self.label_texture.setText(f"Texture Score: {metrics_data['texture_score']:.3f}")
        if "color_diversity" in metrics_data:
            self.label_color_div.setText(f"Color Diversity: {metrics_data['color_diversity']:.3f}")
        if "edge_density" in metrics_data:
            self.label_edge_density.setText(f"Edge Density: {metrics_data['edge_density']:.3f}")
        
        # Liveness Score
        if "liveness_score" in metrics_data:
            score = metrics_data['liveness_score']
            color = Theme.SECONDARY_GREEN if score > 0.5 else Theme.SECONDARY_RED
            self.label_liveness_score.setText(f"Liveness Score: {score:.3f}")
            self.label_liveness_score.setStyleSheet(f"""
                color: {color};
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                background-color: rgba(0, 244, 255, 5);
                border-radius: 5px;
            """)
        
        if "status" in metrics_data:
            status = metrics_data['status']
            color = Theme.SECONDARY_GREEN if status == "REAL" else Theme.SECONDARY_RED if status == "SPOOF/FAKE" else Theme.PRIMARY
            self.label_liveness_status.setText(f"Status: {status}")
            self.label_liveness_status.setStyleSheet(f"""
                color: {color};
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                background-color: rgba(0, 244, 255, 5);
                border-radius: 5px;
            """)
        
        if "confidence" in metrics_data:
            self.label_confidence.setText(f"Confidence: {metrics_data['confidence']:.1%}")
    
    def update_frame(self, frame_name: str, frame: np.ndarray):
        """Cập nhật một frame xử lý"""
        try:
            display_label = getattr(self, f"display_{frame_name}", None)
            if display_label is None:
                return
            
            # Resize và convert
            frame_resized = cv2.resize(frame, (260, 195))
            
            # Check if grayscale
            if len(frame_resized.shape) == 2:
                frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_GRAY2RGB)
            else:
                frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            
            h, w, ch = frame_rgb.shape
            q_image = QImage(frame_rgb.tobytes(), w, h, ch * w, QImage.Format_RGB888).copy()
            pixmap = QPixmap.fromImage(q_image)
            
            display_label.setPixmap(pixmap)
        except Exception as e:
            print(f"Error updating frame {frame_name}: {e}")
    
    def update_steps(self, completed_steps: list, instruction: str):
        """Cập nhật trạng thái các bước"""
        
        # Reset all
        for step_label in [self.step_blink, self.step_left, self.step_right, self.step_texture]:
            step_label.setStyleSheet(f"""
                color: {Theme.TEXT_GRAY};
                font-size: 14px;
                padding: 10px;
                background-color: rgba(50, 50, 50, 100);
                border: 2px solid {Theme.TEXT_GRAY};
                border-radius: 8px;
            """)
        
        # Update completed
        step_map = {
            "blink": self.step_blink,
            "left": self.step_left,
            "right": self.step_right,
            "texture": self.step_texture
        }
        
        for step in completed_steps:
            if step in step_map:
                step_map[step].setStyleSheet(f"""
                    color: {Theme.SECONDARY_GREEN};
                    font-size: 14px;
                    font-weight: bold;
                    padding: 10px;
                    background-color: rgba(0, 255, 157, 20);
                    border: 2px solid {Theme.SECONDARY_GREEN};
                    border-radius: 8px;
                """)
                # Update text
                icon_texts = {
                    "blink": "👁️ Eye Blink",
                    "left": "◀️ Turn Left",
                    "right": "▶️ Turn Right",
                    "texture": "🔍 Texture Check"
                }
                step_map[step].setText(f"{icon_texts[step]}\n✅ Completed")
        
        # Update instruction
        self.instruction_label.setText(f"Hướng dẫn: {instruction}")


# === STANDALONE PREVIEW ===
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    
    # Mock Theme
    class MockTheme:
        PRIMARY = "#00f4ff"
        SECONDARY_GREEN = "#00ff9d"
        SECONDARY_RED = "#ff4d4d"
        TEXT_WHITE = "#ffffff"
        TEXT_GRAY = "#a0a0a0"
        BACKGROUND = "#050816"
    Theme = MockTheme
    
    app = QApplication(sys.argv)
    app.setStyleSheet(f"QWidget {{ background-color: {Theme.BACKGROUND}; }}")
    
    panel = LivenessPanel()
    panel.show()
    
    # Simulate updates
    def simulate_data():
        import random
        
        # Update metrics
        metrics = {
            "ear_left": random.uniform(0.15, 0.35),
            "ear_right": random.uniform(0.15, 0.35),
            "ear_avg": random.uniform(0.15, 0.35),
            "yaw": random.uniform(-30, 30),
            "pitch": random.uniform(-15, 15),
            "roll": random.uniform(-10, 10),
            "texture_score": random.uniform(0.3, 0.9),
            "color_diversity": random.uniform(0.4, 0.8),
            "edge_density": random.uniform(0.5, 0.9),
            "liveness_score": random.uniform(0.4, 0.9),
            "status": random.choice(["REAL", "PROCESSING", "SPOOF/FAKE"]),
            "confidence": random.uniform(0.6, 0.95)
        }
        panel.update_metrics(metrics)
        
        # Update steps
        steps = random.choice([
            [],
            ["blink"],
            ["blink", "left"],
            ["blink", "left", "right"],
            ["blink", "left", "right", "texture"]
        ])
        instruction = random.choice([
            "Nháy mắt",
            "Quay đầu sang trái",
            "Quay đầu sang phải",
            "Giữ nguyên tư thế"
        ])
        panel.update_steps(steps, instruction)
        
        # Update frames with random noise (for demo)
        dummy_frame = (np.random.rand(480, 640, 3) * 255).astype(np.uint8)
        panel.update_frame("original", dummy_frame)
        panel.update_frame("grayscale", cv2.cvtColor(dummy_frame, cv2.COLOR_BGR2GRAY))
        panel.update_frame("face_roi", dummy_frame[100:300, 200:400])
        panel.update_frame("edge_detection", cv2.Canny(cv2.cvtColor(dummy_frame, cv2.COLOR_BGR2GRAY), 100, 200))
    
    timer = QTimer()
    timer.timeout.connect(simulate_data)
    timer.start(1000)
    
    sys.exit(app.exec())
