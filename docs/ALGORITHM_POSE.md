# Nguyên lý Thuật toán Nhận diện Góc quay (Geometric Ratio)

Tài liệu này mô tả chi tiết thuật toán xác định hướng quay đầu (Trái/Phải/Lên/Xuống) dựa trên **Tỷ lệ Hình học (Geometric Ratio)** thay vì tính toán góc quay 3D (Euler Angles).

## 1. Giới thiệu
Phương pháp truyền thống (PnP - Perspective-n-Point) tính toán góc Yaw/Pitch/Roll 3D thường gặp vấn đề:
- **Không ổn định**: Giá trị góc bị nhảy (jitter) khi mặt di chuyển nhẹ.
- **Phụ thuộc Camera**: Cần tham số nội tại (intrinsic parameters) chính xác của camera để tính đúng.
- **Khó căn chỉnh**: Người dùng khó hình dung "quay 30 độ" là bao nhiêu.

**Phương pháp Tỷ lệ Hình học** giải quyết vấn đề bằng cách đo tỷ lệ khoảng cách tương đối giữa các điểm mốc trên khuôn mặt. Phương pháp này trực quan ("Mũi lệch về phía nào?") và ổn định hơn.

## 2. Horizontal Ratio (Xoay Trái / Phải)
Xác định việc quay đầu sang hai bên dựa trên vị trí tương đối của **Mũi** so với hai **Gò má/Tai**.

### Điểm mốc (MediaPipe Landmarks)
- **Nose Tip (Mũi)**: Index `1`.
- **Left Face (Mép trái)**: Index `454`.
- **Right Face (Mép phải)**: Index `234`.

### Công thức
$$d_{Left} = |x_{Nose} - x_{LeftFace}|$$
$$d_{Right} = |x_{Nose} - x_{RightFace}|$$
$$Ratio_{H} = \frac{d_{Left}}{d_{Right}}$$

### Ngưỡng (Thresholds)
- **Nhìn thẳng (Frontal)**: $0.5 \le Ratio_{H} \le 2.0$ (Mũi nằm giữa).
- **Quay Trái (Turn Left)**: $Ratio_{H} > 2.8$ (Mũi tiến sát mép phải ảnh - do ảnh mirrored hoặc cam ngược).
- **Quay Phải (Turn Right)**: $Ratio_{H} < 0.35$ (Mũi tiến sát mép trái ảnh).

## 3. Vertical Ratio (Ngẩng Lên / Cúi Xuống)
Xác định việc ngẩng hoặc cúi đầu dựa trên vị trí tương đối của **Mũi** trên trục dọc.

### Điểm mốc
- **Mid-Eye (Giữa 2 mắt)**: Index `168`.
- **Nose Tip (Mũi)**: Index `1`.
- **Chin (Cằm)**: Index `152`.

### Công thức
$$d_{Top} = |y_{MidEye} - y_{Nose}|$$
$$d_{Bottom} = |y_{Nose} - y_{Chin}|$$
$$Ratio_{V} = \frac{d_{Top}}{d_{Bottom}}$$

### Ngưỡng (Thresholds)
- **Nhìn thẳng (Frontal)**: $0.25 \le Ratio_{V} \le 0.65$.
- **Ngẩng lên (Up)**: $Ratio_{V} < 0.25$ (Mũi "cao" lên gần mắt, khoảng cách mũi-cằm dài ra).
- **Cúi xuống (Down)**: $Ratio_{V} > 0.65$ (Mũi "thấp" xuống gần cằm, khoảng cách trán-mũi dài ra).

## 4. Tóm tắt Giá trị
| Tư thế (Pose) | Chỉ số quan trọng | Điều kiện |
| :--- | :--- | :--- |
| **Frontal** | H-Ratio, V-Ratio | $H \in [0.5, 2.0]$ VÀ $V \in [0.25, 0.65]$ |
| **Left** | H-Ratio | $H < 0.35$ (V-Ratio lax: $0.15-0.8$) |
| **Right** | H-Ratio | $H > 2.8$ (V-Ratio lax: $0.15-0.8$) |
| **Up** | V-Ratio | $V < 0.25$ |
| **Down** | V-Ratio | $V > 0.65$ |
