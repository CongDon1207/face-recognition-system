# Cấu trúc thư mục (Project Structure)

## 📂 Tổng quan

```
FaceRecognitionSystem/
├── 📄 main.py                      # Entry point - khởi chạy ứng dụng
├── 📄 requirements.txt             # Danh sách dependencies
├── 📄 README.md                    # Tài liệu tổng quan dự án
├── 📄 CHANGELOG.md                 # Lịch sử thay đổi
├── 📄 AGENTS.md                    # Quy tắc code cho AI agents
│
├── 📁 UI/                          # Giao diện người dùng (PySide6)
│   ├── base_ui.py                  # MainWindow - cửa sổ chính (quản lý auth state)
│   ├── styles.py                   # Theme Neon Glassmorphism
│   ├── 📁 components/              # UI components tái sử dụng
│   │   └── sidebar.py              # Navigation sidebar (2 mode: guest/authenticated)
│   ├── 📁 authentication/          # Module xác thực khuôn mặt
│   │   ├── auth_ui.py              # Giao diện Authentication
│   │   └── success_view.py         # (Legacy - không dùng nữa)
│   ├── 📁 enrollment/              # Module đăng ký khuôn mặt
│   │   ├── enroll_ui.py            # Manager 3-step wizard
│   │   └── 📁 steps/
│   │       ├── profile_step.py
│   │       ├── 📁 capture_step/
│   │       │   ├── capture_step.py
│   │       │   └── capture_ui.py
│   │       └── success_step.py
│   ├── 📁 dashboard/               # Dashboard (sau khi auth thành công)
│   │   └── dashboard_ui.py         # Stats cards + Logs table + Chart placeholder
│   ├── 📁 profile/                 # Trang Profile người dùng
│   │   └── profile_ui.py           # Hiển thị thông tin user đang đăng nhập
│   ├── 📁 about/                   # Trang About
│   │   └── about_ui.py             # Thông tin ứng dụng
│   └── 📁 assets/                  # Tài nguyên (icon, hình ảnh)
│       ├── 📁 icons/
│       └── 📁 images/
│
├── 📁 modules/                     # Business logic
│   ├── 📁 ai/                      # Lớp AI Processing
│   │   ├── face_analyzer.py    # FaceAnalyzer core
│   │   └── pose_logic.py       # Thuật toán head pose
│   ├── database.py                 # SQLite Manager (users, embeddings, events)
│   └── authenticator.py            # Logic so khớp khuôn mặt
│
├── 📁 common/                      # Tiện ích dùng chung
│   ├── camera.py                   # Đọc webcam
│   └── 📁 workers/                 # Các Worker Thread chạy ngầm (Qt)
│       ├── auth_worker.py      # Worker cho Authentication
│       └── enroll_worker.py    # Worker cho Enrollment (đổi tên từ face_processing_thread)
│
├── 📁 data/                        # Dữ liệu runtime
├── 📁 docs/                        # Tài liệu dự án
└── 📁 venv/                        # Môi trường ảo (git ignored)
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
- **faces.db**: SQLite với 3 bảng:
  - `users(id, fullname, email, phone, dob, avatar_path, created_at)`
  - `face_embeddings(id, user_id, embedding_blob, pose_type, image_path, created_at)`
  - `events(id, event_type, user_id, result, score, details, created_at)` - logs cho Dashboard
- **faces/**: Lưu ảnh raw theo `user_id/pose_type.jpg` (optional, chủ yếu dùng embedding)
- **models/**: InsightFace pretrained models (buffalo_s/buffalo_l)

### 6. Navigation Flow
- **Guest Mode** (chưa xác thực): Chỉ hiển thị Authentication + Enrollment
- **Authenticated Mode** (sau khi auth thành công): Dashboard + Profile + About + Logout
- Logout sẽ reset về Guest Mode

### 7. Documentation (`docs/`)
- Guides, algorithms, proposals, và file cấu trúc này


