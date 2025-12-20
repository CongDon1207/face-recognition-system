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
│   │   ├── auth_panel.py           # Panel camera + HUD + status
│   │   ├── auth_view_logic.py      # Logic UI xac thuc (progress, lockout, overlay)
│   │   └── liveness.py             # Panel/bước hiển thị liveness
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
│   ├── 📁 workers/                 # Qt Background Threads (Presentation Layer support)
│   │   ├── auth_worker.py          # Worker cho Authentication
│   │   └── enroll_worker.py        # Worker cho Enrollment
│   └── 📁 assets/                  # Tài nguyên (icon, hình ảnh)
│       ├── 📁 icons/
│       └── 📁 images/
│
├── 📁 modules/                     # Business Logic + Data Access Layer
│   ├── 📁 ai/                      # Lớp AI Processing (Business Logic)
│   │   ├── face_analyzer.py    # FaceAnalyzer core
│   │   ├── liveness_detector.py # Liveness detection
│   │   └── pose_logic.py       # Thuật toán head pose
│   ├── database.py                 # Data Access: SQLite Manager (users, embeddings, events)
│   ├── camera.py                   # Data Access: CameraThread đọc webcam
│   └── authenticator.py            # Business Logic: So khớp khuôn mặt
│
├── 📁 data/                        # Dữ liệu runtime
├── 📁 docs/                        # Tài liệu dự án
?   ??? ?? plans/                   # Thiet ke / ke hoach noi bo
?       ??? 2025-12-19-liveness-progress-design.md
└── 📁 venv/                        # Môi trường ảo (git ignored)
```

## 🎯 Mô tả chi tiết

### 0. Kiến trúc 3 lớp (Layered Architecture)
Hệ thống tuân theo kiến trúc phân lớp rõ ràng:
- **Presentation Layer**: `UI/` - Giao diện người dùng, bao gồm cả Qt workers hỗ trợ background processing
- **Business Logic Layer**: `modules/ai/`, `modules/authenticator.py` - Xử lý logic nghiệp vụ, AI, so khớp
- **Data Access Layer**: `modules/database.py`, `modules/camera.py` - Quản lý cơ sở dữ liệu và truy cập camera

Các lớp chỉ giao tiếp trực tiếp với lớp liền kề, đảm bảo phân tách rõ ràng và dễ bảo trì.

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

### 3. Business Logic + Data Access Layer (`modules/`)
**Business Logic:**
- **authenticator.py**: Logic so khớp khuôn mặt
- **ai/face_analyzer.py**:
  - `FaceAnalyzer` - detect mặt (InsightFace), kiểm tra distance/pose, trích embedding
  - `PoseType` enum: FRONTAL, LEFT, RIGHT, UP, DOWN
  - `DistanceStatus` enum: OK, TOO_FAR, TOO_CLOSE, NO_FACE
- **ai/liveness_detector.py**: Kiểm tra tính "sống" của khuôn mặt (anti-spoofing)
- **ai/pose_logic.py**:
  - `check_pose_logic()` - tính geometric ratio (h_ratio, v_ratio) từ MediaPipe landmarks
  - Stability checking để tránh false positive

**Data Access Layer:**
- **database.py**: 
  - `DatabaseManager` - CRUD cho users, embeddings, events
  - Foreign key enforcement, transaction safety
- **camera.py**: `CameraThread` - QThread đọc webcam, emit `frame_captured(np.ndarray)` mỗi frame

### 4. UI Workers (`UI/workers/`)
- **auth_worker.py**: Qt background thread xử lý AI cho màn Authentication
- **enroll_worker.py**: Qt background thread xử lý AI cho màn Enrollment

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


