"""
Module phân tích khuôn mặt: Head Pose Estimation, Face Detection, Embedding Extraction.
Sử dụng MediaPipe cho Head Pose và InsightFace cho Embedding.
"""
import cv2
import os
import numpy as np
from enum import Enum

# Lazy imports để tránh load nặng khi khởi động
_mp_face_mesh = None
_insightface_app = None


class DistanceStatus(Enum):
    """Trạng thái khoảng cách khuôn mặt."""
    OK = "OK"
    TOO_FAR = "TOO_FAR"
    TOO_CLOSE = "TOO_CLOSE"
    NO_FACE = "NO_FACE"


class PoseType(Enum):
    """Các góc quay đầu cần capture."""
    FRONTAL = "Frontal"
    LEFT = "Left"
    RIGHT = "Right"
    UP = "Up"
    DOWN = "Down"


# Ngưỡng cho từng góc (yaw, pitch)
POSE_THRESHOLDS = {
    PoseType.FRONTAL: {"yaw": (-25, 25), "pitch": (-20, 20)}, # Rất dễ
    PoseType.LEFT: {"yaw": (10, 90), "pitch": (-20, 20)},     # Chỉ cần nghiêng nhẹ 10 độ
    PoseType.RIGHT: {"yaw": (-90, -10), "pitch": (-20, 20)},  # Chỉ cần nghiêng nhẹ 10 độ
    PoseType.UP: {"yaw": (-30, 30), "pitch": (10, 60)},
    PoseType.DOWN: {"yaw": (-30, 30), "pitch": (-60, -10)},
}

# Ngưỡng tỷ lệ diện tích khuôn mặt / khung hình
FACE_AREA_MIN_RATIO = 0.08  # Quá xa
FACE_AREA_MAX_RATIO = 0.35  # Quá gần


def _get_face_mesh():
    """Lazy load MediaPipe Face Mesh."""
    global _mp_face_mesh
    if _mp_face_mesh is None:
        import mediapipe as mp
        _mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    return _mp_face_mesh


def _get_insightface(use_gpu=True, model_name='buffalo_s'):
    """
    Lazy load InsightFace model.
    Args:
        use_gpu (bool): Có ưu tiên dùng GPU không.
        model_name (str): Tên model ('buffalo_s' cho nhẹ, 'buffalo_l' cho chính xác).
    """
    global _insightface_app
    
    if _insightface_app is not None:
        return _insightface_app

    # Hack: Thêm đường dẫn CUDA bin vào DLL sreach path (cho Windows)
    if use_gpu and os.name == 'nt':
        cuda_path = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin"
        if os.path.exists(cuda_path):
            try:
                os.add_dll_directory(cuda_path)
                print(f"Đã thêm CUDA bin vào DLL path: {cuda_path}")
            except Exception as e:
                print(f"Không thể thêm DLL path: {e}")

    from insightface.app import FaceAnalysis
    
    app = None
    
    # 1. Nếu bật GPU, thử khởi tạo với CUDA
    if use_gpu:
        try:
            print(f"Đang thử khởi tạo FaceAnalysis ({model_name}) với CUDA...")
            providers = ['CUDAExecutionProvider'] # Explicitly only try CUDA first
            app = FaceAnalysis(name=model_name, providers=providers)
            app.prepare(ctx_id=0, det_size=(640, 640))
            print("Đã khởi tạo thành công với CUDA!")
        except Exception as e:
            print(f"Lỗi khởi tạo CUDA ({e}). Sẽ chuyển sang CPU.")
            app = None

    # 2. Nếu không dùng GPU hoặc khởi tạo GPU thất bại -> Dùng CPU
    if app is None:
        try:
            print(f"Đang khởi tạo FaceAnalysis ({model_name}) với CPU...")
            providers = ['CPUExecutionProvider']
            app = FaceAnalysis(name=model_name, providers=providers)
            app.prepare(ctx_id=-1, det_size=(640, 640))
            print("Đã khởi tạo thành công với CPU!")
        except Exception as e_cpu:
            print(f"Lỗi khởi tạo InsightFace với CPU: {e_cpu}")
            raise e_cpu
            
    _insightface_app = app
    return _insightface_app


