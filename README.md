# 🔗 ShiftLink Automation Tool

[![Download EXE](https://img.shields.io/github/v/release/khoathoiloi/shorten-link-automation?label=Download%20EXE&logo=windows&color=blue)](https://github.com/khoathoiloi/shorten-link-automation/releases/latest)

Hệ thống tự động hóa trích xuất link từ file Excel, tự động rút gọn link trên nền tảng **ShiftLink** (`https://shorten-link-swart.vercel.app/`) và xuất ra file Excel mới hoàn chỉnh.

---

## 📥 Tải Về Ứng Dụng (Không cần cài Python)
👉 **[Tải file ShiftLink_Automation.exe tại đây](https://github.com/khoathoiloi/shorten-link-automation/releases/latest/download/ShiftLink_Automation.exe)**

---

## 🌟 Tính Năng Nổi Bật

1. **Smart Auto-Detection**: Tự động quét và phát hiện cột chứa link website trong file Excel mà không phụ thuộc vào thứ tự cột (không sợ người dùng đổi cấu trúc cột).
2. **Quy tắc tạo Slug chuẩn SEO**:
   - Lấy ngẫu nhiên từ 15 đến 21 ký tự ở cuối đường dẫn gốc.
   - Bắt buộc bắt đầu bằng chữ cái hoặc số (loại bỏ dấu `-` ở đầu).
   - Giữ nguyên các dấu `-` ở giữa chuỗi.
3. **Bộ nhớ đệm thông minh (Deduplication Cache)**:
   - Nếu trong file Excel có nhiều dòng chứa cùng một link gốc, hệ thống chỉ gọi rút gọn 1 lần duy nhất trên web và tự động điền link đã rút gọn cho toàn bộ các dòng còn lại (tiết kiệm thời gian, chống trùng slug).
4. **Tự động lưu phiên đăng nhập**:
   - Lưu trữ `user_data` (cookies, local storage), chỉ cần đăng nhập tài khoản 1 lần duy nhất, các lần chạy sau tự động nhận diện tài khoản.
5. **Xuất file Excel chuyên nghiệp**:
   - Giữ nguyên 100% định dạng, dữ liệu file gốc.
   - Thêm cột mới `Link da rut gon` có tiền tố `watch full here 👉: https://nextpart2.online/...`.

---

## 🚀 Hướng Dẫn Sử Dụng

### Cách 1: Sử dụng file chạy trực tiếp (`ShiftLink_Automation.exe`)
1. Tải file `ShiftLink_Automation.exe` từ mục **Releases**.
2. Nhấp đúp mở file.
3. Kéo thả file Excel của bạn vào cửa sổ console và nhấn `Enter`.
4. Chương trình sẽ tự động mở Chrome và thực hiện toàn bộ quy trình cho đến khi hoàn tất.

### Cách 2: Chạy bằng mã nguồn Python
1. Cài đặt các thư viện:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
2. Chạy kịch bản:
   ```bash
   python main.py
   ```

---

## 🛠️ Công Nghệ Sử Dụng
- **Python 3.12**
- **Playwright** (Tự động hóa trình duyệt Web)
- **OpenPyXL** (Xử lý bảng tính Excel)
- **PyInstaller** (Đóng gói ứng dụng Desktop)
