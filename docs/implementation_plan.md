# Kế hoạch Triển khai Hệ thống Nhận diện Khuôn mặt (Chiến lược UI First)

## Mục tiêu
Xây dựng ứng dụng nhận diện khuôn mặt Real-time với UI "Neon Glass" hiện đại.
**Chiến lược**: Tập trung hoàn thiện 100% Giao diện (Front-end) trước để chốt thiết kế, sau đó mới tích hợp logic (Back-end).

## Chi tiết Thiết kế UI/UX (Đã duyệt)
- **Theme**: Dark Mode (`#1e1e2e`), Accent Cyan (`#00f2ff`).
- **Layout**: Sidebar trái, Content phải (Stacked Widget).
- **Features**: Liveness check, Animation quét, Thẻ thông tin trượt.

---

## CÁC BƯỚC THỰC HIỆN (ĐÃ SẮP XẾP LẠI)

### Giai đoạn 1: Khởi tạo & Tài nguyên (Setup)
*Mục tiêu: Chuẩn bị "nguyên liệu" cho giao diện.*

1.  **Cài đặt & Cấu trúc**:
    -   Tạo file [requirements.txt](file:///d:/hk1nam4/Digital_Image/FaceRecognitionSystem/requirements.txt) (pyside6, opencv-python, ...).
    -   Tạo cây thư mục: `assets/`, `UI/`, `common/`, `modules/`, `data/`.
    -   Tạo file `main.py` rỗng.

2.  **Tài nguyên Giao diện (`assets/`)**:
    -   **`style.qss`**: Viết CSS định nghĩa màu sắc Neon, nút bấm bo tròn, thanh cuộn tùy chỉnh.
    -   **Icons**: Tạo/Copy các icon vector (SVG) cho Sidebar (Home, Face ID, Settings) và các nút điều khiển.

### Giai đoạn 2: Xây dựng Khung Giao diện (UI Skeleton)
*Mục tiêu: Lên hình cửa sổ ứng dụng, điều hướng mượt mà.*

3.  **Cửa sổ chính (`UI/base_ui.py`)**:
    -   Class `MainWindow(QMainWindow)`.
    -   Cài đặt `FramelessWindowHint` (Bỏ viền Windows cũ).
    -   Thiết kế **Sidebar**:
        -   Sử dụng `QVBoxLayout`.
        -   Thêm các nút điều hướng với hiệu ứng Hover phát sáng (dùng QSS).
    -   Thiết kế **Content Area**:
        -   Sử dụng `QStackedWidget` để chứa các trang con.
    -   Logic: Click nút Sidebar -> Chuyển trang `QStackedWidget`.

### Giai đoạn 3: Hiện thực Chi tiết Màn hình (Screens)
*Mục tiêu: Vẽ chi tiết từng màn hình với các thành phần đồ họa (Dummy Data).*

4.  **Màn hình Xác thực (`UI/auth_ui.py`)**:
    -   Class `AuthPage(QWidget)`.
    -   **Placeholder Camera**: Tạo một khung đen (`QLabel`) có bo góc, nằm giữa màn hình.
    -   **Overlay (Lớp phủ)**:
        -   Dùng `QPainter` vẽ khung ngắm (Reticle) tĩnh.
        -   Tạo Animation cho đường quét (Scan line) chạy lên xuống (giả lập).
    -   **Thẻ Thông tin (Card)**:
        -   Tạo một Widget con chứa Avatar + Tên Dummy ("Nguyễn Văn A").
        -   Làm hiệu ứng Slide-in (Trượt vào) để test animation.

5.  **Màn hình Đăng ký (`UI/enroll_ui.py`)**:
    -   Class `EnrollPage(QWidget)`.
    -   **Layout 2 cột**:
        -   Trái: Khung Camera (giả lập).
        -   Phải: Form nhập liệu (Input Tên) và List hướng dẫn (Checklist).
    -   **Thanh tiến trình**: Vẽ một vòng tròn (Circular Progress) chưa chạy, để canh chỉnh vị trí.

6.  **Tích hợp `main.py` (Test UI)**:
    -   Chạy file chính.
    -   Kiểm tra logic chuyển trang.
    -   Kiểm tra độ phản hồi của nút bấm, màu sắc, font chữ.

### Giai đoạn 4: Kết nối Camera & Backend (Sau khi UI đã đẹp)
*Mục tiêu: Làm cho giao diện "sống" với dữ liệu thật.*

7.  **Camera Thread (`common/camera.py`)**: 
    -   Đọc webcam thật -> Đẩy hình lên UI thay cho khung đen placeholder.
8.  **Backend Logic (`modules/`)**:
    -   Implement `liveness.py` (Check mắt/đầu).
    -   Implement `matcher.py` (So khớp khuôn mặt).
9.  **Wiring (Đấu nối)**:
    -   Nối tín hiệu Camera vào Logic check Liveness/Matching.
    -   Cập nhật trạng thái UI dựa trên kết quả trả về (VD: Đổi màu viền đỏ nếu Fake, Xanh nếu Real).

---

## Kế hoạch kiểm thử (Verification)
1.  **Test Giao diện**: Chạy app, click chuyển qua lại các tab. Đảm bảo không bị lag, giật. Resize cửa sổ xem bố cục có vỡ không.
2.  **Test Thẩm mỹ**: So sánh thực tế với ý tưởng "Neon Glass". Màu sắc có đủ độ tương phản không?
3.  **Test Chức năng (Sau GĐ 4)**: Flow đăng ký và xác thực hoạt động trơn tru.
