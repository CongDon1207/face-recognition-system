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
