from PySide6.QtCore import QTimer
from UI.styles import Theme
from modules.ai.face_analyzer import DistanceStatus
import cv2
import time


class AuthViewLogic:
    def __init__(self, view):
        self.view = view

    def on_ai_result(self, result: dict):
        view = self.view
        if not view.is_checking or view.auth_worker is None:
            return
        
        # Neu da co ket qua authentication (success/fail), khong update nua
        if view.authentication_completed:
            return

        view.last_ai_result = result

        time_elapsed = result.get("time_elapsed", 0)
        fail_count = result.get("fail_count", 0)

        view.timer_label.setText(f"TIME: {int(time_elapsed)}s")
        view.fail_label.setText(f"FAILS: {fail_count}/3")
        view.fail_count_changed.emit(fail_count)

        if fail_count >= 2:
            view.fail_label.setStyleSheet(
                f"color: {Theme.DANGER_RED}; font-size: 11px; font-weight: bold; font-family: 'Consolas';"
            )
        else:
            view.fail_label.setStyleSheet(
                f"color: {Theme.SECONDARY_RED}; font-size: 11px; font-weight: bold; font-family: 'Consolas';"
            )

        completed_challenges = result.get("completed_challenges", [])
        completed_count = len(completed_challenges) if isinstance(completed_challenges, list) else 0
        progress_status = result.get("liveness_status", "PROCESSING")
        steps_done = min(completed_count, 3)
        if progress_status == "REAL":
            steps_done += 1
        progress_value = int(round((steps_done / 4) * 100))
        view.liveness_progress.setValue(progress_value)
        
        # Cap nhat progress label
        if hasattr(view, 'progress_label'):
            step_names = ["Checking", "Challenge", "Verifying", "Complete"]
            current_step = min(steps_done, 3)
            view.progress_label.setText(f"Step {steps_done}/4 - {step_names[current_step]}")

        if not result.get("has_face"):
            view.status_message.setText("No face detected")
            view.status_message.setStyleSheet(
                f"color: {Theme.DANGER_RED}; font-size: 13px; font-weight: bold; "
                f"background-color: rgba(0, 0, 0, 180); border-radius: 8px; padding: 8px; "
                f"border: 1px solid {Theme.DANGER_RED};"
            )
            view.liveness_label.setText("STATUS: NO FACE")
            view.liveness_progress.setValue(0)
            return

        is_real = result.get("is_real", False)
        l_status = result.get("liveness_status", "PROCESSING")
        instruction = result.get("pose_instruction", "")
        dist_status = result.get("distance_status")

        view.liveness_label.setText(f"STATUS: {l_status}")

        if l_status in ["SPOOF/FAKE", "SPOOF/VIDEO", "SPOOF/FLAT", "SPOOF/STRONG", "SPOOF/SOFT"]:
            # Hien thi ly do cu the tu instruction
            spoof_msg = instruction if instruction else "WARNING: SPOOF DETECTED!"
            view.status_message.setText(spoof_msg)
            view.status_message.setStyleSheet(
                f"color: {Theme.DANGER_RED}; font-size: 13px; font-weight: bold; "
                f"background-color: rgba(255, 50, 50, 50); border-radius: 8px; padding: 8px; "
                f"border: 1px solid {Theme.DANGER_RED};"
            )
            return

        # Neu chua xac thuc xong (PROCESSING) -> hien thi instruction, KHONG check distance
        if not is_real or l_status == "PROCESSING":
            # Reset liveness passed state neu dang processing
            view.liveness_passed = False
            view.liveness_passed_time = None
            
            view.status_message.setText(instruction if instruction else "Verifying liveness...")
            view.status_message.setStyleSheet(
                f"color: {Theme.PRIMARY}; font-size: 13px; font-weight: bold; "
                f"background-color: rgba(0, 0, 0, 180); border-radius: 8px; padding: 8px; "
                f"border: 1px solid {Theme.PRIMARY};"
            )
            return

        # === LIVENESS PASSED - Bat dau qua trinh face recognition ===
        now = time.time()
        
        # Lan dau pass liveness -> ghi nhan thoi gian
        if not view.liveness_passed:
            view.liveness_passed = True
            view.liveness_passed_time = now
            print(f"[AuthView] Liveness PASSED! Bat dau delay 2s truoc khi face recognition")
        
        # Tinh thoi gian da troi qua ke tu khi pass liveness
        time_since_liveness = now - view.liveness_passed_time
        
        # Check timeout 10s cho face recognition
        if time_since_liveness > view.face_recognition_timeout:
            print(f"[AuthView] Face recognition TIMEOUT sau {time_since_liveness:.1f}s")
            view.authentication_completed = True
            view.liveness_passed = False
            view.status_message.setText("Face recognition timeout!")
            view.status_message.setStyleSheet(
                f"color: {Theme.DANGER_RED}; font-size: 13px; font-weight: bold; "
                f"background-color: rgba(255, 50, 50, 50); border-radius: 8px; padding: 8px; "
                f"border: 1px solid {Theme.DANGER_RED};"
            )
            self.on_timeout_warning("TIMEOUT! Face recognition that bai")
            return
        
        # Delay 2s - hien thi text "Dang xac thuc khuon mat..."
        if time_since_liveness < view.liveness_delay:
            remaining = view.liveness_delay - time_since_liveness
            view.status_message.setText(f"Liveness OK! Xac thuc khuon mat trong {remaining:.1f}s...")
            view.status_message.setStyleSheet(
                f"color: {Theme.SECONDARY_GREEN}; font-size: 13px; font-weight: bold; "
                f"background-color: rgba(0, 0, 0, 180); border-radius: 8px; padding: 8px; "
                f"border: 1px solid {Theme.SECONDARY_GREEN};"
            )
            return

        # === SAU DELAY 2s - Check distance va face recognition ===
        if dist_status == DistanceStatus.TOO_FAR:
            view.status_message.setText("Move closer to camera")
            view.status_message.setStyleSheet(
                f"color: {Theme.SECONDARY_GREEN}; font-size: 13px; font-weight: bold; "
                f"background-color: rgba(0, 0, 0, 180); border-radius: 8px; padding: 8px; "
                f"border: 1px solid {Theme.SECONDARY_GREEN};"
            )
            return
        if dist_status == DistanceStatus.TOO_CLOSE:
            view.status_message.setText("Move back from camera")
            view.status_message.setStyleSheet(
                f"color: {Theme.SECONDARY_GREEN}; font-size: 13px; font-weight: bold; "
                f"background-color: rgba(0, 0, 0, 180); border-radius: 8px; padding: 8px; "
                f"border: 1px solid {Theme.SECONDARY_GREEN};"
            )
            return

        if dist_status == DistanceStatus.OK:
            if now - view.last_auth_time > view.auth_cooldown:
                if "embedding" in result and result["embedding"] is not None:
                    view.status_message.setText("Recognizing face...")
                    view.status_message.setStyleSheet(
                        f"color: {Theme.SECONDARY_GREEN}; font-size: 13px; font-weight: bold; "
                        f"background-color: rgba(0, 0, 0, 180); border-radius: 8px; padding: 8px; "
                        f"border: 1px solid {Theme.SECONDARY_GREEN};"
                    )
                    view.auth_worker.authenticate(result["embedding"])
                    view.last_auth_time = now
            else:
                if "SUCCESS" not in view.status_message.text():
                    view.status_message.setText("Recognizing...")

    def on_timeout_warning(self, warning_msg: str):
        view = self.view
        print(f"[AuthView] Timeout warning received: {warning_msg}")

        view.status_message.setText(f"{warning_msg}")
        view.status_message.setStyleSheet(
            f"color: {Theme.DANGER_RED}; font-size: 13px; font-weight: bold; "
            f"background-color: rgba(255, 50, 50, 50); border-radius: 8px; padding: 8px; "
            f"border: 1px solid {Theme.DANGER_RED};"
        )

        if "FAIL" in warning_msg.upper() or "TIMEOUT" in warning_msg.upper():
            self.start_lockout_period(10)

    def start_lockout_period(self, seconds: int):
        view = self.view
        print(f"[AuthView] Starting lockout period: {seconds}s")

        view.is_locked = True
        view.stop_authentication()

        view.btn_toggle.setEnabled(False)
        view.btn_toggle.setText(f"Wait {seconds}s")
        view.btn_toggle.setStyleSheet(
            "QPushButton { color: #666666; border: 2px solid #666666; "
            "border-radius: 22px; font-size: 13px; font-weight: bold; background: transparent; }"
        )

        view.lockout_timer = QTimer(view)
        remaining = [seconds]

        def countdown():
            remaining[0] -= 1
            if remaining[0] > 0:
                view.btn_toggle.setText(f"Wait {remaining[0]}s")
            else:
                self.end_lockout_period()

        view.lockout_timer.timeout.connect(countdown)
        view.lockout_timer.start(1000)

    def end_lockout_period(self):
        view = self.view
        print("[AuthView] Lockout period ended")

        if view.lockout_timer:
            view.lockout_timer.stop()
            view.lockout_timer = None

        view.is_locked = False
        view.btn_toggle.setEnabled(True)
        view.btn_toggle.setText("START AUTHENTICATION")
        view.btn_toggle.setStyleSheet(
            f"QPushButton {{ color: {Theme.PRIMARY}; border: 2px solid {Theme.PRIMARY}; "
            "border-radius: 22px; font-size: 13px; font-weight: bold; background: transparent; }}"
        )

        if view.auth_worker:
            view.auth_worker.reset_fail_count()

        view.status_message.setText("Ready to authenticate")
        view.status_message.setStyleSheet(
            f"color: {Theme.SECONDARY_GREEN}; font-size: 13px; font-weight: bold; "
            f"background-color: rgba(0, 0, 0, 180); border-radius: 8px; padding: 8px; "
            f"border: 1px solid {Theme.SECONDARY_GREEN};"
        )

    def on_auth_result(self, success, user_id, distance):
        view = self.view
        view.authentication_completed = True  # Danh dau da co ket qua
        view.liveness_passed = False  # Reset state
        
        if success:
            info = view.auth_worker.authenticator.get_user_info(user_id)
            name = info["fullname"] if info else user_id
            view.status_message.setText(f"SUCCESS: {name}")
            view.status_message.setStyleSheet(
                f"color: {Theme.SECONDARY_GREEN}; font-size: 13px; font-weight: bold; "
                f"background-color: rgba(0, 100, 50, 100); border-radius: 8px; padding: 8px; "
                f"border: 1px solid {Theme.SECONDARY_GREEN};"
            )
            print(f"[AuthView] Authentication SUCCESS: {name}")
            view.authentication_success.emit(user_id, name)
        else:
            view.status_message.setText("Xác thực thất bại")
            view.status_message.setStyleSheet(
                f"color: {Theme.DANGER_RED}; font-size: 13px; font-weight: bold; "
                f"background-color: rgba(255, 50, 50, 50); border-radius: 8px; padding: 8px; "
                f"border: 1px solid {Theme.DANGER_RED};"
            )
            print(f"[AuthView] Authentication FAILED - not recognized")

    def draw_ui_overlay(self, frame):
        view = self.view
        display_frame = frame.copy()
        h, w = display_frame.shape[:2]

        color_hex = Theme.PRIMARY

        if view.last_ai_result:
            if not view.last_ai_result.get("has_face"):
                color_hex = Theme.DANGER_RED
            elif not view.last_ai_result.get("is_real", True):
                color_hex = Theme.SECONDARY_RED
            elif view.last_ai_result.get("distance_status") == DistanceStatus.OK:
                if "SUCCESS" in view.status_message.text():
                    color_hex = Theme.SECONDARY_GREEN
                elif "NOT RECOGNIZED" in view.status_message.text().upper():
                    color_hex = Theme.DANGER_RED
                else:
                    color_hex = Theme.SECONDARY_GREEN
            else:
                color_hex = "#FFD700"

        r, g, b = int(color_hex[1:3], 16), int(color_hex[3:5], 16), int(color_hex[5:7], 16)
        cv2.ellipse(
            display_frame,
            (w // 2, h // 2),
            (int(min(h, w) * 0.38), int(min(h, w) * 0.52)),
            0,
            0,
            360,
            (b, g, r),
            2,
        )

        view.camera_panel.display_frame(display_frame)
