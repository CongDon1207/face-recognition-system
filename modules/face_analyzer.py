"""
Phân tích khuôn mặt: phát hiện, ước lượng head pose và trích xuất embedding.
Sử dụng MediaPipe cho head pose và InsightFace cho embedding.
"""

import os
from enum import Enum

import cv2
import numpy as np

_mp_face_mesh = None
_insightface_app = None


class DistanceStatus(Enum):
    """Trạng thái khoảng cách khuôn mặt so với khung hình."""

    OK = "OK"
    TOO_FAR = "TOO_FAR"
    TOO_CLOSE = "TOO_CLOSE"
    NO_FACE = "NO_FACE"


class PoseType(Enum):
    """Các góc quay đầu cần chụp."""

    FRONTAL = "Frontal"
    LEFT = "Left"
    RIGHT = "Right"
    UP = "Up"
    DOWN = "Down"


# --- Thresholds (Geometric Ratio) ---
RATIO_THRESHOLDS = {
    "frontal": {"h_min": 0.5, "h_max": 2.0, "v_min": 0.25, "v_max": 0.65},
    "left": {"h_min": 2.8, "v_lax_min": 0.15, "v_lax_max": 0.8},
    "right": {"h_max": 0.35, "v_lax_min": 0.15, "v_lax_max": 0.8},
    "up": {"v_max": 0.25},
    "down": {"v_min": 0.65}
}

# Nới lỏng một chút để người dùng không phải đưa mặt quá gần/xa.
FACE_AREA_MIN_RATIO = 0.06
FACE_AREA_MAX_RATIO = 0.55  # Tăng từ 0.45 lên 0.55 để cho phép mặt gần hơn

# Số frame phải giữ ổn định để xác nhận pose (15 frames @ 30fps = 0.5s)
STABLE_FRAMES_REQUIRED = 15


def _get_face_mesh():
    """Lazy load MediaPipe FaceMesh."""
    global _mp_face_mesh
    if _mp_face_mesh is None:
        import mediapipe as mp

        _mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
    return _mp_face_mesh




