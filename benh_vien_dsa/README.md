# ĐỒ ÁN MÔN HỌC: CẤU TRÚC DỮ LIỆU & THUẬT TOÁN (DSA)

## Đề tài: Hệ Thống Quản Lý Đặt Lịch Khám Trước và Điều Phối Hàng Đợi Khám Bệnh Tại Bệnh Viện

**Ngôn ngữ lập trình:** Python 3.11+  
**Mô hình lưu trữ:** In-Memory Hash Tables (dict) — mô phỏng không dùng Database thực  
**Giao diện:** Console CLI (Command Line Interface)  

---

## Mục Lục

1. [Tổng quan hệ thống](#1-tổng-quan-hệ-thống)
2. [Kiến trúc lưu trữ toàn cục](#2-kiến-trúc-lưu-trữ-toàn-cục)
3. [Sơ đồ lớp & Cấu trúc dữ liệu cốt lõi](#3-sơ-đồ-lớp--cấu-trúc-dữ-liệu-cốt-lõi)
4. [Các cấu trúc dữ liệu sử dụng](#4-các-cấu-trúc-dữ-liệu-sử-dụng)
5. [Các thuật toán cốt lõi](#5-các-thuật-toán-cốt-lõi)
6. [Quy trình luồng dữ liệu (Workflow)](#6-quy-trình-luồng-dữ-liệu-workflow)
7. [Thiết kế giao diện CLI](#7-thiết-kế-giao-diện-cli)
8. [Class Diagram & Chi tiết đối tượng](#8-class-diagram--chi-tiết-đối-tượng)
9. [Kết quả kiểm thử (Unit Tests)](#9-kết-quả-kiểm-thử-unit-tests)
10. [Kết quả đánh giá hiệu năng (Performance Benchmark)](#10-kết-quả-đánh-giá-hiệu-năng-performance-benchmark)
11. [Hướng dẫn cài đặt & vận hành](#11-hướng-dẫn-cài-đặt--vận-hành)
12. [Cấu trúc thư mục dự án](#12-cấu-trúc-thư-mục-dự-án)

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

**Lý do chọn Hash Table (dict):**
- Truy cập, chèn, xóa trung bình **O(1)**.
- Không cần duyệt tuần tự qua hàng nghìn bản ghi khi tra cứu.
- Linh hoạt với nhiều kiểu khóa (String, Tuple).

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

**Các thao tác:**
| Thao tác | Độ phức tạp | Mô tả |
|----------|-------------|-------|
| `enqueue(item, priority)` | **O(1)** | Thêm vào cuối deque |
| `dequeue()` | **O(1)** | Lấy từ đầu theo thứ tự 3→2→1 |
| `appendleft_emergency(item)` | **O(1)** | Chèn cấp cứu lên đầu |
| `remove(item, priority)` | **O(N)** | Xóa phần tử cụ thể |
| `get_total_size()` | **O(1)** | Tổng số bệnh nhân chờ |

**Ưu điểm:** Bảo toàn FIFO trong cùng mức ưu tiên; thao tác hai đầu cực nhanh.  
**Nhược điểm:** Tìm kiếm phần tử ở giữa chậm **O(N)**.  
**Lý do chọn:** Số mức ưu tiên cố định (chính xác 3 mức), đòi hỏi tính FIFO cao, không cần cơ chế Heap phức tạp.

### 4.2. Bảng Băm (Hash Table / dict)
**Ứng dụng:**
- **Quản lý Slot đặt lịch:** Key = `(doctorID, ngày, khung_giờ)` → Value = `list` (tối đa 4 BN).
- **Kho thuốc:** Key = `medicineID` → Value = `stockQuantity`.

| Thao tác | Độ phức tạp |
|----------|-------------|
| Chèn/Cập nhật | **O(1)** |
| Tra cứu | **O(1)** |
| Xóa | **O(1)** |

### 4.3. Tập Hợp Băm (Hash Set / set)
**Ứng dụng:** Chặn vòng lặp luân chuyển liên khoa.

```python
visited_departments = set()  # O(1) kiểm tra tồn tại
```

Mỗi lần bệnh nhân khám xong khoa `u`, hệ thống thực hiện `visited_departments.add(u)`.  
Khi bác sĩ chuyển khoa `v`, kiểm tra `if v in visited_departments:` → **O(1)**.

---

## 5. Các thuật toán cốt lõi

### 5.1. Thuật toán Điều phối Hàng đợi Ưu tiên Nghiêm ngặt (Strict Priority Scheduling)

**Giả mã:**
```python
def callNextPatient(self):
    # Mức 3: Cấp cứu
    if len(self.queues[3]) > 0:
        return self.queues[3].popleft()
    
    # Mức 2: Đặt lịch — kiểm tra đúng khung giờ
    if len(self.queues[2]) > 0:
        patient = self.queues[2][0]
        if is_valid_time(patient):
            return self.queues[2].popleft()
    
    # Mức 1: Vãng lai
    if len(self.queues[1]) > 0:
        return self.queues[1].popleft()
    
    return None  # Phòng rảnh
```

**Cấp cứu khẩn cấp (Preemptive Injection):**
```python
def emergencyPreempt(self, patient_visit):
    self.remove_from_current_queue(patient_visit)
    self.queues[3].appendleft(patient_visit)
```

| | Phân tích |
|---|---|
| **Time** | **O(1)** cho dequeue và appendleft_emergency |
| **Space** | **O(N)** với N = tổng số bệnh nhân đang chờ |

**Ưu điểm:** Phản hồi tức thời O(1), code gọn nhẹ, không cần re-indexing.  
**Nhược điểm:** Có thể xảy ra "Starvation" (bệnh nhân Mức 1 đợi vĩnh viễn nếu Mức 2/3 liên tục vào).  
**Lý do chọn:** Trong y tế, tính mạng là ưu tiên số một. Việc BN vãng lai phải chờ khi có ca cấp cứu là logic hoàn toàn hợp lý.

---

### 5.2. Thuật toán Cân bằng tải "Hàng đợi ngắn nhất" (Shortest Queue First — SQF)

**Giả mã:**
```python
def assign_to_optimal_room(self, visit_obj):
    best_room = None
    min_length = float('inf')
    
    for room in self.rooms:
        total_waiting = len(room.queues[3]) + len(room.queues[2]) + len(room.queues[1])
        if total_waiting < min_length:
            min_length = total_waiting
            best_room = room
    
    best_room.queues[visit_obj.priority].append(visit_obj)
    return best_room
```

| | Phân tích |
|---|---|
| **Time** | **O(K)** với K = số phòng trong khoa (thực tế K rất nhỏ, ~2-5) |
| **Space** | **O(1)** chỉ lưu vài biến tạm |

**Ưu điểm:** Triển khai cực nhanh, kết hợp hoàn hảo với `len()` của deque (**O(1)**).  
**Nhược điểm:** Chỉ đếm "số người" chứ không ước lượng "thời gian khám".  
**Lý do chọn:** Chi phí tính toán gần như bằng 0, hiệu quả điều phối thực tế tốt.

---

### 5.3. Thuật toán Xác thực toàn vẹn 2 bước (Two-Pass Validation)

Mô phỏng nguyên tắc **ACID** (Atomicity): giao dịch xuất kho thuốc chỉ thành công trọn vẹn, hoặc không có thay đổi nào (All-or-Nothing).

**Giả mã:**
```python
def process_prescription(prescription_obj, global_inventory):
    # Bước 1: Read-only Validation
    for med_id, required_qty in prescription_obj.medicineList.items():
        if global_inventory[med_id].stockQuantity < required_qty:
            return False, f"Lỗi: Kho không đủ số lượng cho thuốc ID {med_id}"
    
    # Bước 2: Write Execution (chỉ khi Bước 1 hoàn toàn thành công)
    for med_id, required_qty in prescription_obj.medicineList.items():
        global_inventory[med_id].deductStock(required_qty)
    
    return True, "Xuất kho và lập hóa đơn thành công"
```

| | Phân tích |
|---|---|
| **Time** | **O(M)** với M = số loại thuốc trong đơn (thường ≤ 10) |
| **Space** | **O(1)** thực hiện trừ trực tiếp trên dict |

**Ưu điểm:** An toàn tuyệt đối về dữ liệu. Không cần logic Rollback phức tạp.  
**Nhược điểm:** Phải duyệt đơn thuốc 2 lần.  
**Lý do chọn:** M rất nhỏ nên chi phí duyệt 2 lần không đáng kể, đổi lại sự an toàn và chính xác tuyệt đối.

---

### 5.4. Thuật toán Phát hiện chu trình trạng thái (O(1) Cycle Detection)

**Giả mã:**
```python
class Visit:
    def __init__(self):
        self.visited_departments = set()  # O(1) tra cứu

    def addDepartment(self, dept_id):
        if dept_id in self.visited_departments:
            return False, "Lỗi: Bệnh nhân đã khám khoa này trong ngày!"
        
        if len(self.visited_departments) >= 3:
            return False, "Lỗi: Đã vượt quá số lượng 3 khoa/ngày!"
        
        self.visited_departments.add(dept_id)
        return True, "Chuyển khoa thành công"
```

| | Phân tích |
|---|---|
| **Time** | **O(1)** cho mọi thao tác kiểm tra (nhờ cơ chế băm của Set) |
| **Space** | **O(D)** với D ≤ 3 (số khoa BN đã khám trong ngày) |

**Ưu điểm:** Khắc phục hoàn toàn việc query lại DB hoặc vòng lặp O(N).  
**Lý do chọn:** Giải pháp thanh lịch, gọn nhẹ, bảo vệ luồng dữ liệu khỏi sai sót con người.

---

## 6. Quy trình luồng dữ liệu (Workflow)

Vòng đời thực thi của chương trình diễn ra theo **5 bước**:

### Bước 1: Boot & Mock Data
- Tạo 5-9 Department.
- Trong mỗi Department tạo 1-2 Room.
- Khởi tạo danh sách Dịch vụ và Kho Thuốc (Hash Tables).
- Sinh dữ liệu mẫu (nếu chạy benchmark).

### Bước 2: Đăng ký (Lễ tân)
1. Khách tạo mới → Lookup `global_patients` (O(1)).
   - Nếu chưa có → Khởi tạo `Patient` → Tạo `Visit`.
2. Xác định mức ưu tiên: Khẩn cấp (3), Có lịch (2), Vãng lai (1).
3. Gọi hàm **SQF** để nhét `Visit` vào 1 `Room` của Khoa đầu tiên.

### Bước 3: Bác sĩ khám (Bảng điều khiển Phòng khám)
1. Bác sĩ ấn "Gọi bệnh nhân" → Hệ thống chạy **Priority Queue** rút BN ra.
2. Khám bệnh: Add `serviceID` vào mảng `usedServiceIDs`.
3. Chuyển khoa: Thuật toán **Cycle Detection** (Set) kiểm tra.
   - Hợp lệ → Chạy lại luồng **SQF** đẩy vào queue khoa tiếp theo.

### Bước 4: Cấp cứu đột xuất
- Admin/bác sĩ đổi `severity = NguyKich`.
- Hàm `emergencyPreempt` kích hoạt: BN bị remove khỏi queue hiện tại và `appendleft` vào Mức 3.

### Bước 5: Thanh toán (Quầy Dược & Thu ngân)
1. Nhập ID bệnh nhân → Lookup **O(1)** lấy `Visit` hiện tại.
2. Tổng hợp tiền từ bảng Dịch vụ **O(N)**.
3. Chạy **Two-Pass Validation** cho đơn thuốc.
4. Xuất `Bill` → Chuyển `status` Visit thành `Discharged`.
5. BN bị xóa khỏi mọi hệ thống, rác tự dọn (Garbage Collection).

---

## 7. Thiết kế giao diện CLI

Hệ thống chia làm **3 phân hệ chính**:

### [1] PHÂN HỆ LỄ TÂN
- `1.1` Đăng ký đặt lịch Online (Xử lý Slot)
- `1.2` Tiếp đón bệnh nhân trực tiếp (Vãng lai)
- `1.3` Kích hoạt trạng thái Cấp cứu khẩn cấp (Chạy Preemptive)
- `1.4` Hiển thị danh sách chờ phòng khám

### [2] PHÂN HỆ BÁC SĨ
- `2.1` Bảng điện tử: Xem danh sách chờ của Phòng khám (Đủ 3 Queue)
- `2.2` Gọi bệnh nhân tiếp theo (Chạy Strict Priority)
- `2.3` Chỉ định dịch vụ / Kê đơn thuốc
- `2.4` Hoàn tất khám / Chuyển khoa chuyên môn (Chạy Cycle Detection)

### [3] PHÂN HỆ THU NGÂN & KHO DƯỢC
- `3.1` Nhập mã bệnh nhân để thanh toán
- `3.2` Trích xuất hóa đơn viện phí & Trừ kho thuốc (Chạy Two-Pass)

### [4-7] Công cụ hỗ trợ
- `4` Lưu dữ liệu ra file JSON
- `5` Tải dữ liệu từ file JSON
- `6` Chạy Performance Test
- `7` Chạy Unit Tests

---

## 8. Class Diagram & Chi tiết đối tượng

### Danh sách 10 Class chính

#### 8.1. Patient (Bệnh nhân)
| Thuộc tính | Kiểu | Ý nghĩa |
|------------|------|---------|
| patientID | str | Mã bệnh nhân |
| fullName | str | Họ tên |
| gender | str | Giới tính |
| dob | str | Ngày sinh |
| citizenID | str | CCCD/CMND |
| phone | str | SĐT |
| email | str | Email |
| address | str | Địa chỉ |
| bloodType | str | Nhóm máu |
| hasInsurance | bool | BHYT |

**Methods:** `updateInfo()`, `displayInfo()`, `to_dict()`, `from_dict()`

#### 8.2. Visit (Lần khám — Xương sống hệ thống)
| Thuộc tính | Kiểu | Ý nghĩa |
|------------|------|---------|
| visitID | str | Mã lần khám |
| patientID | str | Mã BN |
| visitDate | str | Ngày khám |
| arrivalTime | str | Giờ đến |
| severity | str | Mức độ sức khỏe |
| queuePriority | int | Mức ưu tiên hàng đợi (1/2/3) |
| status | str | Trạng thái |
| departmentSequence | list | Danh sách khoa cần khám |
| currentDepartmentIndex | int | Vị trí khoa hiện tại |
| assignedDoctorIDs | list | Các bác sĩ đã khám |
| assignedRoomID | str | Phòng hiện tại |
| usedServiceIDs | list | Dịch vụ đã dùng |
| prescriptionID | str | Mã toa thuốc |
| billID | str | Mã hóa đơn |
| visited_departments | set | Lịch sử khoa đã khám (Cycle Detection) |

**Methods:** `addDepartment()`, `moveToNextDepartment()`, `addService()`, `assignDoctor()`, `updatePriority()`, `updateStatus()`, `getCurrentDepartment()`, `isCompleted()`

#### 8.3. Doctor (Bác sĩ)
| Thuộc tính | Kiểu | Ý nghĩa |
|------------|------|---------|
| doctorID | str | Mã BS |
| fullName | str | Họ tên |
| gender | str | Giới tính |
| dob | str | Ngày sinh |
| phone | str | SĐT |
| email | str | Email |
| address | str | Địa chỉ |
| departmentID | str | Khoa trực thuộc |
| degree | str | Học hàm/vị |
| licenseNumber | str | Số CCHN |
| yearsExperience | int | Số năm kinh nghiệm |
| roomID | str | Phòng khám |

**Methods:** `assignPatient()`, `completeExamination()`, `addServiceToVisit()`, `transferDepartment()`

#### 8.4. Department (Khoa)
| Thuộc tính | Kiểu | Ý nghĩa |
|------------|------|---------|
| departmentID | str | Mã khoa |
| departmentName | str | Tên khoa |
| doctorIDs | list | Danh sách bác sĩ |
| roomIDs | list | Danh sách phòng |
| serviceIDs | list | Danh sách dịch vụ |

**Methods:** `addDoctor()`, `addRoom()`, `addService()`

#### 8.5. Room (Phòng khám)
| Thuộc tính | Kiểu | Ý nghĩa |
|------------|------|---------|
| roomID | str | Mã phòng |
| departmentID | str | Mã khoa |
| doctorID | str | Mã BS phụ trách |
| queues | MultiLevelQueue | Hàng đợi 3 mức |
| currentVisitID | str | BN đang khám |

**Methods:** `addToQueue()`, `callNextPatient()`, `getQueueSize()`, `isBusy()`, `emergencyPreempt()`

#### 8.6. Service (Dịch vụ y tế)
| Thuộc tính | Kiểu | Ý nghĩa |
|------------|------|---------|
| serviceID | str | Mã DV |
| serviceName | str | Tên DV |
| departmentID | str | Khoa phụ trách |
| price | float | Giá tiền |

**Methods:** `displayService()`

#### 8.7. Medicine (Thuốc)
| Thuộc tính | Kiểu | Ý nghĩa |
|------------|------|---------|
| medicineID | str | Mã thuốc |
| medicineName | str | Tên thuốc |
| unitPrice | float | Đơn giá |
| stockQuantity | int | Tồn kho |

**Methods:** `addStock()`, `deductStock()`, `checkAvailability()`

#### 8.8. Prescription (Toa thuốc)
| Thuộc tính | Kiểu | Ý nghĩa |
|------------|------|---------|
| prescriptionID | str | Mã toa |
| visitID | str | Mã lần khám |
| doctorID | str | Mã BS kê đơn |
| medicineList | dict | {medID: qty} |
| note | str | Ghi chú |

**Methods:** `addMedicine()`, `removeMedicine()`, `calculateMedicineCost()`

#### 8.9. Bill (Hóa đơn)
| Thuộc tính | Kiểu | Ý nghĩa |
|------------|------|---------|
| billID | str | Mã HĐ |
| visitID | str | Mã lần khám |
| serviceCost | float | Tiền dịch vụ |
| medicineCost | float | Tiền thuốc |
| insuranceDiscount | float | Giảm trừ BHYT |
| finalTotal | float | Tổng thanh toán |
| paymentStatus | str | Trạng thái |

**Methods:** `calculateTotal()`, `applyInsurance()`, `generateInvoice()`, `markPaid()`

#### 8.10. Appointment (Lịch hẹn)
| Thuộc tính | Kiểu | Ý nghĩa |
|------------|------|---------|
| appointmentID | str | Mã lịch |
| patientID | str | Mã BN |
| departmentSequence | list | Chuỗi khoa |
| selectedDoctorID | str | BS đã chọn |
| appointmentDate | str | Ngày hẹn |
| timeSlot | str | Khung giờ |
| status | str | Trạng thái |

**Methods:** `confirmAppointment()`, `cancelAppointment()`, `updateSlot()`

---

## 9. Kết quả kiểm thử (Unit Tests)

Chạy lệnh: `python -m unittest benh_vien_dsa.tests -v`

**Kết quả:** `Ran 16 tests in 0.002s — OK`

### Danh sách 16 Test Case

| STT | Test Case | Mô tả | Kết quả |
|-----|-----------|-------|---------|
| 1 | `test_priority_queue_operations` | Enqueue 3 mức, verify dequeue 3→2→1, emergency appendleft | ✅ Pass |
| 2 | `test_strict_priority_call_next_empty_room` | Gọi phòng rỗng trả về None | ✅ Pass |
| 3 | `test_sqf_assign_shortest_queue` | 2 phòng (2 BN vs 0 BN), verify vào phòng ngắn hơn | ✅ Pass |
| 4 | `test_cycle_detection_blocks_duplicate` | Thêm khoa A 2 lần → bị chặn | ✅ Pass |
| 5 | `test_cycle_detection_max_3_departments` | Thêm khoa thứ 4 → bị từ chối | ✅ Pass |
| 6 | `test_two_pass_validation_success` | Thuốc đủ kho → xuất kho đúng | ✅ Pass |
| 7 | `test_two_pass_validation_failure` | Thuốc thiếu → stock giữ nguyên (không bị trừ) | ✅ Pass |
| 8 | `test_emergency_preempt` | Preempt đẩy BN lên đầu queue cấp cứu | ✅ Pass |
| 9 | `test_bill_calculation_with_insurance` | Có BHYT: thanh toán 20% tổng chi phí | ✅ Pass |
| 10 | `test_bill_calculation_without_insurance` | Không BHYT: thanh toán 100% | ✅ Pass |
| 11 | `test_slot_limit_blocks_fifth_patient` | Slot thứ 5 bị từ chối (giới hạn 4) | ✅ Pass |
| 12 | `test_reception_checkin_walkin` | Check-in vãng lai có priority = 1 | ✅ Pass |
| 13 | `test_reception_checkin_appointment` | Check-in có hẹn có priority = 2 | ✅ Pass |
| 14 | `test_doctor_complete_examination_calls_next` | Hoàn tất khám giải phóng phòng, gọi BN tiếp theo | ✅ Pass |
| 15 | `test_persistence_save_and_load` | Save JSON → reset → load → verify dữ liệu đúng | ✅ Pass |
| 16 | `test_transfer_department_valid` | Chuyển khoa hợp lệ, update visited_departments | ✅ Pass |

---

## 10. Kết quả đánh giá hiệu năng (Performance Benchmark)

**Chạy lệnh:** `python -m benh_vien_dsa.performance_test`

### Bảng tổng hợp benchmark thực tế

| Thao tác | Số lượng | Tổng thời gian | Trung bình / lần | Đánh giá |
|----------|----------|----------------|------------------|----------|
| **Tìm kiếm ID** (dict lookup) | 10.000 | 0.0004s | ~0.000000s | O(1) ✅ |
| **Tìm kiếm ID** | 50.000 | 0.0006s | ~0.000001s | O(1) ✅ |
| **Tìm kiếm ID** | 100.000 | 0.0012s | ~0.000001s | O(1) ✅ |
| **Priority Queue** (enqueue/dequeue) | 10.000 | 0.0049s | ~0.000000s | O(1) ✅ |
| **Priority Queue** | 50.000 | 0.0257s | ~0.000001s | O(1) ✅ |
| **Cycle Detection** (Set lookup) | 10.000 | 0.0059s | ~0.000001s | O(1) ✅ |
| **Cycle Detection** | 50.000 | 0.0295s | ~0.000001s | O(1) ✅ |
| **Cycle Detection** | 100.000 | 0.0702s | ~0.000001s | O(1) ✅ |
| **Two-Pass Validation** | 10.000 | 0.0173s | ~0.000002s | O(M) ✅ |
| **Two-Pass Validation** | 50.000 | 0.0902s | ~0.000002s | O(M) ✅ |
| **Two-Pass Validation** | 100.000 | 0.1985s | ~0.000002s | O(M) ✅ |
| **Lưu/Tải JSON** | 10.000 BN | 0.1596s | 0.0798s | I/O bound |
| **Lưu/Tải JSON** | 50.000 BN | 1.0454s | 0.5227s | I/O bound |
| **Lưu/Tải JSON** | 100.000 BN | 1.3458s | 0.6729s | I/O bound |

### Nhận xét hiệu năng
- **Tìm kiếm ID** trên 100.000 bản ghi chỉ mất **0.0012 giây** → xác nhận độ phức tạp **O(1)** của Hash Table.
- **Priority Queue** xử lý 50.000 lượt enqueue/dequeue trong **0.0257 giây** → xác nhận **O(1)** của deque.
- **Cycle Detection** 100.000 lần kiểm tra trong **0.07 giây** → xác nhận **O(1)** của Set.
- **Two-Pass Validation** tuyến tính theo số loại thuốc trong đơn, hoàn toàn đáp ứng yêu cầu thời gian thực.
- **Lưu/Tải JSON** là thao tác I/O bound, tỷ lệ thuận với số lượng dữ liệu, nhưng vẫn rất nhanh với 100k bản ghi (~1.3 giây).

---

## 11. Hướng dẫn cài đặt & vận hành

### 11.1. Yêu cầu
- Python 3.11 hoặc cao hơn
- Không cần cài thêm thư viện ngoài (chỉ dùng Standard Library)

### 11.2. Khởi chạy hệ thống
```bash
# 1. Chạy giao diện CLI tương tác
python -m benh_vien_dsa.main

# 2. Chạy Unit Tests
python -m unittest benh_vien_dsa.tests -v

# 3. Chạy Performance Benchmark
python -m benh_vien_dsa.performance_test

# 4. Chạy sinh dữ liệu mẫu lớn (10.000+ bản ghi)
python -c "from benh_vien_dsa.mock_generator import init_mock_data_large; init_mock_data_large()"
```

### 11.3. Lưu ý khi chạy trên Windows
Nếu gặp lỗi `UnicodeEncodeError` khi in tiếng Việt ra console, hãy chạy với encoding UTF-8:
```bash
chcp 65001
set PYTHONIOENCODING=utf-8
python -m benh_vien_dsa.main
```

---

## 12. Cấu trúc thư mục dự án

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
├── cli.py                   # Menu Console tương tác (3 phân hệ)
├── main.py                  # Điểm vào chính
└── README.md                # Tài liệu hệ thống (file này)
```

---

## Kết luận

Hệ thống đã hoàn thiện toàn bộ các yêu cầu nghiệp vụ, áp dụng đúng 4 cấu trúc dữ liệu cốt lõi (dict, deque, set, list) và 4 thuật toán chính (Strict Priority Scheduling, SQF, Two-Pass Validation, Cycle Detection). Tất cả Unit Test đều pass, hiệu năng đạt yêu cầu O(1) cho các thao tác chính trên tập dữ liệu lên đến 100.000 bản ghi.

---
*Đồ án môn Cấu trúc Dữ liệu & Thuật toán (DSA)*
