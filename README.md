# Hệ Thống Định Danh Sinh Trắc Học Khuôn Mặt (Face Recognition System)

> **Đồ án môn học: Xử lý ảnh**
> **Nhóm thực hiện: Nhóm 4**

## 📚 Tài liệu hướng dẫn

Để bắt đầu với dự án, vui lòng tham khảo các tài liệu chi tiết dưới đây:

*   **🚀 [RUN.md](docs/guide/RUN.md)**: Hướng dẫn chạy ứng dụng.
*   **⚙️ [SETUP.md](docs/guide/SETUP.md)**: Hướng dẫn cài đặt môi trường và thư viện.
*   **📂 [STRUCTURE.md](docs/STRUCTURE.md)**: Giải thích cấu trúc thư mục dự án.

---

## 💡 Giới thiệu


Dự án phát triển một hệ thống điểm danh và định danh sinh trắc học dựa trên khuôn mặt, sử dụng các công nghệ hiện đại trong thị giác máy tính. Ứng dụng tập trung vào trải nghiệm người dùng với giao diện **Neon Glassmorphism** hiện đại.

### Tính năng chính

1.  **Đăng ký (Enrollment)**:
    *   Quy trình Wizard từng bước (Thông tin -> Chụp ảnh -> Hoàn tất).
    *   Hướng dẫn người dùng quay đa góc độ (Trái, Phải, Thẳng).
    *   Lưu trữ vector đặc trưng (Embedding) thay vì ảnh thô để bảo mật.

2.  **Xác thực (Authentication)**:
    *   Nhận diện khuôn mặt theo thời gian thực (Real-time).
    *   So khớp vector sinh trắc học với độ chính xác cao (sử dụng InsightFace/DeepFace).
    *   **Chống giả mạo (Anti-Spoofing)**: Phát hiện người thật qua chớp mắt (Blink Detection) và chuyển động đầu.

3.  **Giao diện người dùng (UI)**:
    *   Xây dựng bằng **PySide6**.
    *   Phong cách thiết kế tối giản, trực quan.
    *   Hỗ trợ phím tắt điều hướng nhanh.
## 🛡️ Chống giả mạo (Anti-Spoofing / Liveness Detection)

Hệ thống tích hợp module **LivenessDetector** tiên tiến sử dụng **MediaPipe Face Mesh** kết hợp nhiều kỹ thuật phân tích đa lớp để phân biệt người thật và các hình thức giả mạo (ảnh in, video replay, màn hình, mặt nạ…).

### Các phương pháp phát hiện chính

#### 1. **Challenge-Response (Active Liveness)**
   * Người dùng được yêu cầu thực hiện ngẫu nhiên 3 hành động trong danh sách:
     - Nháy mắt (Blink)
     - Nháy mắt hai lần (Blink Twice)
     - Quay đầu sang trái (Turn Left)
     - Quay đầu sang phải (Turn Right)
   * Hệ thống kiểm tra thứ tự hoàn thành trong thời gian giới hạn (2 giây/challenge).
   * Phát hiện nháy mắt hợp lệ chỉ khi có chuyển động đầu đồng thời → chống replay video.
   ```python
self.challenge_list = random.sample(
    ["BLINK", "TURN_LEFT", "TURN_RIGHT", "BLINK_TWICE"], k=3
)
instruction = f"Hãy {current_challenge
    .replace('TURN_LEFT', 'quay trái')
    .replace('TURN_RIGHT', 'quay phải')
    .replace('BLINK', 'nháy mắt')
    .replace('_TWICE', ' hai lần')}"
```

#### 2. **Phân tích độ sâu 3D (3D Depth Analysis)**
   * Sử dụng tọa độ Z từ Face Mesh để tính độ lệch giữa mũi và tai.
   * Kiểm tra độ phân tán (std) của các điểm khuôn mặt trên trục Z.
   * Phát hiện ngay lập tức nếu khuôn mặt phẳng (ảnh in, màn hình).
 ```python
    nose_z = mesh_coords[1].z
    ears_z = (mesh_coords[234].z + mesh_coords[454].z) / 2
    depth_delta = abs(nose_z - ears_z)
    z_std = np.std([p.z for p in mesh_coords])
    is_3d = (depth_delta > 0.04) and (z_std > 0.02)
```