class FaceAnalyzer:
    """Phân tích khuôn mặt: detect, pose, embedding."""

    def __init__(self, use_gpu=True, model_name='buffalo_l'):
        """
        Args:
            use_gpu (bool): Bật/tắt sử dụng GPU.
            model_name (str): 'buffalo_s' (nhẹ) hoặc 'buffalo_l' (nặng).
        """
        self.face_mesh = None
        self.insightface = None
        self._last_face_box = None
        self._pose_history = []
        
        # Lưu cấu hình
        self.use_gpu = use_gpu
        self.model_name = model_name

    def _ensure_models(self):
        """Load models nếu chưa có."""
        if self.face_mesh is None:
            self.face_mesh = _get_face_mesh()
        if self.insightface is None:
            # Truyền cấu hình vào hàm get
            self.insightface = _get_insightface(self.use_gpu, self.model_name)

    def detect_face(self, frame: np.ndarray) -> tuple[bool, tuple | None]:
        """
        Phát hiện khuôn mặt và trả về bounding box.
        Returns: (has_face, (x, y, w, h) or None)
        """
        self._ensure_models()
        faces = self.insightface.get(frame)
        if faces:
            box = faces[0].bbox.astype(int)
            x, y, x2, y2 = box
            self._last_face_box = (x, y, x2 - x, y2 - y)
            return True, self._last_face_box
        self._last_face_box = None
        return False, None

    def check_face_distance(self, frame: np.ndarray, face_box: tuple = None) -> DistanceStatus:
        """
        Kiểm tra khoảng cách khuôn mặt so với khung hình.
        face_box: (x, y, w, h)
        """
        if face_box is None:
            has_face, face_box = self.detect_face(frame)
            if not has_face:
                return DistanceStatus.NO_FACE

        frame_h, frame_w = frame.shape[:2]
        frame_area = frame_h * frame_w
        _, _, w, h = face_box
        face_area = w * h
        ratio = face_area / frame_area

        if ratio < FACE_AREA_MIN_RATIO:
            return DistanceStatus.TOO_FAR
        elif ratio > FACE_AREA_MAX_RATIO:
            return DistanceStatus.TOO_CLOSE
        return DistanceStatus.OK

    def estimate_head_pose(self, frame: np.ndarray) -> tuple[float, float, float] | None:
        """
        Ước lượng góc quay đầu sử dụng MediaPipe Face Mesh.
        Returns: (yaw, pitch, roll) in degrees, or None if no face.
        """
        self._ensure_models()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        if not results.multi_face_landmarks:
            self._pose_history.clear() # Reset nếu mất mặt
            return None

        landmarks = results.multi_face_landmarks[0].landmark
        h, w = frame.shape[:2]

        # Các điểm 3D chuẩn trên khuôn mặt
        face_3d = []
        face_2d = []

        # Sử dụng các landmark chính: mũi, cằm, mắt, miệng
        key_points = [1, 33, 61, 199, 263, 291]  # Nose tip, eyes, mouth corners
        for idx in key_points:
            lm = landmarks[idx]
            x, y = int(lm.x * w), int(lm.y * h)
            face_2d.append([x, y])
            face_3d.append([x, y, lm.z * 3000])

        face_2d = np.array(face_2d, dtype=np.float64)
        face_3d = np.array(face_3d, dtype=np.float64)

        # Camera matrix
        focal_length = w
        cam_matrix = np.array([
            [focal_length, 0, w / 2],
            [0, focal_length, h / 2],
            [0, 0, 1]
        ])
        dist_coeffs = np.zeros((4, 1))

        # Solve PnP
        success, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_coeffs)
        if not success:
            return None

        # Chuyển rotation vector thành euler angles
        rmat, _ = cv2.Rodrigues(rot_vec)
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)
        
        yaw = angles[1]
        pitch = angles[0]
        roll = angles[2]
        
        # --- SMOOTHING (EMA) ---
        alpha = 0.1 # Mượt hơn nữa (giảm từ 0.3)
        if self._pose_history:
            prev_yaw, prev_pitch, prev_roll = self._pose_history[-1]
            yaw = alpha * yaw + (1 - alpha) * prev_yaw
            pitch = alpha * pitch + (1 - alpha) * prev_pitch
            roll = alpha * roll + (1 - alpha) * prev_roll
        
        self._pose_history.append((yaw, pitch, roll))
        if len(self._pose_history) > 10: # Tăng buffer history
            self._pose_history.pop(0)

        return yaw, pitch, roll

    def check_pose(self, frame: np.ndarray, target_pose: PoseType) -> tuple[bool, str]:
        """
        Kiểm tra xem góc quay đầu hiện tại có khớp với target không.
        Returns: (is_match, instruction_message)
        """
        pose = self.estimate_head_pose(frame)
        if pose is None:
            return False, "Không phát hiện khuôn mặt"

        yaw, pitch, roll = pose
        
        thresholds = POSE_THRESHOLDS[target_pose]

        yaw_ok = thresholds["yaw"][0] <= yaw <= thresholds["yaw"][1]
        pitch_ok = thresholds["pitch"][0] <= pitch <= thresholds["pitch"][1]

        # Nếu ĐÚNG rồi -> Ẩn số cho đỡ rối
        if yaw_ok and pitch_ok:
            return True, "Tuyệt vời! Giữ nguyên..."

        # Logic hướng dẫn chi tiết
        msg = ""
        debug_info = "" # Ẩn số đi cho user đỡ rối, hoặc chỉ hiện khi cần thiết

        # 1. Hướng dẫn Pitch (Lên/Xuống)
        if not pitch_ok:
            if pitch < thresholds["pitch"][0]: msg = "Ngẩng mặt lên \u2191" # Pitch âm là cúi (tùy cam, check lại) -> MediaPipe: Pitch âm là CÚI, dương là NGẨNG? 
            # Check lại: Trong code cũ Pitch < -20 là Cúi (Down). 
            # Vậy Pitch < Threshold[0] (ví dụ -20) -> Đang quá nhỏ (< -20) -> Cúi quá -> Cần Ngẩng. Đúng.
            elif pitch > thresholds["pitch"][1]: msg = "Cúi mặt xuống \u2193"
            
        # 2. Hướng dẫn Yaw (Trái/Phải)
        if not yaw_ok or msg == "":
            if target_pose == PoseType.LEFT:
                # Target: (10, 90) -> Cần Yaw dương
                if yaw > 90: 
                    msg = "Quay lại phải một chút \u2192"
                elif yaw < -5: 
                    msg = "Ngược bên rồi! Quay sang TRÁI \u2190"
                elif yaw < 10: 
                    # Đang trong khoảng -5 đến 10 (Gần được hoặc đang nhìn thẳng)
                    msg = "Xoay thêm sang TRÁI một chút \u2190"
                
            elif target_pose == PoseType.RIGHT:
                # Target: (-90, -10) -> Cần Yaw âm
                if yaw < -90: 
                    msg = "Quay lại trái một chút \u2190"
                elif yaw > 5: 
                    msg = "Ngược bên rồi! Quay sang PHẢI \u2192"
                elif yaw > -10: 
                    # Đang trong khoảng -10 đến 5
                    msg = "Xoay thêm sang PHẢI một chút \u2192"
            
            elif target_pose == PoseType.FRONTAL:
                 if abs(yaw) > 25: 
                     direction = "trái" if yaw > 0 else "phải"
                     # Nếu Yaw > 25 (đang quay trái) -> Cần quay phải để về 0
                     msg = "Quay mặt về chính diện (giữa)"

        if msg == "": 
            msg = "Điều chỉnh nhẹ..." 

        return False, f"{msg}"

    def get_embedding(self, frame: np.ndarray) -> np.ndarray | None:
        """
        Trích xuất embedding 512-d từ khuôn mặt.
        Returns: numpy array (512,) or None if no face.
        """
        self._ensure_models()
        faces = self.insightface.get(frame)
        if faces:
            return faces[0].embedding
        return None

    def get_face_crop(self, frame: np.ndarray, padding: float = 0.2) -> np.ndarray | None:
        """
        Cắt vùng khuôn mặt với padding.
        """
        has_face, box = self.detect_face(frame)
        if not has_face:
            return None

        h, w = frame.shape[:2]
        x, y, bw, bh = box
        
        # Thêm padding
        pad_x = int(bw * padding)
        pad_y = int(bh * padding)
        
        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y)
        x2 = min(w, x + bw + pad_x)
        y2 = min(h, y + bh + pad_y)
        
        return frame[y1:y2, x1:x2]
