"""
Phân tích khuôn mặt: phát hiện, kiểm tra khoảng cách, kiểm tra head pose và trích xuất embedding.
Pose-logic đã được tách sang modules/pose_logic.py.
"""

import os
from enum import Enum
import numpy as np
from modules.ai.pose_logic import check_pose_logic

_mp_face_mesh = None
_insightface_app = None
_current_config: dict = {}


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


# Ngưỡng khoảng cách theo diện tích bbox / diện tích khung hình
FACE_AREA_MIN_RATIO = 0.3
FACE_AREA_MAX_RATIO = 0.55

# Siết khoảng cách tối thiểu riêng cho từng pose (FRONTAL cần gần hơn)
FACE_AREA_MIN_RATIO_BY_POSE = {
    PoseType.FRONTAL: 0.3,
    PoseType.LEFT: 0.2,
    PoseType.RIGHT: 0.2,
    PoseType.UP: 0.2,
    PoseType.DOWN: 0.2,
}


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
    """Phân tích khuôn mặt: detect, pose, embedding."""

    def __init__(self, use_gpu: bool = False, model_name: str = "buffalo_l"):
        self.face_mesh = None
        self.insightface = None
        self._last_face_box = None

        # State cho pose stability
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
        Phân tích 1 frame duy nhất.
        Trả về dict:
        {
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

        faces = self.insightface.get(frame)
        if not faces:
            self.reset_pose_state()
            return {
                "has_face": False,
                "distance_status": DistanceStatus.NO_FACE,
                "face_box": None,
                "pose_ok": False,
                "pose_instruction": "Không tìm thấy khuôn mặt",
                "yaw": None,
                "embedding": None,
                "face_crop": None,
            }

        face = faces[0]
        x1, y1, x2, y2 = face.bbox.astype(int)
        face_box = (x1, y1, x2 - x1, y2 - y1)
        embedding = face.embedding

        frame_h, frame_w = frame.shape[:2]
        w, h = face_box[2], face_box[3]
        ratio = (w * h) / float(frame_h * frame_w) if frame_h and frame_w else 0.0

        min_ratio = FACE_AREA_MIN_RATIO_BY_POSE.get(target_pose, FACE_AREA_MIN_RATIO)
        if ratio < min_ratio:
            dist_status = DistanceStatus.TOO_FAR
        elif ratio > FACE_AREA_MAX_RATIO:
            dist_status = DistanceStatus.TOO_CLOSE
        else:
            dist_status = DistanceStatus.OK

        pose_ok = False
        instruction = ""
        yaw = None

        if dist_status == DistanceStatus.OK:
            pose_ok, instruction, yaw = self._check_pose_logic(frame, target_pose)
        else:
            self._stable_frames = 0
            if dist_status == DistanceStatus.TOO_FAR:
                instruction = "Lại gần hơn!"
            elif dist_status == DistanceStatus.TOO_CLOSE:
                instruction = "Lùi xa hơn!"
        
        return {
            "has_face": True,
            "distance_status": dist_status,
            "face_box": face_box,
            "pose_ok": pose_ok,
            "pose_instruction": instruction,
            "yaw": yaw,
            "embedding": embedding,
            "face_crop": None
        }

    def _check_pose_logic(self, frame: np.ndarray, target_pose: PoseType) -> tuple[bool, str, float | None]:
        (
            pose_ok,
            msg,
            debug_value,
            new_last_pose_ok,
            new_last_instruction,
            new_stable_frames,
        ) = check_pose_logic(
            frame=frame,
            face_mesh=self.face_mesh,
            target_pose=target_pose,
            PoseTypeEnum=PoseType,
            last_pose_ok=self._last_pose_ok,
            last_instruction=self._last_instruction,
            stable_frames=self._stable_frames,
        )
        self._last_pose_ok = new_last_pose_ok
        self._last_instruction = new_last_instruction
        self._stable_frames = new_stable_frames
        return pose_ok, msg, debug_value

    def reset_pose_state(self) -> None:
        self._last_pose_ok = False
        self._stable_frames = 0
        self._last_instruction = ""


def _get_insightface(use_gpu: bool = False, model_name: str = "buffalo_s"):
    """Lazy load InsightFace FaceAnalysis với khả năng chuyển đổi CPU/GPU."""
    global _insightface_app, _current_config

    new_config = {"use_gpu": use_gpu, "model_name": model_name}
    if _insightface_app is not None and _current_config == new_config:
        return _insightface_app

    _insightface_app = None

    if use_gpu and os.name == "nt":
        cuda_path = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin"
        if os.path.exists(cuda_path):
            try:
                os.add_dll_directory(cuda_path)
            except Exception:
                pass

    from insightface.app import FaceAnalysis

    app = None
    if use_gpu:
        try:
            print(f"Khởi tạo InsightFace ({model_name}) với CUDA...")
            app = FaceAnalysis(name=model_name, providers=["CUDAExecutionProvider"])
            app.prepare(ctx_id=0, det_size=(640, 640))
            print("Khởi tạo InsightFace với CUDA thành công.")
        except Exception as exc:
            print(f"Lỗi CUDA ({exc}), chuyển sang CPU.")
            app = None

    if app is None:
        try:
            print(f"Khởi tạo InsightFace ({model_name}) với CPU...")
            app = FaceAnalysis(name=model_name, providers=["CPUExecutionProvider"])
            app.prepare(ctx_id=-1, det_size=(640, 640))
            print("Khởi tạo InsightFace với CPU thành công.")
        except Exception as exc:
            print(f"Lỗi InsightFace CPU: {exc}")
            raise

    _insightface_app = app
    _current_config = new_config
    return _insightface_app