#### 3. **Phân tích kết cấu da (Texture Analysis)**
   * Tính độ biến thiên Laplacian và Sobel trên vùng khuôn mặt.
   * Ngưỡng thích ứng theo độ sáng môi trường.
   * Phát hiện kết cấu kém (low texture) thường gặp ở ảnh in hoặc màn hình.
```python
score = cv2.Laplacian(gray, cv2.CV_64F).var()
threshold = self.get_adaptive_threshold(frame_brightness)
is_real = threshold < score < 55.0
```
#### 4. **Phát hiện nhấp nháy màn hình (Screen Flicker Detection)**
   * Phân tích FFT trên chuỗi độ sáng liên tục.
   * Phát hiện tần số đặc trưng của màn hình (50Hz, 60Hz, 100Hz, 120Hz).
```python
ft = np.abs(np.fft.rfft(signal))
for f in [50, 60, 100, 120]:
    if fft[np.argmin(np.abs(freqs - f))] > 40.0:
        self.soft_spoof_reasons.append("SCREEN_FLICKER")
```
#### 5. **Phát hiện rung tự nhiên (Natural Tremor Detection)**
   * Phân tích chuyển động vi mô của mũi (nose tip) theo thời gian.
   * Người thật luôn có rung nhẹ tần số 8-12Hz → nếu thiếu → nghi ngờ giả mạo.
```python
peak_freq = freqs[np.argmax(fft[1:]) + 1]
if not (8.0 <= peak_freq <= 12.0) and peak_amplitude > 0.5:
    self.soft_spoof_reasons.append("NO_TREMOR")
```
#### 6. **Phân tích chuyển động quang học (Optical Flow)**
   * Tính variance của optical flow giữa các frame.
   * Video replay hoặc ảnh tĩnh thường có chuyển động rất thấp.
```python
mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
if np.var(mag) < 0.1:
    self.soft_spoof_reasons.append("STATIC_FLOW")
```
#### 7. **Phát hiện sai lệch màu (Chromatic Aberration)**
   * Đo độ lệch chuẩn giữa các kênh R-G và G-B.
   * Camera thật thường có một chút aberration → ảnh chụp màn hình thường không có.
```python
diff_rg = np.std(r - g)
diff_gb = np.std(g - b)
if (diff_rg + diff_gb) > 50.0:
    self.soft_spoof_reasons.append("CHROMATIC")
```
#### 8. **Phân tích entropy thời gian (Temporal Entropy)**
   * Đo độ đa dạng của độ sáng qua nhiều frame.
   * Hình ảnh tĩnh hoặc video loop có entropy thấp.
```python
entropy = -np.sum(hist * np.log2(hist + 1e-10))
if entropy < 1.5:
    self.soft_spoof_reasons.append("LOW_ENTROPY")
```
#### 9. **Các biện pháp bổ trợ**
   * Phát hiện thay đổi sáng đột ngột (flash) để bỏ qua kiểm tra tạm thời.
   * Tự động tăng cường ảnh trong điều kiện ánh sáng yếu (CLAHE + Gamma correction).
   * Cảnh báo người dùng khi ánh sáng quá tối hoặc đang dùng flash.

### Cơ chế ra quyết định
* **Strong Spoof**: Phát hiện ngay lập tức (ví dụ: mặt phẳng, depth không thay đổi khi di chuyển) → từ chối ngay.
* **Soft Spoof**: Tích lũy điểm (mỗi dấu hiệu +1). Khi đạt ≥ 3 dấu hiệu → từ chối và hiển thị lý do bằng tiếng Việt thân thiện.

**Ví dụ thông báo khi bị từ chối (soft spoof):**
> **Phát hiện giả mạo:**  
> Kết cấu da kém, nhấp nháy màn hình, ảnh không rung tự nhiên.  
> Vui lòng dùng thiết bị thật và ánh sáng tốt.
## 🛠 Công nghệ sử dụng

*   **Ngôn ngữ**: Python
*   **Giao diện**: PySide6 (Qt)
*   **Xử lý ảnh**: OpenCV, MediaPipe
*   **Nhận diện khuôn mặt**: InsightFace / DeepFace
*   **Tính toán**: NumPy, SciPy

---

## 👥 Thành Viên Nhóm

| STT | Họ và Tên | MSSV |
|:---:|:---|:---:|
| 1 | **Nguyễn Thị Hồng Thơ** | 22151305 |
| 2 | **Nguyễn Công Đôn** | 22133013 |
| 3 | **Nguyễn Như Hoàng Tiến** | 22133061 |
