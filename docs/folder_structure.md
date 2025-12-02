FaceRecognitionSystem/
│
├─ main.py                     # [USER 1] File chạy chính
├─ requirements.txt            # [Team] Danh sách thư viện (opencv, pyqt6, insightface…)
│
├─ common/                     # [USER 1] Các công cụ nền tảng
│  ├─ __init__.py
│  ├─ camera.py                # Class CameraThread (QThread + OpenCV)
│  └─ utils.py                 # Hàm resize ảnh, convert ảnh sang Qt, vẽ khung
│
├─ UI/                         # [CHIA NHAU] Code giao diện
│  ├─ __init__.py
│  ├─ base_ui.py               # [USER 1] Cửa sổ cha, Layout chính, Hiển thị Camera
│  ├─ enroll_ui.py             # [USER 2] Màn hình đăng ký (kế thừa base_ui)
│  └─ auth_ui.py               # [USER 3] Màn hình xác thực (kế thừa base_ui)
│
├─ modules/                    # [CHIA NHAU] Xử lý logic (Backend)
│  ├─ enrollment/              # [USER 2]
│  │  ├─ __init__.py
│  │  ├─ manager.py            # Logic chụp ảnh, xử lý ảnh đầu vào
│  │  └─ storage.py            # Logic lưu file .json, .npy
│  │
│  ├─ auth/                    # [USER 3]
│  │  ├─ __init__.py
│  │  └─ matcher.py            # Logic so sánh vector (Distance < Threshold)
│  │
│  └─ security/                # [USER 3]
│     ├─ __init__.py
│     └─ liveness.py           # Logic tính EAR (mắt), Head Pose (đầu)
│
├─ data/                       # [USER 2] Quản lý cấu trúc folder này
│  ├─ database.json
│  └─ embeddings/
