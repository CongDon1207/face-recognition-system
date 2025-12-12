"""
Pose logic tách riêng khỏi FaceAnalyzer.
Chứa hàm tính ratio hình học và kiểm tra pose + ổn định.
"""

import cv2
import numpy as np


# --- Thresholds (Geometric Ratio) ---
RATIO_THRESHOLDS = {
    "frontal": {"h_min": 0.5, "h_max": 2.0, "v_min": 0.25, "v_max": 0.65},
    "left": {"h_min": 2.8, "v_lax_min": 0.15, "v_lax_max": 0.8},
    "right": {"h_max": 0.35, "v_lax_min": 0.15, "v_lax_max": 0.8},
    "up": {"v_max": 0.25},
    "down": {"v_min": 0.65},
}


def calculate_pose_ratio(landmarks, width: int, height: int) -> tuple[float | None, float | None]:
    """
    Tính tỉ lệ hình học:
    - H-Ratio (Ngang) = d_left / d_right
    - V-Ratio (Dọc)   = d_top / d_bottom
    """
    try:
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

        x_nose = nose.x * width
        x_left = left.x * width
        x_right = right.x * width

        d_left = abs(x_nose - x_left)
        d_right = abs(x_nose - x_right)
        h_ratio = d_left / d_right if d_right != 0 else 999.0

        y_nose = nose.y * height
        y_mid_eye = mid_eye.y * height
        y_chin = chin.y * height

        d_top = abs(y_mid_eye - y_nose)
        d_bottom = abs(y_nose - y_chin)
        v_ratio = d_top / d_bottom if d_bottom != 0 else 999.0

        return h_ratio, v_ratio
    except Exception:
        return None, None


def check_pose_logic(
    frame: np.ndarray,
    face_mesh,
    target_pose,
    PoseTypeEnum,
    last_pose_ok: bool,
    last_instruction: str,
    stable_frames: int,
) -> tuple[bool, str, float | None, bool, str, int]:
    """
    Kiểm tra pose theo geometric ratio + ổn định.
    Trả về:
    (pose_ok, msg, debug_value, new_last_pose_ok, new_last_instruction, new_stable_frames)
    """
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if not results.multi_face_landmarks:
        return False, "Không phát hiện được khuôn mặt (MP)", None, False, "", 0

    landmarks = results.multi_face_landmarks[0].landmark
    h, w = frame.shape[:2]

    h_ratio, v_ratio = calculate_pose_ratio(landmarks, w, h)
    if h_ratio is None or v_ratio is None:
        return False, "Lỗi tính toán tỉ lệ khuôn mặt", None, last_pose_ok, last_instruction, stable_frames

    hysteresis = 0.05 if last_pose_ok else 0.0
    pose_ok = False
    msg = ""
    debug_value = 0.0

    if target_pose == PoseTypeEnum.FRONTAL:
        debug_value = h_ratio
        cfg = RATIO_THRESHOLDS["frontal"]
        h_ok = (cfg["h_min"] - hysteresis) <= h_ratio <= (cfg["h_max"] + hysteresis)
        v_ok = (cfg["v_min"] - hysteresis) <= v_ratio <= (cfg["v_max"] + hysteresis)
        if h_ok and v_ok:
            pose_ok = True
        else:
            if not h_ok:
                msg = "Quay mặt về giữa (lệch trái)" if h_ratio < cfg["h_min"] else "Quay mặt về giữa (lệch phải)"
            elif not v_ok:
                msg = "Hạ cằm xuống (ngẩng)" if v_ratio < cfg["v_min"] else "Ngẩng đầu lên (cúi)"

    elif target_pose == PoseTypeEnum.LEFT:
        debug_value = h_ratio
        cfg = RATIO_THRESHOLDS["left"]
        if h_ratio > (cfg["h_min"] - hysteresis):
            if cfg["v_lax_min"] <= v_ratio <= cfg["v_lax_max"]:
                pose_ok = True
            else:
                msg = "Giữ độ cao đầu bình thường."
        else:
            msg = "Xoay trái thêm chút nữa."

    elif target_pose == PoseTypeEnum.RIGHT:
        debug_value = h_ratio
        cfg = RATIO_THRESHOLDS["right"]
        if h_ratio < (cfg["h_max"] + hysteresis):
            if cfg["v_lax_min"] <= v_ratio <= cfg["v_lax_max"]:
                pose_ok = True
            else:
                msg = "Giữ độ cao đầu bình thường."
        else:
            msg = "Xoay phải thêm chút nữa."

    elif target_pose == PoseTypeEnum.UP:
        debug_value = v_ratio
        cfg = RATIO_THRESHOLDS["up"]
        if v_ratio < (cfg["v_max"] + hysteresis):
            pose_ok = True
        else:
            msg = "Ngẩng đầu lên cao hơn."

    elif target_pose == PoseTypeEnum.DOWN:
        debug_value = v_ratio
        cfg = RATIO_THRESHOLDS["down"]
        if v_ratio > (cfg["v_min"] - hysteresis):
            pose_ok = True
        else:
            msg = "Cúi đầu xuống thấp hơn."

    # --- Stability giống logic cũ ---
    if pose_ok:
        stable_frames += 1
        return True, "Tuyệt vời! Giữ nguyên.", debug_value, True, last_instruction, stable_frames

    if last_pose_ok:
        stable_frames += 1
        if stable_frames < 6:
            return True, "Giữ nguyên.", debug_value, True, last_instruction, stable_frames
        last_pose_ok = False
        stable_frames = 0

    if not msg:
        msg = "Điều chỉnh góc mặt."

    if last_instruction and msg != last_instruction:
        stable_frames += 1
        if stable_frames < 8:
            return False, last_instruction, debug_value, last_pose_ok, last_instruction, stable_frames
        stable_frames = 0

    last_instruction = msg
    return False, msg, debug_value, last_pose_ok, last_instruction, stable_frames