class FaceAnalyzer:
    """Phân tích khuôn mặt: detect, head pose, embedding."""

    def __init__(self, use_gpu: bool = True, model_name: str = "buffalo_s"): 
        self.face_mesh = None
        self.insightface = None
        self._last_face_box = None
        
        # Internal state
        self._last_pose_ok = False
        self._last_instruction = ""
        self._stable_frames = 0
        
        self.use_gpu = use_gpu
        self.model_name = model_name

    def _ensure_models(self) -> None:
        if self.face_mesh is None:
            self.face_mesh = _get_face_mesh()
        if self.insightface is None:
            self.insightface = _get_insightface(self.use_gpu, self.model_name)

    def analyze_frame(self, frame: np.ndarray, target_pose: PoseType) -> dict:
        """
        Phân tích toàn diện frame 1 lần duy nhất.
        Trả về dict: {
            "has_face": bool,
            "distance_status": DistanceStatus,
            "face_box": tuple | None,
            "pose_ok": bool,
            "pose_instruction": str,
            "yaw": float | None,
            "embedding": np.ndarray | None,
            "face_crop": np.ndarray | None
        }
        """
        self._ensure_models()
        
        # 1. InsightFace Detection & Embedding (Heavy op - run once)
        faces = self.insightface.get(frame)
        if not faces:
            # Reset pose tracking if lost face
            self._stable_frames = 0
            self._pose_history.clear()
            return {
                "has_face": False,
                "distance_status": DistanceStatus.NO_FACE,
                "face_box": None,
                "pose_ok": False,
                "pose_instruction": "Không tìm thấy khuôn mặt",
                "yaw": None,
                "embedding": None,
                "face_crop": None
            }

        # Take largest face (assuming single user)
        # InsightFace sorts by det score, but let's just take the first one usually
        face = faces[0]
        x1, y1, x2, y2 = face.bbox.astype(int)
        face_box = (x1, y1, x2 - x1, y2 - y1)
        embedding = face.embedding

        # 2. Check Distance
        frame_h, frame_w = frame.shape[:2]
        w, h = face_box[2], face_box[3]
        ratio = (w * h) / float(frame_h * frame_w) if frame_h and frame_w else 0.0

        if ratio < FACE_AREA_MIN_RATIO:
            dist_status = DistanceStatus.TOO_FAR
        elif ratio > FACE_AREA_MAX_RATIO:
            dist_status = DistanceStatus.TOO_CLOSE
        else:
            dist_status = DistanceStatus.OK

        # 3. Check Pose (only if distance is OK)
        pose_ok = False
        instruction = ""
        yaw = None
        
        if dist_status == DistanceStatus.OK:
            pose_ok, instruction, yaw = self._check_pose_logic(frame, target_pose)
        else:
            # Nếu distance fail, reset pose stability
            self._stable_frames = 0
            if dist_status == DistanceStatus.TOO_FAR:
                instruction = "Lại gần hơn!"
            elif dist_status == DistanceStatus.TOO_CLOSE:
                instruction = "Lùi xa hơn!"
        
        # 4. Prepare result
        return {
            "has_face": True,
            "distance_status": dist_status,
            "face_box": face_box,
            "pose_ok": pose_ok,
            "pose_instruction": instruction,
            "yaw": yaw,
            "embedding": embedding,
            # Chỉ crop khi cần save để tiết kiệm, hoặc trả về luôn nếu UI cần preview crop
            "face_crop": None 
        }



    # ---------------------------- Geometric Ratio --------------------------- #
    def calculate_pose_ratio(self, landmarks, width: int, height: int) -> tuple[float | None, float | None]:
        """
        Tính tỷ lệ hình học:
        - H-Ratio (Ngang) = d_left / d_right
        - V-Ratio (Dọc)   = d_top / d_bottom
          + d_top = |y_mid_eye - y_nose|
          + d_bottom = |y_nose - y_chin|
        """
        try:
            # MediaPipe indices
            NOSE_TIP = 1
            LEFT_FACE = 454
            RIGHT_FACE = 234
            MID_EYE = 168
            CHIN = 152

            nose = landmarks[NOSE_TIP]
            left = landmarks[LEFT_FACE]
            right = landmarks[RIGHT_FACE]
            mid_eye = landmarks[MID_EYE]
            chin = landmarks[CHIN]

            # Horizontal Layout
            x_nose = nose.x * width
            x_left = left.x * width
            x_right = right.x * width
            
            d_left = abs(x_nose - x_left)
            d_right = abs(x_nose - x_right)
            h_ratio = d_left / d_right if d_right != 0 else 999.0

            # Vertical Layout
            y_nose = nose.y * height
            y_mid_eye = mid_eye.y * height
            y_chin = chin.y * height
            
            d_top = abs(y_mid_eye - y_nose)
            d_bottom = abs(y_nose - y_chin)
            v_ratio = d_top / d_bottom if d_bottom != 0 else 999.0

            return h_ratio, v_ratio
        except Exception:
            return None, None

    def _check_pose_logic(self, frame: np.ndarray, target_pose: PoseType) -> tuple[bool, str, float | None]:
        """Logic kiểm tra pose dùng Geometric Ratio toàn diện."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)
        
        if not results.multi_face_landmarks:
            self._stable_frames = 0
            return False, "Không phát hiện được khuôn mặt (MP)", None
            
        landmarks = results.multi_face_landmarks[0].landmark
        h, w = frame.shape[:2]
        
        h_ratio, v_ratio = self.calculate_pose_ratio(landmarks, w, h)
        if h_ratio is None or v_ratio is None:
             return False, "Lỗi tính toán tỷ lệ khuôn mặt", None

        hysteresis = 0.05 if self._last_pose_ok else 0.0
        pose_ok = False
        msg = ""
        debug_value = 0.0

        # --- Logic Checks ---
        if target_pose == PoseType.FRONTAL:
            debug_value = h_ratio
            cfg = RATIO_THRESHOLDS["frontal"]
            h_ok = (cfg["h_min"] - hysteresis) <= h_ratio <= (cfg["h_max"] + hysteresis)
            v_ok = (cfg["v_min"] - hysteresis) <= v_ratio <= (cfg["v_max"] + hysteresis)
            
            if h_ok and v_ok:
                pose_ok = True
            else:
                if not h_ok:
                    msg = "Quay mặt về giữa (lệch TRÁI)" if h_ratio < cfg["h_min"] else "Quay mặt về giữa (lệch PHẢI)"
                elif not v_ok:
                    msg = "Hạ cằm xuống (Ngẩng)" if v_ratio < cfg["v_min"] else "Ngẩng đầu lên (Cúi)"

        elif target_pose == PoseType.LEFT:
            debug_value = h_ratio
            cfg = RATIO_THRESHOLDS["left"]
            if h_ratio > (cfg["h_min"] - hysteresis):
                # Check V-Ratio lax
                if cfg["v_lax_min"] <= v_ratio <= cfg["v_lax_max"]:
                    pose_ok = True
                else: 
                    msg = "Giữ độ cao đầu bình thường."
            else:
                msg = "Xoay TRÁI thêm chút nữa."
                
        elif target_pose == PoseType.RIGHT:
            debug_value = h_ratio
            cfg = RATIO_THRESHOLDS["right"]
            if h_ratio < (cfg["h_max"] + hysteresis):
                 if cfg["v_lax_min"] <= v_ratio <= cfg["v_lax_max"]:
                    pose_ok = True
                 else:
                    msg = "Giữ độ cao đầu bình thường."
            else:
                msg = "Xoay PHẢI thêm chút nữa."

        elif target_pose == PoseType.UP:
             debug_value = v_ratio
             cfg = RATIO_THRESHOLDS["up"]
             if v_ratio < (cfg["v_max"] + hysteresis):
                 pose_ok = True
             else:
                 msg = "Ngẩng đầu lên cao hơn."
                 
        elif target_pose == PoseType.DOWN:
             debug_value = v_ratio
             cfg = RATIO_THRESHOLDS["down"]
             if v_ratio > (cfg["v_min"] - hysteresis):
                 pose_ok = True
             else:
                 msg = "Cúi đầu xuống thấp hơn."
                 
        # --- Stability ---
        if pose_ok:
            self._last_pose_ok = True
            self._stable_frames += 1
            return True, "Tuyệt vời! Giữ nguyên.", debug_value
        
        if self._last_pose_ok:
            self._stable_frames += 1
            if self._stable_frames < 6:
                return True, "Giữ nguyên.", debug_value
            self._last_pose_ok = False
            self._stable_frames = 0
            
        if not msg: msg = "Điều chỉnh góc mặt."
        
        if self._last_instruction and msg != self._last_instruction:
            self._stable_frames += 1
            if self._stable_frames < 8:
                return False, self._last_instruction, debug_value
            self._stable_frames = 0
            
        self._last_instruction = msg
        return False, msg, debug_value


    def reset_pose_state(self) -> None:
        self._last_pose_ok = False
        self._stable_frames = 0
        self._last_instruction = ""



_current_config = {}

def _get_insightface(use_gpu: bool = False, model_name: str = "buffalo_s"):
    """Lazy load InsightFace FaceAnalysis với khả năng chuyển đổi CPU/GPU."""
    global _insightface_app, _current_config
    
    # Check if config changed
    new_config = {"use_gpu": use_gpu, "model_name": model_name}
    if _insightface_app is not None and _current_config == new_config:
        return _insightface_app

    # Reset if config changed or not init
    _insightface_app = None

    if use_gpu and os.name == "nt":
        cuda_path = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin"
        if os.path.exists(cuda_path):
            try:
                os.add_dll_directory(cuda_path)
            except Exception:  # pragma: no cover
                pass

    from insightface.app import FaceAnalysis

    app = None
    if use_gpu:
        try:
            print(f"Khởi tạo InsightFace ({model_name}) với CUDA...")
            app = FaceAnalysis(name=model_name, providers=["CUDAExecutionProvider"])
            app.prepare(ctx_id=0, det_size=(640, 640))
            print("Khởi tạo InsightFace với CUDA thành công.")
        except Exception as exc:  # pragma: no cover
            print(f"Lỗi CUDA ({exc}), chuyển sang CPU.")
            app = None

    if app is None:
        try:
            print(f"Khởi tạo InsightFace ({model_name}) với CPU...")
            app = FaceAnalysis(name=model_name, providers=["CPUExecutionProvider"])
            app.prepare(ctx_id=-1, det_size=(640, 640))
            print("Khởi tạo InsightFace với CPU thành công.")
        except Exception as exc:  # pragma: no cover
            print(f"Lỗi InsightFace CPU: {exc}")
            raise

    _insightface_app = app
    _current_config = new_config
    return _insightface_app
