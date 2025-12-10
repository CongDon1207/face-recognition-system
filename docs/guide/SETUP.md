# Thiết lập môi trường (Setup)

## 1. Tạo Virtual Environment
```bash
python -m venv venv
```

## 2. Kích hoạt môi trường

**Windows (CMD/PowerShell):**
```bash
.\venv\Scripts\activate
```

**Git Bash:**
```bash
source venv/Scripts/activate
```

## 3. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

## 4. Chuẩn bị Model (Tùy chọn)

Ứng dụng sẽ tự động tải model khi chạy lần đầu. Tuy nhiên, nếu bạn muốn tải thủ công (để copy sang máy offline):

1.  **Tải model**:
    *   **buffalo_s.zip** (Cho CPU - Nhẹ): [Link Tải](https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_s.zip)
    *   **buffalo_l.zip** (Cho GPU - Chuẩn): [Link Tải](https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip)

2.  **Giải nén**:
    *   Tạo thư mục: `data/models` trong thư mục gốc dự án.
    *   Giải nén file zip vào đó.

3.  **Cấu trúc thư mục đúng**:
    ```text
    FaceRecognitionSystem/
    ├── data/
    │   └── models/
    │       ├── buffalo_s/
    │       │   ├── 1k3d68.onnx
    │       │   ├── 2d106det.onnx
    │       │   └── ...
    │       └── buffalo_l/
    │           ├── 1k3d68.onnx
    │           └── ...
    ```
