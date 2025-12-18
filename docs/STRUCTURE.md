# Cấu trúc thư mục (Project Structure)

## 📂 Tổng quan

```
FaceRecognitionSystem/
├── 📄 main.py                      # Entry point - khởi chạy ứng dụng
├── 📄 requirements.txt             # Danh sách dependencies
├── 📄 README.md                    # Tài liệu tổng quan dự án
├── 📄 CHANGELOG.md                 # Lịch sử thay đổi
├── 📄 HANDOFF.md                   # Trạng thái hiện tại & TODO
├── 📄 AGENTS.md                    # Quy tắc code cho AI agents
│
├── 📁 UI/                          # Giao diện người dùng (PySide6)
│   ├── __init__.py
│   ├── base_ui.py                  # MainWindow - cửa sổ chính
│   ├── styles.py                   # Theme Neon Glassmorphism
│   │
│   ├── 📁 components/              # UI components tái sử dụng
│   │   └── sidebar.py              # Thanh điều hướng bên trái
│   ├── authentication/         # Module xác thực khuôn mặt
│   │   └── auth_ui.py          # Giao diện Authentication (Camera + Liveness)
│   ├── 📁 enrollment/              # Module đăng ký khuôn mặt
│   │   ├── enroll_ui.py            # Manager 3-step wizard
│   │   └── 📁 steps/
│   │       ├── profile_step.py     # Bước 1: Nhập thông tin (MSSV, Tên)
│   │       ├── 📁 capture_step/    # Bước 2: Module chụp 5 góc
│   │       │   ├── capture_step.py           # UI logic chính
│   │       │   ├── capture_ui.py             # UI components riêng
│   │       │   └── face_processing_thread.py # AI thread xử lý pose/distance
│   │       └── success_step.py     # Bước 3: Thông báo hoàn tất
│   │
│   └── 📁 assets/                  # Tài nguyên (icon, hình ảnh)
│
├── 📁 modules/                     # Business logic & AI
│   ├── database.py                 # DatabaseManager - SQLite (users, embeddings)
│   ├── face_analyzer.py            # FaceAnalyzer - detect, distance, pose, embedding
│   ├── authenticator.py            # Authenticator - So khớp embedding, xác thực user
│   └── pose_logic.py               # Geometric ratio logic cho head pose
│
├── 📁 common/                      # Utilities dùng chung
│   └── camera.py                   # CameraThread - đọc webcam qua QThread
│
├── 📁 data/                        # Dữ liệu runtime
│   ├── faces.db                    # SQLite database
│   ├── 📁 faces/                   # Thư mục lưu ảnh enroll (theo user_id)
│   │   ├── 1/
│   │   ├── 3/
│   │   └── ...
│   └── 📁 models/                  # Pretrained models (InsightFace)
│       ├── 📁 buffalo_s/           # Model nhẹ (default)
│       └── 📁 buffalo_l/           # Model lớn (optional)
│
├── 📁 docs/                        # Tài liệu dự án
│   ├── STRUCTURE.md                # File này
│   ├── ALGORITHM_POSE.md           # Giải thích thuật toán head pose
│   ├── implementation_plan.md      # Kế hoạch triển khai
│   ├── Proposal.md                 # Đề xuất đồ án
│   └── 📁 guide/
│       ├── RUN.md                  # Hướng dẫn chạy ứng dụng
│       └── SETUP.md                # Hướng dẫn cài đặt môi trường
│
└── 📁 venv/                        # Môi trường ảo Python (git ignored)
```

## 🎯 Mô tả chi tiết

### 1. Entry Point
- **main.py**: Khởi tạo QApplication và hiển thị BaseWindow

### 2. UI Layer (`UI/`)
- **base_ui.py**: MainWindow chứa sidebar + content area (QStackedWidget)
- **styles.py**: Theme CSS với hiệu ứng Neon Glassmorphism
- **components/sidebar.py**: Navigation menu với signal `nav_clicked(id, label)`
- **enrollment/**: Module đăng ký theo wizard 3 bước
  - **enroll_ui.py**: Orchestrator cho 3 steps
  - **steps/profile_step.py**: Form nhập MSSV + Họ tên
  - **steps/capture_step/**: Module chụp 5 góc (Frontal/Left/Right/Up/Down)
    - **capture_step.py**: UI logic chính
    - **capture_ui.py**: UI components riêng
    - **face_processing_thread.py**: QThread xử lý AI không block UI
  - **steps/success_step.py**: Màn hình xác nhận thành công

### 3. Business Logic (`modules/`)
- **database.py**: 
  - `DatabaseManager` - CRUD cho users, embeddings
  - Foreign key enforcement, transaction safety
- **face_analyzer.py**:
  - `FaceAnalyzer` - detect mặt (InsightFace), kiểm tra distance/pose, trích embedding
  - `PoseType` enum: FRONTAL, LEFT, RIGHT, UP, DOWN
  - `DistanceStatus` enum: OK, TOO_FAR, TOO_CLOSE, NO_FACE
- **pose_logic.py**:
  - `check_pose_logic()` - tính geometric ratio (h_ratio, v_ratio) từ MediaPipe landmarks
  - Stability checking để tránh false positive

### 4. Common Utilities (`common/`)
- **camera.py**: `CameraThread` - QThread emit `frame_captured(np.ndarray)` mỗi frame

### 5. Data (`data/`)
- **faces.db**: SQLite với 2 bảng:
  - `users(id, name, student_id, created_at)`
  - `face_embeddings(id, user_id, embedding_blob, pose_type, created_at)`
- **faces/**: Lưu ảnh raw theo `user_id/pose_type.jpg` (optional, chủ yếu dùng embedding)
- **models/**: InsightFace pretrained models (buffalo_s/buffalo_l)

### 6. Documentation (`docs/`)
- Guides, algorithms, proposals, và file cấu trúc này


