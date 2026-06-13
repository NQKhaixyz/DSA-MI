# HƯỚNG DẪN SỬ DỤNG CHI TIẾT

## Hệ Thống Quản Lý Bệnh Viện MediCare Pro

**Phiên bản:** v2.3  
**Ngày cập nhật:** 13/06/2026

---

## Mục Lục

1. [Giới thiệu](#1-giới-thiệu)
2. [Cài đặt và chạy](#2-cài-đặt-và-chạy)
3. [Luồng nghiệp vụ chính](#3-luồng-nghiệp-vụ-chính)
4. [Hướng dẫn chi tiết từng tab](#4-hướng-dẫn-chi-tiết-từng-tab)
5. [Xử lý lỗi thường gặp](#5-xử-lý-lỗi-thường-gặp)
6. [Lưu ý quan trọng](#6-lưu-ý-quan-trọng)

---

## 1. Giới thiệu

### 1.1. Tổng quan hệ thống

MediCare Pro là hệ thống quản lý bệnh viện mô phỏng, cung cấp đầy đủ các chức năng:

- **Tiếp đón:** Đăng ký khám, đặt lịch hẹn, check-in
- **Phòng khám:** Gọi số, chỉ định dịch vụ, kê đơn thuốc, chuyển khoa
- **Thu ngân:** Thanh toán viện phí, áp dụng BHYT, in hóa đơn
- **Dashboard:** Thống kê real-time, danh sách chờ

### 1.2. Các thực thể

| Thực thể | Mô tả | Mã định danh |
|----------|-------|-------------|
| Bệnh nhân (Patient) | Người đến khám | `PAT_xxx` hoặc `BN_xxx` |
| Bác sĩ (Doctor) | Người khám chữa bệnh | `DOC_xxx` |
| Khoa (Department) | Chuyên khoa | Tên khoa (vd: `NoiTongQuat`) |
| Phòng (Room) | Phòng khám | `ROOM_xxx` |
| Dịch vụ (Service) | Xét nghiệm, thủ thuật | `SVC_xxx` |
| Thuốc (Medicine) | Thuốc trong kho | `MED_xxx` |
| Lượt khám (Visit) | Một lần khám bệnh | `VISIT_xxx` |
| Đơn thuốc (Prescription) | Đơn thuốc kê | `PRE_xxx` |
| Hóa đơn (Bill) | Hóa đơn thanh toán | `BILL_xxx` |
| Lịch hẹn (Appointment) | Lịch hẹn khám | `APT_xxx` |

---

## 2. Cài đặt và chạy

### 2.1. Yêu cầu hệ thống

- Python 3.11+
- pip
- Trình duyệt web (Chrome, Firefox, Edge)

### 2.2. Cài đặt

```bash
# 1. Clone repository
git clone https://github.com/NQKhaixyz/DSA-MI.git
cd DSA-MI

# 2. Cài đặt dependencies
pip install -r requirements.txt

# 3. Khởi chạy server
python app.py
```

### 2.3. Truy cập

- **Local:** http://127.0.0.1:5000
- **Public (ngrok):** https://tidbit-repayment-prewar.ngrok-free.dev (có thể thay đổi)

### 2.4. Deploy public (tùy chọn)

```bash
# Cài ngrok
# Download từ https://ngrok.com/download

# Cấu hình authtoken
ngrok authtoken YOUR_TOKEN

# Khởi động tunnel
ngrok http 5000
```

---

## 3. Luồng nghiệp vụ chính

### 3.1. Luồng khám bệnh thông thường

```
Bước 1: Tiếp đón (Tab "Quản lý Bệnh nhân")
  ↓ Nhập thông tin BN → Chọn khoa → Bấm "Tạo"
  ↓ BN xuất hiện trong bảng với nút "Check-in" (ĐỎ)
  
Bước 2: Check-in
  ↓ Bấm nút "Check-in" (ĐỎ)
  ↓ Chuyển thành "Đã check-in" (Xanh Lá)
  ↓ BN được xếp vào hàng đợi phòng khám

Bước 3: Phòng khám (Tab "Phòng Khám")
  ↓ Chọn phòng → Click "Gọi bệnh nhân tiếp"
  ↓ BN vào phòng khám
  ↓ Chỉ định dịch vụ (nếu cần)
  ↓ Kê đơn thuốc (nếu cần)
  ↓ Bấm "Hoàn tất khám"
  ↓ BN chuyển sang trạng thái "Chờ thanh toán"

Bước 4: Thanh toán (Tab "Thu ngân & Kho Dược")
  ↓ Chọn lượt khám → Bấm "Tải"
  ↓ Kiểm tra dịch vụ + thuốc
  ↓ Nhập % BHYT (nếu có)
  ↓ Bấm "Thanh toán"
  ↓ In hóa đơn (nếu cần)
```

### 3.2. Luồng đặt lịch hẹn trước

```
Bước 1: Tiếp đón
  ↓ Chọn "Hình thức tiếp đón: Có đặt lịch trước"
  ↓ Chọn khoa → Chọn bác sĩ → Chọn ngày/giờ
  ↓ Bấm "Tạo"
  ↓ Tạo lịch hẹn + Visit

Bước 2: Đến ngày khám
  ↓ BN đến bệnh viện
  ↓ Tìm lịch hẹn trong danh sách
  ↓ Bấm "Check-in"
  ↓ Ưu tiên hàng đợi (mức 2)
```

### 3.3. Luồng cấp cứu

```
Bước 1: Nhập mã Visit trong "Kích hoạt cấp cứu"
  ↓ Bấm "Kích hoạt"
  ↓ BN được đẩy lên đầu hàng đợi (mức 3)
  ↓ Preempt: BN đang khám có thể bị tạm dừng
```

---

## 4. Hướng dẫn chi tiết từng tab

### 4.1. Tab Dashboard

**Chức năng:** Xem tổng quan hệ thống

**Các chỉ số:**
- Tổng số bệnh nhân
- Tổng số bác sĩ
- Lượt khám đang hoạt động
- Số ca cấp cứu

**Danh sách chờ:**
- Hiển thị bệnh nhân đang chờ hoặc đang khám
- Cập nhật tự động mỗi 5 giây
- Màu badge: Đỏ (Cấp cứu), Vàng (Ưu tiên), Xanh (Thường)

### 4.2. Tab Quản lý Bệnh nhân (Tiếp đón)

**Form bên trái:**

| Field | Mô tả | Bắt buộc |
|-------|-------|----------|
| Họ tên | Tên bệnh nhân | ✅ |
| Giới tính | Nam/Nữ | ✅ |
| Ngày sinh | dd/mm/yyyy | ✅ |
| CCCD | 12 số | ✅ |
| SĐT | 10 số | ✅ |
| Nhóm máu | A+/A-/B+/B-/AB+/AB-/O+/O- | ✅ |
| BHYT | Checkbox | ❌ |
| Hình thức | Khám trực tiếp / Có đặt lịch | ✅ |
| Khoa | Chọn khoa khám | ✅ |
| Bác sĩ | Chọn bác sĩ (nếu đặt lịch) | ❌ |
| Ngày khám | Ngày hẹn (nếu đặt lịch) | ❌ |
| Giờ khám | Khung giờ (nếu đặt lịch) | ❌ |

**Bảng bên phải:**
- Danh sách tiếp đón trong ngày
- Trạng thái: ChoCheckIn (Đỏ), DangKham (Vàng), DaHoanThanh (Xanh)
- Nút Check-in: Chuyển sang xanh lá khi đã xếp hàng đợi

**Các chức năng:**
1. **Tạo bệnh nhân mới:** Điền form → Bấm "Tạo"
2. **Check-in:** Click nút ĐỎ → Chuyển Xanh Lá → BN vào queue
3. **Đặt lịch hẹn:** Chọn "Có đặt lịch" → Chọn BS/Ngày/Giờ

### 4.3. Tab Bác sĩ / Khoa / Phòng

**Danh sách khoa:**
- Hiển thị dạng card: Tên khoa, số bác sĩ, số phòng
- Click card → Xem chi tiết bác sĩ và phòng

**Chi tiết khoa:**
- Danh sách bác sĩ: Tên, học vị
- Danh sách phòng: Tên phòng, số BN chờ, tên bác sĩ trực

### 4.4. Tab Phòng Khám

**Danh sách phòng (dạng card):**
- Tên phòng
- Số BN đang chờ
- Khoa
- Bác sĩ trực

**Chi tiết phòng (click card):**

**Hàng đợi 3 cột:**
- Cột 1: Cấp cứu (mức 3) - Viền đỏ
- Cột 2: Ưu tiên (mức 2) - Viền vàng
- Cột 3: Thường (mức 1) - Viền xanh

**Bệnh nhân đang khám:**
- Tên BN
- Mã visit
- Số thứ tự

**Chức năng:**

1. **Gọi bệnh nhân tiếp:**
   - Bấm nút "Gọi bệnh nhân tiếp"
   - Hệ thống tự động chọn theo priority: 3 → 2 → 1
   - BN đầu tiên trong queue được gọi

2. **Chỉ định dịch vụ:**
   - Check các dịch vụ trong danh sách
   - Bấm "Chỉ định"
   - Dịch vụ được thêm vào lượt khám

3. **Kê đơn thuốc:**
   - Bấm "+" để thêm dòng thuốc
   - Nhập tên thuốc (gợi ý từ datalist)
   - Nhập số lượng
   - Bấm "Lưu đơn thuốc"
   - **Lưu ý:** Hệ thống tự động lấy medicineID từ datalist

4. **Chuyển khoa:**
   - Chọn khoa mới từ dropdown
   - Bấm "Chuyển khoa"
   - Hệ thống kiểm tra: không lặp khoa, không quá 3 khoa/ngày

5. **Hoàn tất khám:**
   - Bấm "Hoàn tất khám"
   - Nếu còn khoa tiếp theo → Tự động chuyển
   - Nếu hết khoa → Chuyển sang "Chờ thanh toán"

6. **Kích hoạt cấp cứu:**
   - Nhập mã Visit
   - Bấm "Kích hoạt"
   - BN được đẩy lên đầu hàng đợi cấp cứu

### 4.5. Tab Thu ngân & Kho Dược

**Chọn lượt khám:**
- Dropdown hiển thị các lượt khám chưa thanh toán
- Bấm "Tải" để xem chi tiết

**Chi tiết thanh toán:**

| Thông tin | Mô tả |
|-----------|-------|
| Tên BN | Họ tên bệnh nhân |
| Mã Visit | Mã lượt khám |
| Bác sĩ | Bác sĩ khám |
| Khoa | Khoa cuối cùng |
| BHYT | Ô nhập % giảm trừ (để trống = không giảm) |

**Bảng dịch vụ:**
- Tên dịch vụ
- Giá tiền
- Tổng dịch vụ (cuối bảng)

**Bảng thuốc:**
- Tên thuốc
- Số lượng
- Đơn giá (lấy từ Kho dược)
- Thành tiền
- Tổng thuốc (cuối bảng)

**Tổng thanh toán:**
- Tự động tính: (Tổng DV + Tổng thuốc) × (1 - BHYT/100)
- Cập nhật real-time khi thay đổi % BHYT

**Thanh toán:**
1. Kiểm tra thông tin
2. Bấm "Thanh toán"
3. Hệ thống:
   - Trừ thuốc trong kho (Two-Pass Validation)
   - Tạo hóa đơn
   - Đánh dấu "Đã thanh toán"
4. Hiển thị hóa đơn chi tiết

**In hóa đơn:**
- Bấm "In hóa đơn"
- Chỉ in phần hóa đơn (ẩn các phần khác)
- Có thể dùng Ctrl+P hoặc bấm nút In

### 4.6. Tab Cài đặt

**Lưu dữ liệu:**
- Bấm "Lưu dữ liệu"
- Tạo file `hospital_data.json`
- **Lưu ý:** Nên lưu trước khi tắt server

**Tải dữ liệu:**
- Chọn file JSON
- Bấm "Tải dữ liệu"
- Khôi phục toàn bộ trạng thái

**Sinh dữ liệu mẫu:**
- Bấm "Sinh dữ liệu mẫu"
- Tạo 5 bệnh nhân, 2 BS/khoa, 1-2 phòng/khoa, dịch vụ, thuốc
- **Cảnh báo:** Ghi đè dữ liệu hiện tại

---

## 5. Xử lý lỗi thường gặp

### 5.1. Lỗi server

| Lỗi | Nguyên nhân | Cách khắc phục |
|-----|-------------|----------------|
| "Không thể kết nối" | Server chưa chạy | Chạy `python app.py` |
| "Port 5000 đang được sử dụng" | Port bị chiếm | Tìm và tắt process đang dùng port 5000 |
| "Module not found" | Thiếu dependencies | Chạy `pip install -r requirements.txt` |

### 5.2. Lỗi chức năng

| Lỗi | Nguyên nhân | Cách khắc phục |
|-----|-------------|----------------|
| Check-in không xếp hàng đợi | BN đã ở trạng thái khác | Kiểm tra status trong bảng |
| Không gọi được BN | Phòng đang bận | Hoàn tất khám BN hiện tại |
| Tính tiền thuốc = 0 | Gửi sai medicineID | Chọn thuốc từ datalist |
| Không chuyển được khoa | Đã khám khoa này hoặc >3 khoa | Chọn khoa khác |
| Không thanh toán được | Thuốc không đủ trong kho | Kiểm tra tồn kho |
| BHYT không áp dụng | BN không có BHYT hoặc nhập sai % | Kiểm tra checkbox BHYT lúc tạo BN |

### 5.3. Lỗi ngrok

| Lỗi | Nguyên nhân | Cách khắc phục |
|-----|-------------|----------------|
| "ERR_NGROK_3200" | Server Flask tắt | Khởi động lại `python app.py` |
| "ERR_NGROK_8012" | Ngrok không kết nối được localhost | Kiểm tra server đang chạy |
| "ERR_NGROK_4018" | Chưa cấu hình authtoken | Chạy `ngrok authtoken TOKEN` |

---

## 6. Lưu ý quan trọng

### 6.1. Dữ liệu

- **Hệ thống lưu trữ In-Memory:** Dữ liệu chỉ tồn tại trong RAM
- **Mất dữ liệu khi tắt server:** Nhớ bấm "Lưu dữ liệu" trước khi tắt
- **Không có database thực:** Mọi thao tác đều trên hash tables (dict)
- **Giới hạn:** Tối đa 3 khoa/ngày cho 1 bệnh nhân

### 6.2. Bảo mật

- **Không có xác thực:** Hệ thống mở, không cần đăng nhập
- **Không phù hợp production:** Chỉ dùng cho demo/mô phỏng
- **Dữ liệu mẫu:** Không dùng thông tin thật

### 6.3. Hiệu năng

- **Tối ưu cho < 10,000 records:** Thời gian phản hồi < 0.1s
- **Auto-refresh:** Mỗi tab tự động cập nhật sau 5 giây
- **Concurrent:** Thiết kế single-user, không hỗ trợ nhiều user đồng thời

### 6.4. BHYT

- **Tùy chỉnh %:** Nhập số bất kỳ từ 0-100
- **Để trống:** Không áp dụng giảm trừ
- **Áp dụng:** Chỉ khi bệnh nhân có BHYT (checkbox lúc tạo BN)
- **Công thức:** `Tổng = (DV + Thuốc) × (1 - BHYT%)`

### 6.5. Mã hóa đơn và visit

- **Mã tự động sinh:** `BILL_timestamp_random` hoặc `VISIT_timestamp_random`
- **Không thể chỉnh sửa sau thanh toán:** Hóa đơn đã thanh toán không sửa được
- **Giữ lại trong DB:** Lịch sử khám vẫn lưu để tra cứu

---

## Phụ lục

### A. Danh sách API endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/dashboard` | Thống kê tổng quan |
| GET | `/api/patients` | Danh sách bệnh nhân |
| POST | `/api/patients` | Tạo bệnh nhân mới |
| POST | `/api/checkin` | Check-in bệnh nhân |
| POST | `/api/confirm-checkin/<id>` | Xác nhận check-in |
| POST | `/api/emergency` | Kích hoạt cấp cứu |
| GET | `/api/departments` | Danh sách khoa |
| GET | `/api/departments/<id>/doctors` | Bác sĩ theo khoa |
| GET | `/api/departments/<id>/rooms` | Phòng theo khoa |
| GET | `/api/rooms` | Danh sách phòng |
| GET | `/api/rooms/<id>/queue` | Queue của phòng |
| GET | `/api/rooms/<id>/services` | Dịch vụ theo phòng |
| POST | `/api/call-next` | Gọi bệnh nhân tiếp |
| POST | `/api/add-service` | Thêm dịch vụ |
| POST | `/api/add-prescription` | Kê đơn thuốc |
| POST | `/api/transfer` | Chuyển khoa |
| POST | `/api/complete` | Hoàn tất khám |
| GET | `/api/active-visits` | Lượt khám đang hoạt động |
| GET | `/api/payment-detail/<id>` | Chi tiết thanh toán |
| POST | `/api/pay` | Thanh toán |
| POST | `/api/save` | Lưu dữ liệu JSON |
| POST | `/api/load` | Tải dữ liệu JSON |
| POST | `/api/mock` | Sinh dữ liệu mẫu |

### B. Các thuật toán cốt lõi

| Thuật toán | Mô tả | Độ phức tạp |
|------------|-------|-------------|
| Strict Priority Scheduling | Gọi số theo ưu tiên 3→2→1 | O(1) |
| Shortest Queue First | Chọn phòng có queue ngắn nhất | O(n) |
| Two-Pass Validation | Kiểm tra kho 2 bước (Read/Write) | O(m) |
| Cycle Detection | Phát hiện chu trình khoa | O(1) |
| Bill Calculation | Tính tiền + BHYT | O(n) |

---

*Hướng dẫn này được cập nhật cho phiên bản v2.3*  
*Mọi thắc mắc vui lòng liên hệ nhóm phát triển*
