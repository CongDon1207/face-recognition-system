import cv2
import numpy as np
import mediapipe as mp
import time
import random
from modules.ai.pose_logic import calculate_pose_ratio, RATIO_THRESHOLDS

class LivenessDetector:
    def __init__(self):
        self.laplacian_base_threshold = 20.0
        self.laplacian_adaptive = True
        self.brightness_compensation = True
        
        self.blink_threshold = 0.22
        self.head_move_threshold = 20.0
        self.z_std_threshold = 0.02
        
        self.brightness_history = []
        self.brightness_calibration_frames = 10
        self.avg_brightness = None
        self.lighting_quality = "UNKNOWN"
        
        self.blink_count = 0
        self.is_blinking = False
        self.yaw_offset = None
        self.moves_completed = []
        
        self.strong_spoof_detected = False
        self.strong_spoof_reason = None
        self.soft_spoof_score = 0
        self.soft_spoof_reasons = []
        self.SOFT_SPOOF_THRESHOLD = 4  # Giam tu 4 xuong 2 de nhanh hon
        
        self.last_yaw_at_blink = None
        self.has_dynamic_movement = False
        self.video_replay_flag = False

        self.mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        self.ear_samples = []
        self.ear_calibrated = False
        self.ear_open = None
        self.ear_close = None
        self.ear_threshold = None
        self.calibration_frames = 15  # Giam tu 30 xuong 15 de nhanh hon

        self.challenge_list = random.sample(["BLINK", "TURN_LEFT", "TURN_RIGHT", "BLINK_TWICE"], k=3)
        self.current_challenge_index = 0
        self.challenge_time = 0
        self.challenge_window = 4.0
        self.completed_challenges = []
        self.required_blink_count = 1
        
        # Stability cho challenges - tranh flicker
        self.challenge_stable_frames = 0
        self.challenge_stable_required = 2  # Can 2 frames lien tiep de xac nhan
        self.last_h_ratio = None
        self.waiting_for_neutral = False  # Đợi user quay về frontal sau khi hoàn thành challenge
        
        self.spoof_detected = False
        self.prev_gray = None
        self.brightness_buffer = []
        self.nose_y_buffer = []
        self.ear_buffer = []
        self.buffer_size = 30
        self.frame_rate = 30.0
        self.tremor_min_freq = 8.0
        self.tremor_max_freq = 12.0
        self.tremor_amp_thresh = 0.1
        self.flicker_freqs = [50, 60, 100, 120]
        self.flicker_amp_thresh = 40.0
        self.flow_var_thresh = 0.1
        self.entropy_thresh = 1.5
        self.moire_high_thresh = 100.0
        self.rolling_angle_std_thresh = 0.1

        self.moire_threshold = 0.005
        self.chromatic_thresh = 50.0
        
        self.flash_detection_enabled = True
        self.prev_brightness = None
        self.flash_cooldown = 0
        self.flash_history = []
        self.brightness_change_threshold = 40.0
        
        self.static_depth_frames = 0
        self.low_entropy_count = 0
        self.prev_depth_delta = None

    def detect_moire_pattern(self, face_img):
        if face_img is None or face_img.size == 0:
            return False
            
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        
        h, w = gray.shape
        dft = np.fft.fft2(gray)
        dft_shift = np.fft.fftshift(dft)
        magnitude_spectrum = 20 * np.log(np.abs(dft_shift) + 1)
        
        crow, ccol = h // 2, w // 2
        mask_size = min(h, w) // 5
        magnitude_spectrum[crow-mask_size:crow+mask_size, ccol-mask_size:ccol+mask_size] = 0
        
        high_freq_energy = np.mean(magnitude_spectrum)
        
        moire_thresh = 45.0 
        if self.lighting_quality == "GOOD":
            moire_thresh = 40.0
            
        return high_freq_energy > moire_thresh

    def detect_flash(self, current_brightness):
        if self.prev_brightness is None:
            self.prev_brightness = current_brightness
            return False
        
        brightness_change = abs(current_brightness - self.prev_brightness)
        is_flash = brightness_change > self.brightness_change_threshold
        
        if is_flash:
            self.flash_history.append(time.time())
            if len(self.flash_history) > 10:
                self.flash_history.pop(0)
            self.flash_cooldown = 10 # dùng frame để tránh phát hiện liên tục
        
        self.prev_brightness = current_brightness
        return is_flash

    def is_under_flash_effect(self):
        if self.flash_cooldown > 0:
            self.flash_cooldown -= 1
            return True
        return False

    def check_chromatic_aberration(self, face_img):
        if face_img is None: 
            return False
        img_f = face_img.astype(float)
        b, g, r = cv2.split(img_f)
        
        diff_rg = np.std(r - g)
        diff_gb = np.std(g - b)
        total_diff = diff_rg + diff_gb
        
        is_aberration = total_diff > self.chromatic_thresh
        return is_aberration

    def check_temporal_entropy(self):
        if len(self.brightness_buffer) < self.buffer_size:
            return
        
        signal = np.array(self.brightness_buffer)
        hist, _ = np.histogram(signal, bins=20)
        hist = hist / (np.sum(hist) + 1e-10)
        entropy = -np.sum(hist * np.log2(hist + 1e-10))
        
        if entropy < self.entropy_thresh:
            self.low_entropy_count += 1
            if self.low_entropy_count > 5:
                if "LOW_ENTROPY" not in self.soft_spoof_reasons:
                    self.soft_spoof_score += 1
                    self.soft_spoof_reasons.append("LOW_ENTROPY")
                    print("[SPOOF SOFT +1] LOW_ENTROPY (entropy quá thấp)")
        else:
            self.low_entropy_count = max(0, self.low_entropy_count - 1)

    def assess_lighting(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        
        self.brightness_history.append(brightness)
        if len(self.brightness_history) > self.brightness_calibration_frames:
            self.brightness_history.pop(0)
            
        if len(self.brightness_history) >= self.brightness_calibration_frames:
            self.avg_brightness = np.mean(self.brightness_history)
            
            if self.avg_brightness > 100:
                self.lighting_quality = "GOOD"
            elif self.avg_brightness > 60:
                self.lighting_quality = "LOW"
            else:
                self.lighting_quality = "VERY_LOW"
                
        return brightness

    def enhance_image_for_low_light(self, img):
        if self.lighting_quality == "VERY_LOW":
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            enhanced = cv2.bilateralFilter(enhanced, d=9, sigmaColor=75, sigmaSpace=75)
            return enhanced
        elif self.lighting_quality == "LOW":
            gamma = 1.5
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 
                            for i in np.arange(0, 256)]).astype("uint8")
            enhanced = cv2.LUT(img, table)
            enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0)
            return enhanced
        return img

    def get_adaptive_threshold(self, brightness):
        if not self.laplacian_adaptive:
            return self.laplacian_base_threshold
            
        if brightness < 50:
            return 8.0 + (brightness / 50) * 4.0
        elif brightness < 100:
            return 12.0 + ((brightness - 50) / 50) * 6.0
        else:
            return 18.0 + min((brightness - 100) / 50, 1.0) * 7.0

    def check_texture(self, face_img, frame_brightness=None):
        if face_img is None or face_img.size == 0:
            return False, 0
            
        enhanced_img = self.enhance_image_for_low_light(face_img)
        gray = cv2.cvtColor(enhanced_img, cv2.COLOR_BGR2GRAY)
        
        score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        if frame_brightness is not None and self.laplacian_adaptive:
            threshold = self.get_adaptive_threshold(frame_brightness)
        else:
            threshold = self.laplacian_base_threshold
        
        is_real = threshold < score < 55.0
        
        if not is_real and self.lighting_quality != "VERY_LOW":
            gradient_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            gradient_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)
            gradient_score = np.mean(gradient_magnitude)
            
            if gradient_score > 15.0:
                is_real = True
        
        if not is_real and self.lighting_quality == "GOOD":
            print(f"[TEXTURE LOW] Laplacian score: {score:.1f} (threshold ~{threshold:.1f})")
        
        return is_real, score

    def calculate_ear(self, eye_landmarks):
        try:
            p2_p6 = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
            p3_p5 = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
            p1_p4 = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
            return (p2_p6 + p3_p5) / (2.0 * p1_p4)
        except Exception:
            return 0.3

    def check_head_movement_ratio(self, mesh_coords, width, height, direction=None):
        """
        Kiểm tra xoay đầu bằng geometric ratio (giống enrollment).
        Thay thế check_head_movement cũ dùng Euler angles.
        """
        h_ratio, v_ratio = calculate_pose_ratio(mesh_coords, width, height)
        if h_ratio is None:
            self.challenge_stable_frames = 0
            return False
        
        # Lưu h_ratio để debug
        self.last_h_ratio = h_ratio
        
        cfg_left = RATIO_THRESHOLDS["left"]
        cfg_right = RATIO_THRESHOLDS["right"]
        
        # Thêm hysteresis để ổn định (lớn hơn enrollment vì auth cần dễ hơn)
        hysteresis = 0.3
        
        is_left = h_ratio > (cfg_left["h_min"] - hysteresis)
        is_right = h_ratio < (cfg_right["h_max"] + hysteresis)
        
        # Check V-ratio lax
        v_ok = v_ratio is None or (0.1 <= v_ratio <= 0.9)
        
        # Stability: cần nhiều frames liên tiếp để xác nhận
        if direction == 'LEFT':
            if is_left and v_ok:
                self.challenge_stable_frames += 1
                if self.challenge_stable_frames >= self.challenge_stable_required:
                    print(f"[HEAD MOVE] Quay TRÁI phát hiện (h_ratio: {h_ratio:.2f}, stable: {self.challenge_stable_frames})")
                    return True
            else:
                self.challenge_stable_frames = 0
            return False
            
        elif direction == 'RIGHT':
            if is_right and v_ok:
                self.challenge_stable_frames += 1
                if self.challenge_stable_frames >= self.challenge_stable_required:
                    print(f"[HEAD MOVE] Quay PHẢI phát hiện (h_ratio: {h_ratio:.2f}, stable: {self.challenge_stable_frames})")
                    return True
            else:
                self.challenge_stable_frames = 0
            return False
        
        # Không có direction cụ thể - check cả hai
        updated = False
        if is_left and v_ok and "LEFT" not in self.moves_completed:
            self.moves_completed.append("LEFT")
            updated = True
            print(f"[HEAD MOVE] Quay TRÁI phát hiện (h_ratio: {h_ratio:.2f})")
        elif is_right and v_ok and "RIGHT" not in self.moves_completed:
            self.moves_completed.append("RIGHT")
            updated = True
            print(f"[HEAD MOVE] Quay PHẢI phát hiện (h_ratio: {h_ratio:.2f})")
        
        return updated or all(m in self.moves_completed for m in ['LEFT', 'RIGHT'])

    def check_head_movement(self, yaw_raw, direction=None):
        """Legacy method - giữ lại để tương thích ngược"""
        current_yaw = np.degrees(yaw_raw) if yaw_raw is not None else 0
        
        if self.yaw_offset is None:
            if abs(current_yaw) < 10:
                self.yaw_offset = current_yaw
                print("[CALIB] Yaw offset đã được set")
            return False
            
        diff = current_yaw - self.yaw_offset
        actual_yaw = (diff + 180) % 360 - 180 
        
        updated = False
        if actual_yaw > self.head_move_threshold and "RIGHT" not in self.moves_completed:
            self.moves_completed.append("RIGHT")
            updated = True
            print(f"[HEAD MOVE] Quay PHẢI phát hiện (yaw: {actual_yaw:.1f} độ)")
        elif actual_yaw < -self.head_move_threshold and "LEFT" not in self.moves_completed:
            self.moves_completed.append("LEFT")
            updated = True
            print(f"[HEAD MOVE] Quay TRÁI phát hiện (yaw: {actual_yaw:.1f} độ)")
        
        if direction:
            return direction in self.moves_completed
        return updated or all(m in self.moves_completed for m in ['LEFT', 'RIGHT'])
        
        if direction:
            return direction in self.moves_completed
        return updated or all(m in self.moves_completed for m in ['LEFT', 'RIGHT'])

    def check_depth(self, mesh_coords):
        try:
            z_values = np.array([p.z for p in mesh_coords])
            z_std = np.std(z_values)
            
            nose_z = mesh_coords[1].z
            ears_z = (mesh_coords[234].z + mesh_coords[454].z) / 2
            depth_delta = abs(nose_z - ears_z)

            eye_dist = abs(mesh_coords[33].x - mesh_coords[263].x)
            face_height = abs(mesh_coords[10].y - mesh_coords[152].y)
            aspect_ratio = eye_dist / face_height

            is_3d = (depth_delta > 0.04) and (z_std > self.z_std_threshold)
            
            if z_std > 0.05:
                if len(self.moves_completed) == 0 and self.blink_count == 0:
                    is_3d = is_3d and (depth_delta < 0.5)

            return is_3d, depth_delta
        except:
            return True, 0

    def check_temporal_and_screen(self, frame, mesh_coords, ear, timestamp, h):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        current_brightness = np.mean(gray)
        
        is_flash = self.detect_flash(current_brightness)
        if is_flash:
            print("[FLASH] Phát hiện thay đổi sáng đột ngột")
            
            
        skip_soft_checks = self.lighting_quality in ["VERY_LOW", "LOW"] or self.is_under_flash_effect()
        
        if self.prev_gray is not None and not skip_soft_checks:
            flow = cv2.calcOpticalFlowFarneback(self.prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            if np.var(mag) < self.flow_var_thresh:
                self.low_flow_frames = getattr(self, 'low_flow_frames', 0) + 1
            else:
                self.low_flow_frames = max(0, getattr(self, 'low_flow_frames', 0) - 2)
            
            if self.low_flow_frames > 20:
                if "STATIC_FLOW" not in self.soft_spoof_reasons:
                    self.soft_spoof_score += 1
                    self.soft_spoof_reasons.append("STATIC_FLOW")
                    print("[SPOOF SOFT +1] STATIC_FLOW (không có chuyển động giữa các frame)")
                self.low_flow_frames = 0
                
        brightness = np.mean(gray)
        self.brightness_buffer.append(brightness)
        if len(self.brightness_buffer) > self.buffer_size:
            self.brightness_buffer.pop(0)
            
        if len(self.brightness_buffer) == self.buffer_size and not skip_soft_checks:
            signal = np.array(self.brightness_buffer) - np.mean(self.brightness_buffer)
            fft = np.abs(np.fft.rfft(signal))
            
            if np.max(fft) > 35.0:
                if "FLICKER" not in self.soft_spoof_reasons:
                    self.soft_spoof_score += 1
                    self.soft_spoof_reasons.append("FLICKER")
                    print("[SPOOF SOFT +1] FLICKER (nhấp nháy ánh sáng)")
            
            freqs = np.fft.rfftfreq(self.buffer_size, 1 / self.frame_rate)
            flicker_detected = False
            for f in self.flicker_freqs:
                idx = np.argmin(np.abs(freqs - f))
                if fft[idx] > self.flicker_amp_thresh:
                    flicker_detected = True
                    break
            
            if flicker_detected and "SCREEN_FLICKER" not in self.soft_spoof_reasons:
                self.soft_spoof_score += 1
                self.soft_spoof_reasons.append("SCREEN_FLICKER")
                print("[SPOOF SOFT +1] SCREEN_FLICKER (tần số màn hình)")

        if mesh_coords is not None:
            nose_y = mesh_coords[1].y * h
            self.nose_y_buffer.append(nose_y)
            if len(self.nose_y_buffer) > self.buffer_size:
                self.nose_y_buffer.pop(0)

        self.prev_gray = gray.copy()

        if mesh_coords is not None and not skip_soft_checks:
            if len(self.nose_y_buffer) == self.buffer_size:
                signal = np.array(self.nose_y_buffer) - np.mean(self.nose_y_buffer)
                fft = np.abs(np.fft.rfft(signal))
                freqs = np.fft.rfftfreq(self.buffer_size, 1 / self.frame_rate)
                peak_idx = np.argmax(fft[1:]) + 1
                peak_freq = freqs[peak_idx]
                peak_amplitude = fft[peak_idx]
                
                if not (self.tremor_min_freq <= peak_freq <= self.tremor_max_freq) and peak_amplitude > 0.5:
                    if "NO_TREMOR" not in self.soft_spoof_reasons:
                        self.soft_spoof_score += 1
                        self.soft_spoof_reasons.append("NO_TREMOR")
                        print("[SPOOF SOFT +1] NO_TREMOR (không có rung tự nhiên)")

        self.ear_buffer.append(ear)
        if len(self.ear_buffer) > self.buffer_size:
            self.ear_buffer.pop(0)
            
        if not skip_soft_checks:
            self.check_temporal_entropy()

    def check_liveness(self, frame, face_box, landmarks=None, head_pose=None, timestamp=time.time()):
        instruction = "Vui lòng nhìn thẳng vào camera"
        is_really_real = False
        status = "PROCESSING"
        
        h, w = frame.shape[:2]
        
        frame_brightness = self.assess_lighting(frame)
        
        if self.lighting_quality in ["LOW", "VERY_LOW"]:
            frame = self.enhance_image_for_low_light(frame)
        
        x1, y1, x2, y2 = face_box
        face_img = frame[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
        
        if face_img.size == 0:
            return False, 0, {"status": "SPOOF", "instruction": "Không tìm thấy mặt"}

        is_texture_real, score = self.check_texture(face_img, frame_brightness)
        
        # Kiem tra moire pattern (man hinh dien thoai/may tinh)
        has_moire = self.detect_moire_pattern(face_img)
        if has_moire and "MOIRE" not in self.soft_spoof_reasons:
            self.soft_spoof_score += 1
            self.soft_spoof_reasons.append("MOIRE")
            print(f"[SPOOF SOFT +1] MOIRE (phát hiện pattern màn hình)")
        
        # Kiểm tra texture - bỏ điều kiện lighting_quality == GOOD
        if not is_texture_real and "LOW_TEXTURE" not in self.soft_spoof_reasons:
            self.soft_spoof_score += 1
            self.soft_spoof_reasons.append("LOW_TEXTURE")
            print(f"[SPOOF SOFT +1] LOW_TEXTURE (score: {score:.1f})")
        
        if self.check_chromatic_aberration(face_img) and not self.is_under_flash_effect():
            if "CHROMATIC" not in self.soft_spoof_reasons:
                self.soft_spoof_score += 1
                self.soft_spoof_reasons.append("CHROMATIC")
                print("[SPOOF SOFT +1] CHROMATIC (sai lệch màu bất thường)")

        blink_status = False
        is_face_3d = False
        current_yaw_deg = np.degrees(head_pose) if head_pose is not None else 0

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_results = self.mp_face_mesh.process(rgb_frame)

        mesh_coords = None
        head_moved = False
        
        if mp_results.multi_face_landmarks:
            mesh_coords = mp_results.multi_face_landmarks[0].landmark
            
            is_face_3d, depth_val = self.check_depth(mesh_coords)
            
            if not is_face_3d:
                self.strong_spoof_detected = True
                self.strong_spoof_reason = "FLAT_DEPTH"
                print("[SPOOF STRONG] FLAT_DEPTH - mặt phẳng")
                return False, score, {
                    "status": "SPOOF/FLAT",
                    "instruction": "Phát hiện hình ảnh"
                }
            
            head_moved = self.check_head_movement_ratio(mesh_coords, w, h) if mesh_coords else False
            
            if self.prev_depth_delta is not None and head_moved:
                depth_stability = abs(depth_val - self.prev_depth_delta)
                if depth_stability < 0.0001:
                    self.static_depth_frames += 1
                    if self.static_depth_frames > 10:
                        self.strong_spoof_detected = True
                        self.strong_spoof_reason = "STATIC_DEPTH_MOVE"
                        print("[SPOOF STRONG] STATIC_DEPTH_MOVE - depth không thay đổi khi di chuyển")
                else:
                    self.static_depth_frames = 0

            self.prev_depth_delta = depth_val
            
            def get_coords(idx):
                return np.array([mesh_coords[idx].x * w, mesh_coords[idx].y * h])
            
            left_eye = [get_coords(i) for i in [33, 160, 158, 133, 153, 144]]
            right_eye = [get_coords(i) for i in [362, 385, 387, 263, 373, 380]]
            ear = (self.calculate_ear(left_eye) + self.calculate_ear(right_eye)) / 2.0

            if not self.ear_calibrated:
                if not self.is_under_flash_effect():
                    self.ear_samples.append(ear)
                
                if len(self.ear_samples) >= self.calibration_frames:
                    self.ear_open = np.mean(self.ear_samples)
                    self.ear_close = self.ear_open * 0.6
                    self.ear_threshold = (self.ear_open + self.ear_close) / 2
                    self.ear_calibrated = True
                    print(f"[CALIBRATED] EAR hoàn tất | mở: {self.ear_open:.3f} | ngưỡng: {self.ear_threshold:.3f}")

            blink_detected = False
            if self.ear_calibrated and not self.is_under_flash_effect():
                if ear < self.ear_threshold:
                    if not self.is_blinking:
                        self.is_blinking = True
                        self.last_yaw_at_blink = current_yaw_deg
                else:
                    if self.is_blinking:
                        # Đơn giản hóa - chấp nhận nháy mắt trực tiếp
                        # Các check anti-replay khác (depth, temporal) đã đủ
                        self.blink_count += 1
                        blink_detected = True
                        print(f"[BLINK] Phát hiện nháy mắt | Count: {self.blink_count}/{self.required_blink_count}")
                        self.is_blinking = False

            if self.blink_count >= self.required_blink_count:
                blink_status = True

        self.check_temporal_and_screen(frame, mesh_coords, ear if 'ear' in locals() else 0.3, timestamp, h)

        if self.strong_spoof_detected:
            status = "SPOOF/STRONG"
            instruction = f"Phát hiện giả mạo: {self.strong_spoof_reason}"
        
        if self.soft_spoof_score >= self.SOFT_SPOOF_THRESHOLD:
            status = "SPOOF/SOFT"
            reasons_str = ", ".join(self.soft_spoof_reasons[:3])
            vietnamese_reasons = {
                "LOW_TEXTURE": "kết cấu da kém",
                "FLICKER": "nhấp nháy màn hình",
                "NO_TREMOR": "không rung tự nhiên",
                "SCREEN_FLICKER": "tần số màn hình",
                "STATIC_FLOW": "không có chuyển động",
                "CHROMATIC": "sai lệch màu",
                "LOW_ENTROPY": "hình ảnh quá tĩnh",
                "MOIRE": "phát hiện màn hình"
            }
            display_reasons = [vietnamese_reasons.get(r, r) for r in self.soft_spoof_reasons[:3]]
            instruction = f"Phát hiện giả mạo:\n{', '.join(display_reasons)}.\nVui lòng dùng khuôn mặt thật."
            print(f"[SPOOF SOFT FINAL] Đạt ngưỡng ({self.soft_spoof_score}/{self.SOFT_SPOOF_THRESHOLD}): {reasons_str}")
        elif not self.ear_calibrated:
            status = "PROCESSING"
            instruction = "Xác thực chống giả mạo..."
        elif not self.strong_spoof_detected and status == "PROCESSING":
            if self.current_challenge_index < len(self.challenge_list):
                current_challenge = self.challenge_list[self.current_challenge_index]
                if self.challenge_time == 0:
                    self.challenge_time = timestamp
                    print(f"[CHALLENGE {self.current_challenge_index+1}/{len(self.challenge_list)}] Bắt đầu: {current_challenge}")
                
                time_diff = timestamp - self.challenge_time
                
                if time_diff > self.challenge_window + 6:
                    self.strong_spoof_detected = True
                    self.strong_spoof_reason = "CHALLENGE_TIMEOUT"
                    self.current_challenge_index = 0
                    self.challenge_time = 0
                    self.blink_count = 0
                    instruction = "Phản ứng quá chậm"
                    print("[SPOOF STRONG] CHALLENGE_TIMEOUT - quá chậm")
                else:
                    # Check nếu đang đợi user quay về frontal
                    if self.waiting_for_neutral:
                        h_ratio, v_ratio = calculate_pose_ratio(mesh_coords, w, h) if mesh_coords else (None, None)
                        # Kiểm tra có phải frontal không (h_ratio gần 1.0)
                        if h_ratio and 0.7 <= h_ratio <= 1.3:
                            self.waiting_for_neutral = False
                            print(f"[NEUTRAL] User đã quay về frontal (h_ratio: {h_ratio:.2f}), bắt đầu challenge mới")
                        else:
                            # Đợi im lặng, không hiển thị gì cả
                            status = "PROCESSING"
                            return is_really_real, score, {
                                "status": status,
                                "instruction": "",
                                "moves_completed": self.moves_completed,
                                "completed_challenges": self.completed_challenges,
                                "blink_count": self.blink_count,
                                "lighting": self.lighting_quality,
                                "strong_spoof": self.strong_spoof_detected,
                                "strong_reason": self.strong_spoof_reason,
                                "soft_score": self.soft_spoof_score,
                                "soft_reasons": self.soft_spoof_reasons
                            }
                    
                    instruction = f"Hãy {current_challenge.replace('TURN_LEFT', 'quay trái').replace('TURN_RIGHT', 'quay phải').replace('BLINK_TWICE', 'nháy mắt hai lần').replace('BLINK', 'nháy mắt một lần')}"
                    
                    completed = False
                    if 'TURN_LEFT' in current_challenge:
                        # Dùng geometric ratio thay vì euler angles
                        if mesh_coords and self.check_head_movement_ratio(mesh_coords, w, h, 'LEFT'):
                            completed = True
                    elif 'TURN_RIGHT' in current_challenge:
                        if mesh_coords and self.check_head_movement_ratio(mesh_coords, w, h, 'RIGHT'):
                            completed = True
                    elif 'BLINK' in current_challenge:
                        self.required_blink_count = 2 if 'TWICE' in current_challenge else 1
                        if self.blink_count >= self.required_blink_count and blink_detected:
                            completed = True
                    
                    if completed:
                        if time_diff > self.challenge_window:
                            print(f"[WARNING] Challenge hoàn thành nhưng QUÁ THỜI GIAN ({time_diff:.1f}s > {self.challenge_window}s)")
                        else:
                            print(f"[SUCCESS] Challenge '{current_challenge}' HOÀN THÀNH trong {time_diff:.1f}s")
                            self.completed_challenges.append(current_challenge)
                            self.current_challenge_index += 1
                            self.challenge_time = 0
                            self.blink_count = 0
                            self.challenge_stable_frames = 0  # Reset stability counter
                            self.moves_completed = []  # Reset tất cả moves, không phân biệt TURN hay BLINK
                            
                            # Nếu là TURN challenge, đợi user quay về frontal trước khi bắt đầu challenge mới
                            if 'TURN' in current_challenge:
                                self.waiting_for_neutral = True
                                print(f"[WAITING] Đợi user quay về frontal trước khi bắt đầu challenge tiếp theo")
                
                status = "PROCESSING"
            else:
                # Da hoan thanh tat ca challenges -> REAL
                is_really_real = True
                status = "REAL"
                instruction = "Xác thực thành công!"
                print("[LIVENESS SUCCESS] Người thật - Xác thực thành công!")
        if self.lighting_quality == "VERY_LOW":
            instruction = "VUI LÒNG TĂNG ÁNH SÁNG!" + instruction
        elif self.is_under_flash_effect():
            instruction = "VUI LÒNG TẮT FLASH!" + instruction
        return is_really_real, score, {
            "status": status,
            "instruction": instruction,
            "moves_completed": self.moves_completed,
            "completed_challenges": self.completed_challenges,
            "blink_count": self.blink_count,
            "lighting": self.lighting_quality,
            "strong_spoof": self.strong_spoof_detected,
            "strong_reason": self.strong_spoof_reason,
            "soft_score": self.soft_spoof_score,
            "soft_reasons": self.soft_spoof_reasons
        }

    def reset(self):
        self.blink_count = 0
        self.is_blinking = False
        self.moves_completed = []
        self.yaw_offset = None
        self.last_yaw_at_blink = None
        self.video_replay_flag = False
        self.ear_samples = []
        self.ear_calibrated = False
        self.challenge_list = random.sample(["BLINK", "TURN_LEFT", "TURN_RIGHT", "BLINK_TWICE"], k=3)
        self.current_challenge_index = 0
        self.challenge_time = 0
        self.challenge_window = 4.0
        self.completed_challenges = []
        self.required_blink_count = 1
        self.challenge_stable_frames = 0
        self.last_h_ratio = None
        self.waiting_for_neutral = False
        self.spoof_detected = False
        self.prev_gray = None
        self.brightness_buffer = []
        self.nose_y_buffer = []
        self.ear_buffer = []
        self.brightness_history = []
        self.lighting_quality = "UNKNOWN"
        self.strong_spoof_detected = False
        self.strong_spoof_reason = None
        self.soft_spoof_score = 0
        self.soft_spoof_reasons = []
        self.prev_brightness = None
        self.flash_cooldown = 0
        self.flash_history = []
        self.static_depth_frames = 0
        self.low_entropy_count = 0
        self.prev_depth_delta = None
        
