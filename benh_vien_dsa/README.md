# ĐỒ ÁN MÔN HỌC: CẤU TRÚC DỮ LIỆU & THUẬT TOÁN (DSA)

## Đề tài: Hệ Thống Quản Lý Đặt Lịch Khám Trước và Điều Phối Hàng Đợi Khám Bệnh Tại Bệnh Viện

**Ngôn ngữ lập trình:** Python 3.11+  
**Mô hình lưu trữ:** In-Memory Hash Tables (dict) — mô phỏng không dùng Database thực  
**Giao diện:** Web Dashboard (Flask + HTML/CSS/JS)  

---

## Mục Lục

1. [Tổng quan hệ thống](#1-tổng-quan-hệ-thống)
2. [Kiến trúc lưu trữ toàn cục](#2-kiến-trúc-lưu-trữ-toàn-cục)
3. [Sơ đồ lớp & Cấu trúc dữ liệu cốt lõi](#3-sơ-đồ-lớp--cấu-trúc-dữ-liệu-cốt-lõi)
4. [Các cấu trúc dữ liệu sử dụng](#4-các-cấu-trúc-dữ-liệu-sử-dụng)
5. [Các thuật toán cốt lõi](#5-các-thuật-toán-cốt-lõi)
6. [Quy trình luồng dữ liệu (Workflow)](#6-quy-trình-luồng-dữ-liệu-workflow)
7. [Giao diện Web Dashboard](#7-giao-diện-web-dashboard)
8. [Class Diagram & Chi tiết đối tượng](#8-class-diagram--chi-tiết-đối-tượng)
9. [Kết quả kiểm thử (Unit Tests)](#9-kết-quả-kiểm-thử-unit-tests)
10. [Kết quả đánh giá hiệu năng (Performance Benchmark)](#10-kết-quả-đánh-giá-hiệu-năng-performance-benchmark)
11. [Hướng dẫn cài đặt & Deploy Local](#11-hướng-dẫn-cài-đặt--deploy-local)
12. [Hướng dẫn test giao diện](#12-hướng-dẫn-test-giao-diện)
13. [Cấu trúc thư mục dự án](#13-cấu-trúc-thư-mục-dự-án)
14. [Các chức năng đã cập nhật](#14-các-chức-năng-đã-cập-nhật)

---

## 1. Tổng quan hệ thống

### 1.1. Mục tiêu
Xây dựng ứng dụng mô phỏng hệ thống **Đặt lịch khám trước** và **Điều phối hàng đợi khám bệnh** tại bệnh viện. Hệ thống tối ưu hóa quy trình tiếp nhận bệnh nhân, tự động sắp xếp thứ tự vào phòng khám, giảm thiểu thời gian chờ đợi và xử lý kịp thời các ca cấp cứu.

### 1.2. Các thực thể chính
| Đối tượng | Thông tin quản lý chính |
|-----------|------------------------|
| **Bệnh nhân** | Mã BN, Họ tên, Giới tính, Ngày sinh, CCCD, SĐT, Email, Địa chỉ, Nhóm máu, BHYT |
| **Bác sĩ** | Mã BS, Họ tên, Giới tính, Ngày sinh, SĐT, Email, Chuyên khoa, Học vị, Số CCHN, Kinh nghiệm |
| **Khoa** | Mã khoa, Tên khoa, Danh sách bác sĩ, Danh sách phòng, Danh sách dịch vụ |
| **Phòng khám** | Mã phòng, Mã khoa, Mã bác sĩ, Hàng đợi đa mức, Bệnh nhân đang khám |
| **Dịch vụ** | Mã DV, Tên DV, Khoa phụ trách, Giá tiền |
| **Thuốc** | Mã thuốc, Tên thuốc, Đơn giá, Tồn kho |
| **Lịch hẹn** | Mã lịch, Mã BN, Chuỗi khoa, Mã BS, Ngày khám, Khung giờ |

### 1.3. Cơ chế ưu tiên hàng đợi (3 mức)
| Mức | Đối tượng | Quy tắc |
|-----|-----------|---------|
| **3 (Cao nhất)** | Cấp cứu / Nguy kịch | Cắt đuôi toàn bộ hàng đợi, đưa vào khám ngay lập tức |
| **2 (Trung bình)** | Đã đặt lịch trước | Chỉ ưu tiên đúng khung giờ đăng ký, có STT riêng |
| **1 (Thấp nhất)** | Khám bình thường (Vãng lai) | STT theo ngày, khám sau khi giải quyết xong mức 3 và 2 |

---

## 2. Kiến trúc lưu trữ toàn cục

Hệ thống sử dụng **Bảng băm (Hash Table / dict)** làm kho lưu trữ trung tâm, đảm bảo thời gian truy xuất **O(1)**.

```python
# Kho lưu trữ toàn cục (Singleton ở mức module)
global_patients      = {}   # Key: patientID      -> Value: Patient Object
global_doctors       = {}   # Key: doctorID       -> Value: Doctor Object
global_departments   = {}   # Key: departmentID   -> Value: Department Object
global_services      = {}   # Key: serviceID      -> Value: Service Object
global_inventory     = {}   # Key: medicineID     -> Value: Medicine Object
global_appointments  = {}   # Key: (doctorID, date, timeSlot) -> List[Appointment]
global_visits        = {}   # Key: visitID        -> Value: Visit Object
global_rooms         = {}   # Key: roomID         -> Value: Room Object
global_prescriptions = {}   # Key: prescriptionID -> Value: Prescription Object
global_bills         = {}   # Key: billID         -> Value: Bill Object
```

---

## 3. Sơ đồ lớp & Cấu trúc dữ liệu cốt lõi

### Mapping Class -> Cấu trúc dữ liệu

| Class | Cấu trúc dữ liệu cốt lõi | Vai trò |
|-------|--------------------------|---------|
| **Room** | `MultiLevelQueue` (dict + 3 `collections.deque`) | Thuật toán xếp hàng ưu tiên nghiêm ngặt |
| **Department** | `list` chứa các `roomID` | Thuật toán cân bằng tải SQF |
| **Appointment** | `dict` kiểm tra dung lượng Slot (`len(slot_list) < 4`) | Quản lý đặt lịch |
| **Visit** | `set` cho `visited_departments` (Cycle Detection **O(1)**); `list` cho `usedServiceIDs` | Phiên khám bệnh, lịch sử dịch vụ |
| **Prescription** | `dict` (`medicineList`) | Danh sách thuốc kê đơn |
| **Bill** | Tổng hợp **O(N)** từ `usedServiceIDs` và `Prescription` | Thanh toán viện phí |

---

## 4. Các cấu trúc dữ liệu sử dụng

### 4.1. Hàng Đợi Ưu Tiên Đa Cấp (MultiLevelQueue)
**Cài đặt:** `collections.deque` kết hợp `dict`

```python
self.queues = {
    3: deque(),  # Cấp cứu
    2: deque(),  # Đặt lịch
    1: deque()   # Vãng lai
}
```

### 4.2. Bảng Băm (Hash Table / dict)
- **Quản lý Slot đặt lịch:** Key = `(doctorID, ngày, khung_giờ)` → Value = `list` (tối đa 4 BN)
- **Kho thuốc:** Key = `medicineID` → Value = `stockQuantity`

### 4.3. Tập Hợp Băm (Hash Set / set)
**Ứng dụng:** Chặn vòng lặp luân chuyển liên khoa
```python
visited_departments = set()  # O(1) kiểm tra tồn tại
```

---

## 5. Các thuật toán cốt lõi

### 5.1. Strict Priority Scheduling (O(1))
Gọi bệnh nhân theo thứ tự: Mức 3 → Mức 2 → Mức 1

### 5.2. Shortest Queue First - SQF (O(K))
Cân bằng tải phòng khám theo số người chờ ít nhất

### 5.3. Two-Pass Validation (O(M))
Xuất kho thuốc: Kiểm tra toàn bộ đơn trước khi trừ kho (All-or-Nothing)

### 5.4. Cycle Detection (O(1))
Chặn bệnh nhân khám trùng khoa trong cùng ngày bằng Set

---

## 6. Quy trình luồng dữ liệu (Workflow)

### 5 bước thực thi:
1. **Boot & Mock Data** - Tạo 5-9 khoa, 1-2 phòng/khoa, 2 bác sĩ/khoa
2. **Đăng ký** (Lễ tân) - Check-in, xác định ưu tiên, SQF xếp phòng
3. **Bác sĩ khám** - Priority Queue rút BN, thêm dịch vụ, chuyển khoa (Cycle Detection)
4. **Cấp cứu** - `emergencyPreempt` đẩy BN lên đầu queue
5. **Thanh toán** - Two-Pass Validation, tính Bill, xuất viện

---

## 7. Giao diện Web Dashboard

### 7.1. Tổng quan
Hệ thống có **7 tab chức năng** trong sidebar:

| Tab | Icon | Chức năng chính |
|-----|------|-----------------|
| **Dashboard** | 📊 | Thống kê real-time, bảng chờ khám |
| **Bệnh nhân** | 👤 | Thêm/Sửa/Xóa BN, danh sách BN |
| **Bác sĩ / Khoa** | 🏥 | Xem khoa → bác sĩ → phòng, số người chờ |
| **Lễ tân** | 📝 | Đặt lịch online, Check-in vãng lai, Cấp cứu |
| **Phòng Khám** | 🩺 | Bảng điện tử 3 queue, Gọi BN, Chỉ định DV, Kê đơn |
| **Thu ngân & Kho** | 💰 | Dropdown chọn visit, tính tiền, BHYT, xuất hóa đơn |
| **Cài đặt** | ⚙️ | Save/Load JSON, Mock data |

### 7.2. Tính năng nổi bật
- **Auto-refresh** 5 giây: Dashboard, Phòng Khám, Thu ngân
- **Toast notifications**: Thông báo thành công/lỗi/cảnh báo
- **Loading spinner**: Khi gọi API
- **Responsive design**: Sidebar + Main content
- **Priority badges**: Màu đỏ (Cấp cứu), vàng (Ưu tiên), xanh (Thường)

---

## 8. Class Diagram & Chi tiết đối tượng

### 10 Class chính
- **Patient** (Bệnh nhân): patientID, fullName, gender, dob, citizenID, phone, hasInsurance
- **Visit** (Lần khám): visitID, patientID, queuePriority, status, departmentSequence, usedServiceIDs
- **Doctor** (Bác sĩ): doctorID, fullName, departmentID, degree, yearsExperience
- **Department** (Khoa): departmentID, departmentName, doctorIDs, roomIDs, serviceIDs
- **Room** (Phòng): roomID, departmentID, doctorID, queues (MultiLevelQueue), currentVisitID
- **Service** (Dịch vụ): serviceID, serviceName, departmentID, price
- **Medicine** (Thuốc): medicineID, medicineName, unitPrice, stockQuantity
- **Prescription** (Toa thuốc): prescriptionID, visitID, medicineList
- **Bill** (Hóa đơn): billID, visitID, serviceCost, medicineCost, insuranceDiscount, finalTotal
- **Appointment** (Lịch hẹn): appointmentID, patientID, departmentSequence, selectedDoctorID

---

## 9. Kết quả kiểm thử (Unit Tests)

```bash
python -m unittest benh_vien_dsa.tests -v
```

**Kết quả:** `Ran 16 tests in 0.002s — OK`

| STT | Test Case | Kết quả |
|-----|-----------|---------|
| 1 | Priority Queue operations (3→2→1) | ✅ Pass |
| 2 | Strict Priority call next empty room | ✅ Pass |
| 3 | SQF assign shortest queue | ✅ Pass |
| 4 | Cycle detection blocks duplicate | ✅ Pass |
| 5 | Cycle detection max 3 departments | ✅ Pass |
| 6 | Two-Pass Validation success | ✅ Pass |
| 7 | Two-Pass Validation failure | ✅ Pass |
| 8 | Emergency preempt | ✅ Pass |
| 9 | Bill with insurance (80% off) | ✅ Pass |
| 10 | Bill without insurance | ✅ Pass |
| 11 | Slot limit blocks 5th patient | ✅ Pass |
| 12 | Reception checkin walkin (priority=1) | ✅ Pass |
| 13 | Reception checkin appointment (priority=2) | ✅ Pass |
| 14 | Doctor complete calls next | ✅ Pass |
| 15 | Persistence save/load JSON | ✅ Pass |
| 16 | Transfer department valid | ✅ Pass |

---

## 10. Kết quả đánh giá hiệu năng (Performance Benchmark)

```bash
python -m benh_vien_dsa.performance_test
```

| Thao tác | 10.000 | 50.000 | 100.000 | Độ phức tạp |
|----------|--------|--------|---------|-------------|
| Tìm kiếm ID (dict) | 0.0004s | 0.0006s | 0.0012s | **O(1)** ✅ |
| Priority Queue | 0.0049s | 0.0257s | — | **O(1)** ✅ |
| Cycle Detection | 0.0059s | 0.0295s | 0.0702s | **O(1)** ✅ |
| Two-Pass Validation | 0.0173s | 0.0902s | 0.1985s | **O(M)** ✅ |
| Save/Load JSON | 0.16s | 1.05s | 1.35s | I/O bound |

---

## 11. Hướng dẫn cài đặt & Deploy Local

### 11.1. Yêu cầu
- Python 3.11 hoặc cao hơn
- Không cần cài thêm thư viện ngoài (chỉ dùng Standard Library + Flask)

### 11.2. Cài đặt Flask
```bash
pip install flask
```

### 11.3. Khởi chạy server
```bash
# 1. Vào thư mục project
cd "D:\cautrucdulieu cho ny"

# 2. Khởi chạy server
python app.py
```

Server sẽ chạy tại:
- **http://127.0.0.1:5000** (localhost)
- **http://192.168.1.xxx:5000** (trong mạng LAN)

Tự động khởi tạo **5 bệnh nhân, 10 bác sĩ, 5 khoa, 7 phòng, 15 dịch vụ, 10 thuốc** sẵn để demo.

### 11.4. Lưu ý quan trọng
- **Đừng tắt terminal** đang chạy `python app.py` (server sẽ tắt)
- Nếu thay đổi code, server tự động reload (Flask debug mode)
- Xóa cache browser: `Ctrl+Shift+R` (Windows/Linux) hoặc `Cmd+Shift+R` (Mac)

### 11.5. Các lệnh hữu ích
```bash
# Chạy Unit Tests
python -m unittest benh_vien_dsa.tests -v

# Chạy Performance Benchmark
python -m benh_vien_dsa.performance_test

# Chạy sinh dữ liệu mẫu lớn (10.000+ bản ghi)
python -c "from benh_vien_dsa.mock_generator import init_mock_data_large; init_mock_data_large()"
```

---

## 12. Hướng dẫn test giao diện

### Test 1: Dashboard
1. Mở `http://127.0.0.1:5000`
2. Tab **Dashboard** hiện số liệu: BN, BS, phòng, lượt khám chờ
3. ✅ Đợi 5 giây, số liệu tự refresh

### Test 2: Thêm bệnh nhân
1. Tab **Bệnh nhân**
2. Điền form: Họ tên, Giới tính, Ngày sinh, SĐT, Nhóm máu
3. ✅ Bấm **"Lưu bệnh nhân"** → Toast xanh + bảng thêm dòng mới

### Test 3: Check-in + Phòng Khám (Flow chính)
1. Tab **Lễ tân** → Form Check-in
   - Chọn BN hoặc nhập thông tin mới
   - Chọn khoa (vd: Nội tổng quát)
   - Chọn mức ưu tiên: **Thường / Ưu tiên / Cấp cứu**
   - ✅ Bấm **Check-in** → Toast thành công

2. Tab **Phòng Khám**
   - Dropdown chọn phòng của khoa đã check-in
   - ✅ Hiện **3 cột queue** (Cấp cứu đỏ, Ưu tiên vàng, Thường xanh)
   - ✅ BN hiện trong queue với **tên + mã BN + badge ưu tiên**
   - Bấm **"Gọi tiếp"**
   - ✅ BN chuyển sang box **"Đang khám"** (nền xanh, chữ trắng)

3. Chỉ định dịch vụ
   - Trong box "Đang khám" → tick chọn dịch vụ
   - Bấm **"Lưu chỉ định"**

4. Hoàn tất khám
   - Bấm **"Hoàn tất khám"**
   - ✅ Box biến mất, hiện lại "Phòng đang rảnh"

### Test 4: Thu ngân (Thanh toán)
1. Tab **Thu ngân & Kho**
   - Dropdown tự động hiện BN vừa khám xong
   - Chọn BN → Bấm **"Tải"**
   - ✅ Hiện: Tên BN, Bác sĩ, Khoa, Dịch vụ đã dùng, Tiền thuốc
   - ✅ BHYT tự động: Có BHYT → giảm 80%, Không → 0%
   - Bấm **"Thanh toán"**
   - ✅ Toast thành công + Xuất hóa đơn

### Test 5: Cấp cứu (Emergency)
1. Tab **Lễ tân** → Check-in với mức **"Cấp cứu"**
2. Tab **Phòng Khám** → Chọn phòng
3. ✅ BN hiện trong cột **Cấp cứu** (border đỏ, badge đỏ)
4. Bấm **"Gọi tiếp"**
5. ✅ BN được gọi **ngay lập tức** (ưu tiên cao nhất)

### Test 6: Mock Data
1. Tab **Cài đặt**
2. Bấm **"Sinh dữ liệu mẫu"**
3. ✅ Toast thành công, dữ liệu demo được tạo

---

## 13. Cấu trúc thư mục dự án

```
benh_vien_dsa/
├── __init__.py              # Package initializer
├── config.py                # Hằng số, Enum, danh sách khoa
├── data_structures.py       # MultiLevelQueue (3 deque)
├── global_state.py          # 10 dict toàn cục (Singleton module)
├── models.py                # 10 Class: Patient, Visit, Doctor, ... (có to_dict/from_dict)
├── algorithms.py            # Strict Priority, SQF, Two-Pass, Cycle Detection
├── services.py              # ReceptionService, DoctorService, PharmacyService
├── persistence.py           # saveData() / loadData() JSON
├── mock_generator.py        # Sinh dữ liệu mẫu 10.000+ bản ghi
├── tests.py                 # 16 Unit Test Cases
├── performance_test.py      # Benchmark 10k/50k/100k records
├── README.md                # Tài liệu hệ thống (file này)

# Web Frontend
app.py                       # Flask API backend (25+ REST endpoints)
templates/
└── index.html               # SPA giao diện đẹp, 7 tabs
static/
├── css/
│   └── style.css            # Medical-grade responsive design
└── js/
    └── app.js               # Vanilla JS SPA logic
```

---

## 14. Các chức năng đã cập nhật

### Web Dashboard (Mới)
- ✅ Giao diện web đẹp, chuyên nghiệp (thay cho CLI cũ)
- ✅ 7 tab chức năng với sidebar navigation
- ✅ Real-time auto-refresh (5 giây) cho Dashboard, Phòng Khám, Thu ngân
- ✅ Toast notifications (success/error/warning)
- ✅ Loading spinner khi gọi API
- ✅ Responsive design

### Phòng Khám
- ✅ Hiển thị 3 cột queue: Cấp cứu (đỏ), Hẹn trước (vàng), Vãng lai (xanh)
- ✅ Queue item hiển thị: **Tên BN + Mã BN + Mã Visit + Badge ưu tiên + Badge STT**
- ✅ Border màu theo ưu tiên, hover effect
- ✅ Box "Đang khám" nền xanh gradient, chữ trắng, cards trong suốt
- ✅ Chỉ định dịch vụ (multi-select checkbox)
- ✅ Kê đơn thuốc (dynamic form)
- ✅ Chuyển khoa + Hoàn tất khám

### Thu ngân (Hoàn toàn mới)
- ✅ **Dropdown chọn visit** (không cần gõ tay)
- ✅ Auto-refresh danh sách visit chưa thanh toán
- ✅ Hiển thị đầy đủ: Tên BN, Bác sĩ, Khoa, Dịch vụ, Thuốc
- ✅ **BHYT tự động**: Có BHYT → giảm 80%, Không → 0%
- ✅ Tính tổng tiền real-time
- ✅ Xuất hóa đơn đẹp (invoice)

### API Backend
- ✅ `/api/payment-detail/<visit_id>` - Trả thông tin đầy đủ để thanh toán
- ✅ `/api/active-visits` - Danh sách visit chưa thanh toán cho dropdown
- ✅ `/api/rooms/<id>/queue` - Trả visit objects với patientName, priorityLabel

### Bug Fixes
- ✅ Fix CSS `!important` conflict (dùng classList thay vì style.display)
- ✅ Fix JS API keys (snake_case từ backend)
- ✅ Fix room queue display (undefined roomId guard)
- ✅ Fix severity nhận cả số và text ("3", "NguyKich")
- ✅ Fix JS syntax error (stray code block)

---

*Đồ án môn Cấu trúc Dữ liệu & Thuật toán (DSA)*
*Cập nhật: 24/05/2026*
