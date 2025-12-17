# Hướng dẫn Cài đặt & Môi trường

## 1. Yêu cầu Hệ thống
- **OS**: Windows 10/11
- **Python**: 3.10 hoặc 3.11
- **GPU**: NVIDIA RTX (2050, 3050, 4060...) để có hiệu năng tốt nhất.

## 2. Cài đặt Môi trường Python
```bash
# Tạo môi trường ảo
python -m venv venv

# Kích hoạt (Windows)
.\venv\Scripts\activate

# Cài đặt thư viện
pip install -r requirements.txt
```

---

## 3. Hướng dẫn Cài đặt GPU (RTX 2050 / 3050...)

Dưới đây là hướng dẫn từng bước chi tiết nhất để bạn cài đặt thành công cho máy RTX 2050 của mình.

### BƯỚC 1: Tải và cài CUDA Toolkit 12.4

*Mục đích: Cài bộ công cụ để Windows "hiểu" và điều khiển được GPU chạy code.*

1.  **Truy cập link tải:**
    Bạn vào Google tìm "CUDA Toolkit 12.4 archive" hoặc vào link trang chủ NVIDIA.
2.  **Chọn cấu hình tải (Bấm đúng theo thứ tự):**
      * Operating System: **Windows**
      * Architecture: **x86\_64**
      * Version: **11** (hoặc **10** tùy win của bạn, thường chọn 11 vẫn chạy được trên 10).
      * Installer Type: **exe (local)**
3.  **Cài đặt:**
      * Bấm **Download** (khoảng 3.0 GB).
      * Chạy file `.exe` vừa tải về.
      * Nó sẽ hiện bảng hỏi nơi giải nén tạm thời -\> Bấm **OK**.
      * Màn hình cài đặt hiện ra:
          * Nó kiểm tra hệ thống (System Check) -\> Chờ 1 chút.
          * License Agreement -\> Bấm **Agree and Continue**.
          * Installation Options (Quan trọng): Chọn **Express (Recommended)**.
          * Bấm **Next** và chờ cài đặt xong (khoảng 5-10 phút).
          * Bấm **Close** khi hoàn tất.

-----

### BƯỚC 2: Tải và cài cuDNN 8.9

*Mục đích: Thư viện chuyên dụng để GPU tính toán AI nhanh hơn.*

1.  **Tải về:**
      * Vào Google tìm "NVIDIA cuDNN archive".
      * Bạn có thể cần đăng nhập tài khoản NVIDIA (nếu chưa có thì đăng ký nhanh bằng Gmail).
      * Tìm dòng: **Download cuDNN v8.9.7 (December 5th, 2023), for CUDA 12.x**.
      * Tải file: **Local Installer for Windows (Zip)**.
2.  **Giải nén:**
      * Giải nén file Zip vừa tải.
      * Bạn sẽ thấy một thư mục bên trong, mở ra cho đến khi thấy **3 thư mục con** tên là: `bin`, `include`, `lib`.
3.  **Copy và Dán (Quan trọng):**
      * **Bôi đen** cả 3 thư mục `bin`, `include`, `lib` và chọn **Copy** (Ctrl+C).
      * Mở thư mục cài đặt CUDA Toolkit trên máy bạn theo đường dẫn sau:
        `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4`
      * Tại đây, bạn dán (**Paste**) 3 thư mục vừa copy vào khoảng trống.
      * **Lưu ý:** Nếu Windows hỏi "Replace the files in the destination?" (Ghi đè file?), hãy chọn **Yes** (hoặc Replace). Nếu hỏi quyền Admin, chọn **Continue**.

-----

### BƯỚC 3: Kiểm tra lại (Bắt buộc)

Sau khi chép xong, bạn phải kiểm tra xem máy đã nhận chưa.

1.  Tắt cửa sổ CMD cũ đi.
2.  Mở cửa sổ CMD mới.
3.  Gõ lệnh sau:

<!-- end list -->

```cmd
nvcc --version
```

Nếu nó hiện ra thông tin: `Cuda compilation tools, release 12.4, V12.4.xx` là **Thành công**.

-----

### BƯỚC 4: Sửa lỗi thiếu zlibwapi.dll (Quan trọng)

*Mục đích: Sửa lỗi "Error 126" hoặc GPU không được nhận diện do thiếu thư viện mở rộng.*

**Triệu chứng:** Nếu bạn gặp lỗi khi chạy code mặc dù đã cài đủ CUDA/cuDNN.

1.  **Tải file sửa lỗi:**
      * Link tải: [http://www.winimage.com/zLibDll/zlib123dllx64.zip](http://www.winimage.com/zLibDll/zlib123dllx64.zip)
      * Tải file zip về máy.
2.  **Giải nén:**
      * Mở file zip ra, tìm file có tên `zlibwapi.dll` (bên trong thư mục `dll_x64`).
3.  **Copy và Dán:**
      * Copy file `zlibwapi.dll`.
      * Dán vào cùng thư mục `bin` của CUDA lúc nãy:
        `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin`
      * **Kiểm tra:** Đảm bảo trong thư mục `bin` này giờ đã có cả `cudnn64_8.dll` và `zlibwapi.dll` nằm cạnh nhau.

**Hoàn tất:** Giờ bạn có thể chạy lại chương trình để tận hưởng tốc độ GPU!
