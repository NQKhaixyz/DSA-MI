# LƯU Ý VÀ HẠN CHẾ (KNOWN ISSUES)

## Hệ Thống Quản Lý Bệnh Viện MediCare Pro

**Phiên bản:** v2.5  
**Ngày cập nhật:** 15/06/2026

---

## Mục Lục

1. [Hạn chế về kiến trúc](#1-hạn-chế-về-kiến-trúc)
2. [Hạn chế về dữ liệu](#2-hạn-chế-về-dữ-liệu)
3. [Hạn chế về bảo mật](#3-hạn-chế-về-bảo-mật)
4. [Hạn chế về hiệu năng](#4-hạn-chế-về-hiệu-năng)
5. [Các vấn đề đã biết (Known Issues)](#5-các-vấn-đề-đã-biết-known-issues)
6. [Các hạn chế của thuật toán](#6-các-hạn-chế-của-thuật-toán)
7. [Lưu ý khi sử dụng](#7-lưu-ý-khi-sử-dụng)
8. [Đề xuất cải tiến tương lai](#8-đề-xuất-cải-tiến-tương-lai)

---

## 1. Hạn chế về kiến trúc

### 1.1. Lưu trữ In-Memory

**Vấn đề:**
- Hệ thống sử dụng Python dictionaries (hash tables) làm "database"
- Dữ liệu chỉ tồn tại trong RAM (Random Access Memory)
- **Mất toàn bộ dữ liệu khi tắt server** (trừ khi đã bấm "Lưu" để xuất JSON)

**Giải pháp tạm thời:**
- Luôn bấm **"Lưu dữ liệu"** trước khi tắt server
- File JSON được lưu tại thư mục làm việc
- Khởi động lại: Bấm **"Tải dữ liệu"** để khôi phục

**Giải pháp dài hạn:**
- Chuyển sang SQLite/PostgreSQL cho persistence thực sự
- Thêm auto-save định kỳ (cron job)

### 1.2. Single-Process, Single-Thread

**Vấn đề:**
- Flask development server chạy single-threaded
- Không hỗ trợ concurrent requests hiệu quả
- Nhiều user đồng thời có thể gây race condition

**Giải pháp tạm thời:**
- Chỉ sử dụng trong môi trường single-user
- Không dùng cho production multi-user

**Giải pháp dài hạn:**
- Chuyển sang Gunicorn/uWSGI + Nginx
- Thêm Redis cho session management
- Sử dụng database transactions

### 1.3. Không có REST API đầy đủ

**Vấn đề:**
- Một số endpoints không có validation đầy đủ
- Không có API versioning
- Không có rate limiting

---

## 2. Hạn chế về dữ liệu

### 2.1. Không có khóa ngoại (Foreign Keys)

**Vấn đề:**
- Relations giữa các entities chỉ là "soft references" (string IDs)
- Có thể tạo dữ liệu "orphan" (vd: visit trỏ đến patient không tồn tại)
- Không có cascade delete/update

**Ví dụ:**
```python
# Visit có patientID nhưng patient đã bị xóa
visit.patientID = "PAT_123"  # PAT_123 có thể không tồn tại
```

### 2.2. Không có validation đầy đủ

**Vấn đề:**
- Một số fields không có validation (vd: email, SĐT)
- Date format không strict (chấp nhận nhiều định dạng)
- Không có data type checking

### 2.3. Giới hạn về số lượng

| Giới hạn | Giá trị | Ghi chú |
|----------|---------|---------|
| Số khoa/ngày | Tối đa 3 | Quy định trong config |
| Số lịch hẹn/slot | Tối đa 4 | Quy định trong config |
| Số phòng/khoa | 1-2 (demo) | Có thể mở rộng |
| Số bác sĩ/khoa | 2 (demo) | Có thể mở rộng |
| Tổng records | Không giới hạn thực | Nhưng >100k sẽ chậm |

### 2.4. Không có lịch sử thay đổi

**Vấn đề:**
- Không log audit trail
- Không biết ai đã thay đổi dữ liệu
- Không có rollback

---

## 3. Hạn chế về bảo mật

### 3.1. Không có xác thực (Authentication)

**Vấn đề:**
- Không cần đăng nhập
- Không có phân quyền (RBAC)
- Mọi người đều có thể thực hiện mọi thao tác

**Rủi ro:**
- Bất kỳ ai truy cập URL đều có thể xóa/sửa dữ liệu
- Không có session management

**Giải pháp dài hạn:**
- Thêm JWT authentication
- Phân quyền: Admin, Bác sĩ, Y tá, Thu ngân
- Session timeout

### 3.2. Không có mã hóa

**Vấn đề:**
- Dữ liệu lưu trữ dạng plain text (JSON)
- Không mã hóa thông tin nhạy cảm (CCCD, SĐT)
- Không có HTTPS (nếu deploy public)

### 3.3. Không có input sanitization

**Vấn đề:**
- Có thể bị XSS nếu hiển thị dữ liệu user nhập trực tiếp
- Không có CSRF protection
- SQL injection không áp dụng (không có SQL) nhưng command injection vẫn có thể

---

## 4. Hạn chế về hiệu năng

### 4.1. Không có caching

**Vấn đề:**
- Mỗi request đều tính toán lại từ đầu
- Không cache dashboard statistics
- Không cache danh sách phòng/bác sĩ

### 4.2. Auto-refresh gây overhead

**Vấn đề:**
- Mỗi tab gọi API mỗi 5 giây
- Nhiều tab mở đồng thời gây nhiều request
- Không có debounce

**Giải pháp:**
- Tăng interval lên 10-30 giây
- Chỉ refresh khi có focus
- Dùng WebSocket thay vì polling

### 4.3. Không có pagination

**Vấn đề:**
- API trả về toàn bộ danh sách
- Với 10,000+ records, response size lớn
- Frontend render tất cả cùng lúc

---

## 5. Các vấn đề đã biết (Known Issues)

### 5.1. Vấn đề về UI

| # | Vấn đề | Mức độ | Ghi chú |
|---|--------|--------|---------|
| 1 | Responsive chưa tốt trên mobile | Trung bình | Cần CSS media queries |
| 2 | Không có dark mode | Thấp | Tính năng bổ sung |
| 3 | Không có print CSS riêng | Thấp | In hóa đơn dùng browser print |
| 4 | Toast notification có thể bị tràn | Thấp | Giới hạn số toast hiển thị |
| 5 | Loading spinner không center đúng | Thấp | CSS issue |

### 5.2. Vấn đề về chức năng

| # | Vấn đề | Mức độ | Ghi chú |
|---|--------|--------|---------|
| 1 | Không thể sửa hóa đơn đã thanh toán | Thấp | Theo thiết kế |
| 2 | Không thể hủy lịch hẹn | Trung bình | Cần thêm endpoint |
| 3 | Không có báo cáo thống kê | Trung bình | Cần thêm tab báo cáo |
| 4 | Không có tìm kiếm bệnh nhân | Trung bình | Cần search box |
| 5 | Không có lịch sử khám của BN | Trung bình | Cần thêm view |
| 6 | Không thể xóa bệnh nhân | Thấp | Cần soft delete |
| 7 | Không có import/export CSV | Thấp | Chỉ có JSON |
| 8 | Không có nhắc nhở lịch hẹn | Thấp | Cần notification system |

### 5.3. Vấn đề về ngrok (public URL)

| # | Vấn đề | Mức độ | Ghi chú |
|---|--------|--------|---------|
| 1 | URL thay đổi sau restart | Trung bình | Dùng ngrok paid hoặc Cloudflare |
| 2 | Tunnel timeout sau 2 giờ | Thấp | Free plan limitation |
| 3 | Không có custom domain | Thấp | Cần paid plan |
| 4 | Rate limiting | Thấp | Free plan: 40 connections/phút |

---

## 6. Các hạn chế của thuật toán

### 6.1. Strict Priority Scheduling

**Ưu điểm:**
- Đơn giản, O(1) cho dequeue
- Đảm bảo cấp cứu luôn được ưu tiên

**Hạn chế:**
- Starvation: BN thường có thể đợi rất lâu nếu liên tục có cấp cứu
- Không có aging mechanism
- Không xét đến thời gian chờ thực tế

**Giải pháp:**
- Thêm priority aging (tăng priority sau 30 phút chờ)
- Hoặc dùng Weighted Fair Queueing

### 6.2. Shortest Queue First

**Ưu điểm:**
- Cân bằng tải giữa các phòng
- Giảm thời gian chờ trung bình

**Hạn chế:**
- Không xét đến thời gian khám thực tế của từng BN
- Không xét đến kỹ năng/kinh nghiệm của bác sĩ
- Có thể dẫn đến 1 phòng quá tải nếu BN phức tạp

### 6.3. Two-Pass Validation

**Ưu điểm:**
- Đảm bảo tính nguyên tử (atomicity)
- Không bị partial update

**Hạn chế:**
- Không có pessimistic locking
- Race condition nếu 2 người cùng thanh toán đơn có thuốc giống nhau
- Không có retry mechanism

---

## 7. Lưu ý khi sử dụng

### 7.1. Trước khi tắt server

```
⚠️ QUAN TRỌNG: Luôn bấm "Lưu dữ liệu" trước khi tắt server!

Nếu không, toàn bộ dữ liệu sẽ bị mất:
- Bệnh nhân
- Lượt khám
- Hóa đơn
- Đơn thuốc
- V.v.
```

### 7.2. Khi dùng dữ liệu mẫu

```
⚠️ CẢNH BÁO: "Sinh dữ liệu mẫu" sẽ XÓA toàn bộ dữ liệu hiện tại!

- Chỉ dùng cho lần đầu demo
- Hoặc khi muốn reset hệ thống
- Nhớ lưu dữ liệu quan trọng trước khi dùng
```

### 7.3. Khi thanh toán

```
⚠️ LƯU Ý: Thanh toán KHÔNG THỂ HOÀN TÁC!

- Hóa đơn đã thanh toán không thể sửa
- Thuốc đã trừ trong kho
- Nếu nhập sai % BHYT, phải tạo visit mới
```

### 7.4. Khi kê đơn thuốc

```
⚠️ LƯU Ý: Chọn thuốc từ datalist (gợi ý)!

- Nếu gõ tay tên thuốc không đúng:
  - Hệ thống không tìm thấy medicineID
  - Tính tiền thuốc = 0đ
  - Không trừ kho
- Luôn chọn từ danh sách gợi ý để đảm bảo đúng ID
```

### 7.5. Khi chuyển khoa

```
⚠️ GIỚI HẠN: Tối đa 3 khoa/ngày!

- Hệ thống tự động chặn nếu > 3 khoa
- Không thể khám lại khoa đã khám trong cùng visit
- Nếu cần khám lại: Tạo visit mới
```

### 7.6. Khi deploy public

```
⚠️ BẢO MẬT: Không dùng cho production!

- URL public có thể bị truy cập bởi bất kỳ ai
- Không có xác thực
- Dữ liệu demo không dùng thông tin thật
- Ngrok free: URL thay đổi, timeout sau 2 giờ
```

---

## 8. Đề xuất cải tiến tương lai

### 8.1. Tính năng bắt buộc (Must-have)

- [ ] Database thực (SQLite/PostgreSQL)
- [ ] Authentication & Authorization (JWT)
- [ ] Audit log (lịch sử thay đổi)
- [ ] Input validation & sanitization
- [ ] HTTPS/SSL
- [ ] Backup tự động

### 8.2. Tính năng nên có (Should-have)

- [ ] Pagination cho API
- [ ] Search & Filter
- [ ] Báo cáo thống kê (PDF/Excel)
- [ ] Email/SMS notification
- [ ] Lịch hẹn calendar view
- [ ] Import/Export CSV

### 8.3. Tính năng tốt có (Nice-to-have)

- [ ] Dark mode
- [ ] Mobile app (PWA)
- [ ] Real-time WebSocket
- [ ] Chat/Comment trong hệ thống
- [ ] Voice call cho cấp cứu
- [ ] AI phân tích triệu chứng

### 8.4. Cải tiến kỹ thuật

- [ ] Async/await cho I/O operations
- [ ] Redis caching
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Unit test coverage > 90%
- [ ] Integration testing

---

## Liên hệ và báo cáo lỗi

Nếu phát hiện lỗi mới, vui lòng:

1. Mô tả chi tiết lỗi
2. Các bước reproduce
3. Screenshot (nếu có)
4. Môi trường (OS, Browser, Python version)

**GitHub:** https://github.com/NQKhaixyz/DSA-MI/issues

---

*Phiên bản: v2.5*  
*Cập nhật: 15/06/2026*
