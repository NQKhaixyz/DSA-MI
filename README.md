# ĐỒ ÁN MÔN HỌC: CẤU TRÚC DỮ LIỆU & THUẬT TOÁN (DSA)

## Đề tài: Hệ Thống Quản Lý Bệnh Viện MediCare Pro

**Ngôn ngữ lập trình:** Python 3.11+  
**Mô hình lưu trữ:** In-Memory Hash Tables (dict) — mô phỏng không dùng Database thực  
**Giao diện:** Web Dashboard (Flask + HTML/CSS/JS)  
**GitHub:** [NQKhaixyz/DSA-MI](https://github.com/NQKhaixyz/DSA-MI)

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
10. [Kết quả đánh giá hiệu năng](#10-kết-quả-đánh-giá-hiệu-năng)
11. [Hướng dẫn cài đặt & Deploy Local](#11-hướng-dẫn-cài-đặt--deploy-local)
12. [Hướng dẫn test giao diện](#12-hướng-dẫn-test-giao-diện)
13. [Cấu trúc thư mục dự án](#13-cấu-trúc-thư-mục-dự-án)
14. [Changelog - Các chức năng đã cập nhật](#14-changelog---các-chức-năng-đã-cập-nhật)

---

## 1. Tổng quan hệ thống

### 1.1. Mục tiêu
Xây dựng ứng dụng mô phỏng hệ thống **Quản lý bệnh viện** với các chức năng: Tiếp đón bệnh nhân, Điều phối hàng đợi khám bệnh, Chỉ định dịch vụ, Kê đơn thuốc, Thanh toán viện phí. Hệ thống tối ưu hóa quy trình tiếp nhận, tự động sắp xếp thứ tự vào phòng khám, giảm thiểu thời gian chờ đợi và xử lý kịp thời các ca cấp cứu.

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
| **Lượt khám** | Mã visit, Mã BN, Trạng thái, Chuỗi khoa, Dịch vụ đã dùng, Đơn thuốc |

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

### 6.1. Quy trình tiếp đón bệnh nhân mới (Đã cập nhật)
1. **Tab "Quản lý Bệnh nhân"** → Form bên trái
2. Chọn **"Hình thức tiếp đón"**:
   - *Khám trực tiếp:* Chọn Khoa khám
   - *Có đặt lịch trước:* Chọn Bác sĩ, Ngày, Giờ khám
3. Bấm **"Lưu & Tiếp đón"** → Tạo Visit (status = `ChoCheckIn`)
4. Bảng bên phải hiện BN mới với nút **Check-in màu ĐỎ**
5. Click nút ĐỎ → Chuyển Xanh Lá (status = `DangKham`) → Tự động xếp vào hàng đợi phòng khám

### 6.2. Quy trình khám bệnh (Đã cập nhật)
1. **Tab "Phòng Khám"** → Danh sách phòng dạng Card (hiển thị số BN chờ)
2. Click phòng → Mở chi tiết
3. Bấm **"Gọi tiếp"** → BN vào khám
4. **Chỉ định dịch vụ:** Chỉ hiển thị dịch vụ thuộc đúng Khoa của phòng (Fix bug hiển thị full)
5. **Kê đơn thuốc:** Chọn thuốc từ Kho dược
6. Bấm **"Hoàn tất khám"** → Chuyển sang `ChoThanhToan`

### 6.3. Quy trình thanh toán (Đã cập nhật)
1. **Tab "Thu ngân & Kho"** → Chọn Visit từ dropdown
2. Hệ thống tính:
   - **Tiền dịch vụ** = Tổng giá các dịch vụ đã dùng
   - **Tiền thuốc** = Σ (Số lượng × Đơn giá từ Kho dược)
   - **BHYT** = Giảm 80% nếu có BHYT
3. Bấm **"Thanh toán"** → Status = `DaHoanThanh` (Giữ nguyên trong DB, không xóa)

---

## 7. Giao diện Web Dashboard

### 7.1. Tổng quan
Hệ thống có **6 tab chức năng** trong sidebar:

| Tab | Icon | Chức năng chính |
|-----|------|-----------------|
| **Dashboard** | 📊 | Thống kê real-time, bảng chờ khám |
| **Quản lý Bệnh nhân** | 👤 | Form tiếp đón + Bảng danh sách tiếp đón trong ngày + Nút Check-in |
| **Bác sĩ / Khoa / Phòng** | 🏥 | Xem khoa → bác sĩ → phòng, số người chờ |
| **Phòng Khám** | 🩺 | Danh sách phòng (Card + Badge số BN chờ), Chi tiết phòng: 3 queue, Gọi BN, Chỉ định DV, Kê đơn |
| **Thu ngân & Kho** | 💰 | Dropdown chọn visit, tính tiền dịch vụ + thuốc, BHYT, xuất hóa đơn |
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
- **Visit** (Lần khám): visitID, patientID, queuePriority, status, departmentSequence, usedServiceIDs, appointmentID
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

## 10. Kết quả đánh giá hiệu năng

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
- pip install flask

### 11.2. Cài đặt
```bash
# Clone repo
git clone https://github.com/NQKhaixyz/DSA-MI.git
cd DSA-MI

# Cài đặt dependencies
pip install -r requirements.txt
```

### 11.3. Khởi chạy server
```bash
# Khởi chạy server
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

### Test 2: Quản lý Bệnh nhân (Tab mới - Gộp Lễ tân + Bệnh nhân)
1. Tab **Quản lý Bệnh nhân**
2. **Form bên trái** — Thêm bệnh nhân mới:
   - Điền: Họ tên, Giới tính, Ngày sinh, SĐT, Nhóm máu
   - Chọn **"Hình thức tiếp đón"**:
     - *Khám trực tiếp* → Chọn Khoa
     - *Có đặt lịch trước* → Chọn Bác sĩ, Ngày, Giờ
   - ✅ Bấm **"Lưu & Tiếp đón"** → Toast xanh
3. **Bảng bên phải** — Danh sách tiếp đón trong ngày:
   - ✅ Hiện BN mới với nút **Check-in màu ĐỎ**
   - Click nút ĐỎ → Chuyển **Xanh Lá** + Toast "Đã xếp vào hàng đợi"

### Test 3: Phòng Khám (Đã cập nhật - Overview Card)
1. Tab **Phòng Khám**
2. ✅ Hiện danh sách phòng dạng **Card** — mỗi card có **Badge số BN đang chờ**
3. Click phòng → Mở chi tiết:
   - ✅ Hiện **3 cột queue** (Cấp cứu đỏ, Ưu tiên vàng, Thường xanh)
   - Bấm **"Gọi tiếp"** → BN chuyển sang box **"Đang khám"**
4. **Chỉ định dịch vụ** (Fix bug filter):
   - ✅ Chỉ hiện dịch vụ thuộc đúng **Khoa của phòng** (không hiện full toàn viện)
   - Tick 2 dịch vụ → Bấm **"Lưu chỉ định"**
5. **Kê đơn thuốc** (Fix bug tính tiền = 0đ):
   - Chọn thuốc từ datalist (không gõ tay)
   - Nhập số lượng
   - Bấm **"Lưu đơn"**
6. **Hoàn tất khám** → Bấm **"Hoàn tất khám"** → Status = `ChoThanhToan`

### Test 4: Thu ngân (Đã cập nhật - Fix tính tiền)
1. Tab **Thu ngân & Kho**
2. Dropdown chọn BN vừa hoàn tất (status = `ChoThanhToan`)
3. Bấm **"Tải"**
4. ✅ Hiện chi tiết:
   - **Dịch vụ:** Tên + Giá từng dịch vụ đã chọn
   - **Thuốc:** Tên + SL + Đơn giá (từ Kho dược) + Thành tiền
   - **Tổng:** Tổng dịch vụ + Tổng thuốc - BHYT
   - ✅ **Không còn bị 0đ** (Fix bug lấy giá thuốc từ inventory)
5. Điều chỉnh **BHYT %** nếu cần
6. Bấm **"Thanh toán"** → Toast thành công + Xuất hóa đơn
7. ✅ BN vẫn giữ trong DB (không xóa), status = `DaHoanThanh`

### Test 5: Cấp cứu (Emergency)
1. Tab **Quản lý Bệnh nhân** → Check-in với mức **"Cấp cứu"** (priority=3)
2. Tab **Phòng Khám** → BN hiện trong cột **Cấp cứu** (border đỏ)
3. Bấm **"Gọi tiếp"** → ✅ BN được gọi **ngay lập tức** (ưu tiên cao nhất)

### Test 6: Mock Data
1. Tab **Cài đặt**
2. Bấm **"Sinh dữ liệu mẫu"**
3. ✅ Toast thành công, dữ liệu demo được tạo

---

## 13. Cấu trúc thư mục dự án

```
DSA-MI/
├── app.py                       # Flask API backend (30+ REST endpoints)
├── requirements.txt             # Dependencies: Flask, gunicorn
├── README.md                    # Tài liệu hệ thống (file này)
├── .gitignore                   # Git ignore rules
│
├── benh_vien_dsa/               # Core business logic package
│   ├── __init__.py              # Package initializer
│   ├── config.py                # Hằng số, Enum, danh sách khoa, Status codes
│   ├── data_structures.py       # MultiLevelQueue (3 deque)
│   ├── global_state.py          # 10 dict toàn cục (Singleton module)
│   ├── models.py                # 10 Class: Patient, Visit, Doctor, ... (có to_dict/from_dict)
│   ├── algorithms.py            # Strict Priority, SQF, Two-Pass, Cycle Detection, calculate_bill
│   ├── services.py              # ReceptionService, DoctorService, PharmacyService
│   ├── persistence.py           # saveData() / loadData() JSON
│   ├── mock_generator.py        # Sinh dữ liệu mẫu 10.000+ bản ghi
│   ├── tests.py                 # 16 Unit Test Cases
│   ├── performance_test.py      # Benchmark 10k/50k/100k records
│   ├── main.py                  # CLI entry point
│   └── cli.py                   # Interactive CLI commands
│
├── templates/                   # Flask Jinja2 templates
│   └── index.html               # SPA giao diện đẹp, 6 tabs
│
├── static/                      # Static assets
│   ├── css/
│   │   └── style.css            # Medical-grade responsive design
│   └── js/
│       └── app.js               # Vanilla JS SPA logic
│
└── .git/                        # Git repository
```

---

## 14. Changelog - Các chức năng đã cập nhật

### v2.3 - Insurance & Room Assignment Fixes (13/06/2026)

#### ✅ Fix BHYT: Tùy chỉnh % giảm trừ tại chỗ
- **Bug:** % BHYT cố định 80%, không thay đổi được
- **Fix:** Thêm tham số `insurance_discount_percent` trong `calculate_bill()` và `process_payment()`
- **Frontend:** Ô input BHYT để trống (không mặc định), người dùng tự nhập % muốn giảm
- **Backend:** Áp dụng đúng % giảm trừ từ request

#### ✅ Fix 1 phòng chỉ có 1 bác sĩ trực
- **Bug:** `random.choice()` có thể chọn cùng 1 bác sĩ cho nhiều phòng trong cùng khoa
- **Fix:** Thêm `assigned_docs` set trong `generate_rooms()` và `init_mock_data_small()` để đảm bảo mỗi phòng trong cùng khoa có bác sĩ khác nhau
- **Fallback:** Tự động tạo bác sĩ mới nếu hết bác sĩ chưa được gán

#### ✅ Thêm chức năng In hóa đơn
- **Thêm:** Nút "In hóa đơn" sau khi thanh toán thành công
- **Chức năng:** In chỉ phần hóa đơn (ẩn các phần khác của trang)

#### ✅ Cập nhật hiển thị hóa đơn
- **Thêm:** Tổng chi phí gốc (trước giảm)
- **Thêm:** Giảm trừ BHYT (số tiền cụ thể)
- **Thêm:** Trạng thái "Đã thanh toán" (badge xanh)
- **Thêm:** Chi phí dịch vụ và chi phí thuốc riêng biệt

#### ✅ Fix truyền BHYT từ check-in
- **Bug:** `hasInsurance` không được truyền từ frontend xuống backend khi tạo bệnh nhân
- **Fix:** Cập nhật `checkin_patient()` nhận tham số `has_insurance`, truyền vào `Patient`

---

### v2.2 - Bug Fixes & UI Polish (26/05/2026)

#### ✅ Fix Dashboard hiển thị sai số liệu
- **Bug:** Bệnh nhân đã check-in, thanh toán xong vẫn hiển thị trong "Lượt khám đang chờ"
- **Root cause:** 
  - Backend `api_dashboard()` đếm tất cả visit chưa `DISCHARGED` (kể cả `ChoThanhToan`, `DaHoanThanh`)
  - `complete_examination()` không xóa visit khỏi `room.queue` khi hết chuỗi khoa
  - Frontend `renderWaitingTable()` không lọc theo status
- **Fix:**
  - Chỉ đếm visit có status `ChoCheckIn`, `DangKham`, `CapCuu`
  - Xóa visit khỏi queue + clear `assignedRoomID` khi hoàn tất khám
  - Frontend lọc chỉ hiển thị visit đang thực sự active

#### ✅ Fix Phòng khám hiển thị "0 BN chờ"
- **Bug:** Check-in xong nhưng card phòng luôn hiển thị "0 BN đang chờ"
- **Root cause:** `Room.to_dict()` không trả về `queueLength`, frontend đọc `undefined` → `0`
- **Fix:** Thêm `"queueLength": self.getQueueSize()` vào `to_dict()`

#### ✅ Fix "Đang khám" hiển thị `--` thay vì tên BN + STT
- **Bug:** Box "Bệnh nhân đang khám" hiển thị: `Tên: Đang khám`, `STT: --`, `Số lớn: --`
- **Root cause:** API `/api/rooms/<id>/queue` chỉ trả `currentVisitID`, không trả `patientName` và `stt`
- **Fix:**
  - Backend trả thêm `currentVisitInfo` gồm `patientName` và `stt` (tính = queueSize + 1)
  - Frontend hiển thị đúng tên BN và số thứ tự

#### ✅ Fix Check-in tạo bệnh nhân trùng lặp
- **Bug:** Check-in 2 bệnh nhân khác nhau nhưng dashboard hiển thị cùng 1 tên
- **Root cause:** Frontend không gửi `patient_id`, backend dùng `patient_id=""` (rỗng). Cả 2 lần đều tạo visit với `patientID=""`, trỏ đến cùng 1 patient object trong `global_patients["")]`
- **Fix:** Backend tự động generate `patient_id` (dạng `BN_xxx`) nếu frontend không gửi

#### ✅ Fix Lọc bác sĩ theo khoa trong đặt lịch
- **Bug:** Dropdown bác sĩ trong form "Có đặt lịch trước" hiển thị **tất cả** bác sĩ trong viện, không phân biệt khoa
- **Root cause:** `populateDoctorsSelect()` gọi `/api/doctors` (toàn bộ), không lọc theo khoa đã chọn
- **Fix:**
  - `populateDoctorsSelect(deptId)` giờ nhận tham số `deptId`
  - Nếu có `deptId`, gọi `/api/departments/<deptId>/doctors` để chỉ lấy bác sĩ trong khoa đó
  - Event listener: Khi thay đổi khoa (`reception-dept`), tự động cập nhật danh sách bác sĩ theo khoa mới

#### ✅ UI/UX Improvements
- Giữ nguyên giao diện xanh medical chuyên nghiệp (rollback từ hồng pastel)
- Badge màu chính xác theo priority (Đỏ/Cấp cứu, Vàng/Ưu tiên, Xanh/Thường)

---

### v2.1 - Major Refactor (25/05/2026)

#### ✅ Tab "Quản lý Bệnh nhân" (Gộp Lễ tân + Bệnh nhân)
- **Gộp 2 tab thành 1:** Layout 2 cột (Form bên trái + Table bên phải)
- **Thêm field "Hình thức tiếp đón":**
  - *Khám trực tiếp:* Hiện Dropdown chọn Khoa
  - *Có đặt lịch trước:* Hiện fields Bác sĩ, Ngày/Giờ khám
- **Bảng "Danh sách tiếp đón trong ngày":**
  - Hiện cả BN khám trực tiếp và đặt lịch
  - Mỗi hàng có nút **Check-in**
  - Mặc định màu **ĐỎ** (Chưa check-in)
  - Click → Chuyển **Xanh Lá** (Đã check-in) + Đẩy vào hàng đợi phòng khám
- **Trạng thái sau thanh toán:** Giữ nguyên trong DB, chỉ đổi status = `DaHoanThanh`

#### ✅ Tab "Phòng Khám" (Tối ưu)
- **Danh sách phòng dạng Card:** Hiển thị Badge số BN đang chờ (VD: "Nội Tổng Quát: 3 BN đang chờ")
- **Click phòng mới mở chi tiết:** Queue 3 mức, Gọi BN, Chỉ định DV, Kê đơn
- **Fix bug Filter Dịch vụ:** Chỉ hiển thị dịch vụ thuộc đúng **Mã Khoa** của phòng (không hiện full toàn viện)

#### ✅ Tab "Thu ngân & Kho" (Fix bugs)
- **Fix bug tính tiền thuốc = 0đ:**
  - Backend: Lấy đơn giá từ `global_inventory` (Kho dược)
  - Công thức: `Tổng = Tiền DV + (SL thuốc × Đơn giá) - BHYT`
- **Fix bug gửi đơn thuốc:** Frontend gửi `medicineID` thay vì tên thuốc
- **Fix dropdown bị reset:** Giữ lựa chọn khi auto-refresh
- **Hóa đơn:** Xuất chi tiết dịch vụ + thuốc + BHYT

#### ✅ Backend API mới
- `POST /api/checkin` — Tạo BN + Visit (status = ChoCheckIn)
- `POST /api/confirm-checkin/<visit_id>` — Xác nhận check-in, xếp queue
- `GET /api/today-visits` — Danh sách tiếp đón trong ngày
- `GET /api/rooms/<id>/services` — Dịch vụ theo Khoa của phòng
- `GET /api/payment-detail/<visit_id>` — Chi tiết thanh toán (gồm giá thuốc từ inventory)

#### ✅ Status codes mới
- `ChoCheckIn` — Đã tạo visit, chờ bấm nút Check-in
- `DaHoanThanh` — Đã khám xong + thanh toán (giữ trong DB)

#### ✅ Bug fixes
- Fix `window.currentVisitId` lấy sai key (`visitId` → `visitID`)
- Fix duplicate sidebar tabs (xóa tab Lễ tân cũ, Phòng Khám cũ)
- Fix `global_state` undefined trong frontend

---

### v2.0 - Web Dashboard (24/05/2026)
- ✅ Giao diện web đẹp, chuyên nghiệp (thay cho CLI cũ)
- ✅ 7 tab chức năng với sidebar navigation
- ✅ Real-time auto-refresh (5 giây)
- ✅ Toast notifications
- ✅ Loading spinner
- ✅ Responsive design

### v1.0 - CLI Core (20/05/2026)
- ✅ MultiLevelQueue (3 mức ưu tiên)
- ✅ Strict Priority Scheduling
- ✅ Shortest Queue First
- ✅ Two-Pass Validation
- ✅ Cycle Detection
- ✅ Bill calculation with insurance

---

*Đồ án môn Cấu trúc Dữ liệu & Thuật toán (DSA)*  
*Cập nhật: 13/06/2026*
