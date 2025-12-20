from PySide6.QtCore import QThread, Signal
import numpy as np
import time
from modules.ai.face_analyzer import FaceAnalyzer, PoseType
from modules.authenticator import Authenticator
from modules.ai.liveness_detector import LivenessDetector


class AuthWorker(QThread):
    result_ready = Signal(dict)
    auth_result = Signal(bool, str, float)
    model_ready = Signal()
    timeout_warning = Signal(str)  # NEW: Signal để thông báo timeout
    
    def __init__(self, parent=None):
        super().__init__(parent)
      
        self.face_analyzer = None
        self.authenticator = None
        self.liveness_detector = None
        self._running = True
        self._pending_frame = None
        self._models_loaded = False
        self.last_auth_time = 0
        
        self.auth_start_time = None  
        self.timeout_threshold = 30.0  
        self.fail_count = 0  
        self.max_fails = 3  

    def process_frame(self, frame: np.ndarray):
        self._pending_frame = frame

    def run(self):
        print("[AuthWorker] Starting - Loading models...")
        
        try:
            self.face_analyzer = FaceAnalyzer()
            self.face_analyzer._ensure_models()
            self.authenticator = Authenticator()
            self.liveness_detector = LivenessDetector()
            self._models_loaded = True
            self.model_ready.emit()
        except Exception as e:
            print(f"[AuthWorker] Failed to load models: {e}")
            return
        
        while self._running:
            if self._pending_frame is not None and self._models_loaded:
                frame = self._pending_frame.copy()
                self._pending_frame = None
                
                try:
                    self._check_authentication_timeout()
                    
                    # 1. Phân tích frame
                    result = self.face_analyzer.analyze_frame(frame, PoseType.FRONTAL)
                    
                    if result["has_face"]:
                        if self.auth_start_time is None:
                            self.auth_start_time = time.time()
                            print(f"[AuthWorker] Authentication session started at {self.auth_start_time}")
                        
                        # 2. Xử lý Landmarks & Pose
                        current_landmarks = result.get("landmarks") or result.get("kps")
                        current_pose = result.get("yaw", 0)
                        if current_pose is not None:
                            print(f"[DEBUG] Pose Data detected: {current_pose}")
                        else:
                            print("[DEBUG] Pose Data is MISSING from analyzer result!")
                        
                        # 3. Gọi Liveness Detector
                        is_real, score, liveness_dict = self.liveness_detector.check_liveness(
                            frame=frame,
                            face_box=result["face_box"],
                            landmarks=current_landmarks,
                            head_pose=current_pose
                        )
                        # Khong dung dem timeout khi pass liveness, nhung van giu auth_start_time de hien thi timer
                        # 4. Cập nhật kết quả tổng hợp
                        result.update({
                            "is_real": is_real,
                            "liveness_score": score,
                            "liveness_status": liveness_dict["status"],
                            "pose_instruction": liveness_dict["instruction"],
                            "moves_completed": liveness_dict.get("moves_completed", []),
                            "completed_challenges": liveness_dict.get("completed_challenges", []),
                            "fail_count": self.fail_count,  # NEW: Thêm fail_count vào result
                            "time_elapsed": time.time() - self.auth_start_time if self.auth_start_time else 0  # NEW
                        })

                        self.last_face_time = time.time()
                    else: 
                        if time.time() - getattr(self, 'last_face_time', 0) > 1.5:
                            self.liveness_detector.reset()
                            # NEW: Reset timeout khi không có mặt lâu
                            if self.auth_start_time and time.time() - self.auth_start_time > 3.0:
                                print("[AuthWorker] No face for too long, resetting session")
                                self.auth_start_time = None
                    
                    self.result_ready.emit(result)
                    
                except Exception as e:
                    print(f"[AuthWorker] Error processing frame: {e}")
            
            self.msleep(20)

    def _check_authentication_timeout(self):
        """NEW: Kiểm tra timeout trong quá trình xác thực"""
        if self.auth_start_time is None:
            return
        
        elapsed = time.time() - self.auth_start_time
        
        # Nếu quá thời gian timeout
        if elapsed > self.timeout_threshold:
            print(f"[AuthWorker] TIMEOUT! Elapsed: {elapsed:.1f}s > {self.timeout_threshold}s")
            
            # Tăng fail count
            self.fail_count += 1
            print(f"[AuthWorker] Fail count increased to: {self.fail_count}/{self.max_fails}")
            
            # Emit warning
            if self.fail_count >= self.max_fails:
                self.timeout_warning.emit(f"ĐÃ THẤT BẠI {self.fail_count} LẦN - Vui lòng thử lại sau")
            else:
                remaining = self.max_fails - self.fail_count
                self.timeout_warning.emit(f"TIMEOUT! Còn {remaining} lần thử")
            
            # Reset liveness detector và session
            self.liveness_detector.reset()
            self.auth_start_time = None
            
            print("[AuthWorker] Session reset due to timeout")

    def authenticate(self, embedding: np.ndarray):
        if embedding is not None:
            success, user_id, distance = self.authenticator.authenticate(embedding)
            
            # NEW: Nếu xác thực thành công, reset fail_count
            if success:
                print("[AuthWorker] Authentication SUCCESS - Resetting fail count")
                self.fail_count = 0
                self.auth_start_time = None  # Reset session
            
            self.auth_result.emit(success, user_id, distance)

    def reset_session(self):
        """NEW: Public method để reset session từ bên ngoài"""
        print("[AuthWorker] Manual session reset")
        self.auth_start_time = None
        self.liveness_detector.reset()

    def reset_fail_count(self):
        """NEW: Reset fail counter (dùng khi admin can thiệp hoặc sau cooldown period)"""
        print(f"[AuthWorker] Resetting fail count from {self.fail_count} to 0")
        self.fail_count = 0

    def stop(self):
        self._running = False
        self.wait()
        print("[AuthWorker] Stopped")
