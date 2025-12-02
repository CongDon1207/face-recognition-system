# 🎯 Face Recognition System

> **Ứng dụng xử lý ảnh trong định danh bằng sinh trắc học khuôn mặt**

## 📖 Giới thiệu

Hệ thống nhận diện khuôn mặt real-time sử dụng công nghệ sinh trắc học để xác thực danh tính người dùng. Ứng dụng phân tích các đặc điểm khuôn mặt độc nhất (khoảng cách mắt, hình dạng mũi, đường viền khuôn mặt) để tạo biometric template và xác thực người dùng.

### 🎯 Mục tiêu chính

- **Xây dựng hệ thống xác thực sinh trắc học** với 2 chế độ: Enrollment (đăng ký) & Authentication (xác thực)
- **Xác thực real-time** sử dụng pretrained deep learning models (InsightFace)
- **Chống giả mạo (Anti-spoofing)** với liveness detection (phát hiện nháy mắt, chuyển động đầu)
- **Giao diện trực quan** với UI đơn giản, dễ sử dụng bằng PySide6/OpenCV

---

## ⭐ Tính năng chính

### 📝 Chế độ Enrollment (Đăng ký)
- Nhập thông tin người dùng (ID, tên)
- Chụp ảnh khuôn mặt đa góc độ (trực diện, trái, phải)
- Phát hiện liveness trong quá trình đăng ký
- Hiển thị khung hướng dẫn vị trí khuôn mặt
- Tiền xử lý ảnh (face detection, cropping, normalization)
- Trích xuất & lưu trữ face embeddings

### 🔐 Chế độ Authentication (Xác thực)
- Camera feed real-time
- Phát hiện khuôn mặt với bounding box
- Hiển thị nhãn danh tính kèm confidence score
- Cảnh báo "UNKNOWN" cho khuôn mặt không nhận diện được
- Cảnh báo anti-spoofing ("FAKE / SPOOF DETECTED")
- So khớp dựa trên ngưỡng (Distance < Threshold = Success)

### 🛡️ Chống giả mạo (Anti-Spoofing)
- **Blink Detection**: Phát hiện nháy mắt sử dụng Eye Aspect Ratio (EAR)
- **Head Movement Detection**: Yêu cầu xoay đầu trái/phải
- Bảo vệ chống tấn công bằng ảnh/video


---

## 🛠️ Công nghệ sử dụng

| Thư viện | Mục đích |
|----------|----------|
| `opencv-python` | Xử lý camera, xử lý ảnh, video streaming |
| `pyside6` | Framework GUI (thay thế PyQt6) |
| `mediapipe` | Face detection, face landmarks, pose estimation |
| `insightface` | Deep learning face recognition (trích xuất embeddings) |
| `numpy` | Xử lý số, lưu trữ embeddings (.npy) |
| `scipy` | Tính toán khoảng cách cho face matching |

---

## 📁 Cấu trúc thư mục

```
FaceRecognitionSystem/
├── main.py                     # Entry point chính
├── requirements.txt            # Dependencies
│
├── common/                     # Tiện ích dùng chung
│   ├── camera.py               # CameraThread (QThread + OpenCV)
│   └── utils.py                # Resize ảnh, chuyển đổi Qt, vẽ frame
│
├── UI/                         # Giao diện người dùng
│   ├── base_ui.py              # Base window, layout chính, hiển thị camera
│   ├── enroll_ui.py            # Màn hình đăng ký (kế thừa base_ui)
│   └── auth_ui.py              # Màn hình xác thực (kế thừa base_ui)
│
├── modules/                    # Logic backend
│   ├── enrollment/
│   │   ├── manager.py          # Chụp ảnh, xử lý input
│   │   └── storage.py          # Lưu trữ file JSON/NPY
│   ├── auth/
│   │   └── matcher.py          # So sánh vector (Distance < Threshold)
│   └── security/
│       └── liveness.py         # Tính EAR, phát hiện head pose
│
├── data/                       # Lưu trữ dữ liệu
│   ├── database.json           # Metadata người dùng
│   └── embeddings/             # Face embedding vectors (.npy)
│
└── docs/                       # Tài liệu
    ├── Proposal.md
    ├── folder_structure.md
    └── 
```

---

## 🚀 Cài đặt & Chạy

### Yêu cầu hệ thống
- Python 3.8+
- Webcam hoạt động
- Windows/Linux/macOS

### Cài đặt

```bash
# Clone repository
git clone https://github.com/CongDon1207/face-recognition-system.git
cd face-recognition-system

# Tạo virtual environment (khuyến nghị)
python -m venv venv

# Kích hoạt virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### Chạy ứng dụng

```bash
python main.py
```

---

## 🔄 Pipeline nhận diện

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Face      │───▶│   Face      │───▶│  Feature    │───▶│  Template   │
│  Detection  │    │  Alignment  │    │ Extraction  │    │  Creation   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                │
                                                                ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Decision   │◀───│   Score     │◀───│  Matching   │◀───│  Database   │
│   Making    │    │ Calculation │    │             │    │   Lookup    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## 📄 License

Dự án này được phát hành dưới giấy phép MIT. Xem file [LICENSE](LICENSE) để biết thêm chi tiết.

---

## 👥 Đóng góp

Mọi đóng góp đều được chào đón! Vui lòng tạo Issue hoặc Pull Request nếu bạn muốn cải thiện dự án.
