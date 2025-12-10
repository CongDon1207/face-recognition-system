# Cấu trúc thư mục (Project Structure)

```text
FaceRecognitionSystem/
  UI/                         # Giao diện người dùng (PySide6)
    components/               # Thành phần tái sử dụng
      sidebar.py              # Thanh điều hướng trái
    enrollment/               # Module quản lý đăng ký khuôn mặt
      steps/                  # Các bước trong quy trình enroll
        profile_step.py       # Bước 1: Nhập thông tin
        capture_step.py       # Bước 2: Chụp ảnh & checklist
        face_processing_thread.py # Thread xử lý AI cho capture
        success_step.py       # Bước 3: Thông báo thành công
      enroll_ui.py            # Quản lý luồng enroll (Manager)
    base_ui.py                # Cửa sổ chính (MainWindow)
    styles.py                 # Theme & stylesheet
    assets/                   # Tài nguyên (ảnh, icon...)
  common/                     # Tiện ích chung
  data/                       # Dữ liệu khuôn mặt, database
  docs/                       # Tài liệu dự án
    guide/                    # Hướng dẫn chi tiết
      RUN.md                  # Hướng dẫn chạy
      SETUP.md                # Hướng dẫn cài đặt
    STRUCTURE.md              # Cấu trúc thư mục
  modules/                    # Logic xử lý (Face Rec, Camera...)
    database.py               # Quản lý SQLite (users, embeddings)
    face_analyzer.py          # Head pose, distance check, embedding
    camera.py                 # Thread đọc camera
  venv/                       # Môi trường ảo Python
  main.py                     # File khởi chạy
  requirements.txt            # Danh sách thư viện
```

