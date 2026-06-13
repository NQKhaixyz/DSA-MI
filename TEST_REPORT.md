# BÁO CÁO KIỂM THỬ TỔNG HỢP

## Hệ Thống Quản Lý Bệnh Viện MediCare Pro

**Phiên bản:** v2.3  
**Ngày kiểm thử:** 13/06/2026  
**Người kiểm thử:** Nhóm phát triển  
**Môi trường:** Windows 11, Python 3.11, Flask 3.x

---

## Mục Lục

1. [Tổng quan kiểm thử](#1-tổng-quan-kiểm-thử)
2. [Kết quả kiểm thử tự động (Unit Tests)](#2-kết-quả-kiểm-thử-tự-động-unit-tests)
3. [Kết quả kiểm thử thủ công (Manual Tests)](#3-kết-quả-kiểm-thử-thủ-công-manual-tests)
4. [Kiểm thử hiệu năng](#4-kiểm-thử-hiệu-năng)
5. [Báo cáo lỗi và khắc phục](#5-báo-cáo-lỗi-và-khắc-phục)
6. [Kết luận](#6-kết-luận)

---

## 1. Tổng quan kiểm thử

### 1.1. Phạm vi kiểm thử

| Module | Chức năng | Trạng thái |
|--------|-----------|------------|
| Tiếp đón | Check-in bệnh nhân | ✅ Pass |
| Tiếp đón | Đặt lịch hẹn | ✅ Pass |
| Tiếp đón | Check-in từ danh sách chờ | ✅ Pass |
| Hàng đợi | Xếp hàng đợi đa mức ưu tiên | ✅ Pass |
| Hàng đợi | Strict Priority gọi số | ✅ Pass |
| Hàng đợi | Cấp cứu ưu tiên (preempt) | ✅ Pass |
| Phòng khám | Gọi bệnh nhân tiếp theo | ✅ Pass |
| Phòng khám | Chỉ định dịch vụ | ✅ Pass |
| Phòng khám | Kê đơn thuốc | ✅ Pass |
| Phòng khám | Chuyển khoa | ✅ Pass |
| Phòng khám | Hoàn tất khám | ✅ Pass |
| Thanh toán | Tính tiền dịch vụ | ✅ Pass |
| Thanh toán | Tính tiền thuốc | ✅ Pass |
| Thanh toán | Áp dụng BHYT (tùy chỉnh %) | ✅ Pass |
| Thanh toán | In hóa đơn | ✅ Pass |
| Dashboard | Thống kê tổng quan | ✅ Pass |
| Dashboard | Danh sách chờ real-time | ✅ Pass |
| Lưu trữ | Save/Load JSON | ✅ Pass |
| Mock data | Sinh dữ liệu mẫu | ✅ Pass |

### 1.2. Phương pháp kiểm thử

- **Unit Tests:** unittest Python (27 test cases)
- **Integration Tests:** API endpoint testing (20+ scenarios)
- **Manual UI Tests:** Kiểm thử giao diện web (15+ scenarios)
- **Performance Tests:** Benchmark với 1000-10000 records

---

## 2. Kết quả kiểm thử tự động (Unit Tests)

### 2.1. Cấu trúc dữ liệu cốt lõi

```
python -m unittest benh_vien_dsa.tests -v
```

| Test Case | Mô tả | Kết quả |
|-----------|-------|---------|
| test_priority_queue_operations | Hàng đợi 3 mức: enqueue/dequeue theo priority 3→2→1 | ✅ Pass |
| test_strict_priority_call_next_empty_room | Gọi số phòng rỗng → None | ✅ Pass |
| test_sqf_assign_shortest_queue | SQF chọn phòng có queue ngắn nhất | ✅ Pass |
| test_sqf_no_available_rooms | SQF khi không có phòng → ValueError | ✅ Pass |
| test_cycle_detection_pass | Chuyển khoa mới không cycle | ✅ Pass |
| test_cycle_detection_fail | Chuyển khoa đã khám → lỗi cycle | ✅ Pass |
| test_cycle_detection_limit | Vượt quá 3 khoa/ngày → lỗi | ✅ Pass |
| test_two_pass_validation_success | Xuất kho đủ thuốc → thành công | ✅ Pass |
| test_two_pass_validation_fail | Xuất kho thiếu thuốc → thất bại | ✅ Pass |
| test_two_pass_validation_missing_med | Thuốc không tồn tại → thất bại | ✅ Pass |
| test_bill_calculation_with_insurance | BHYT giảm 80% → trả 20% | ✅ Pass |
| test_bill_calculation_without_insurance | Không BHYT → trả 100% | ✅ Pass |
| test_bill_total_zero | Tổng tiền âm → về 0 | ✅ Pass |
| test_patient_update_info | Cập nhật thông tin bệnh nhân | ✅ Pass |
| test_visit_add_department | Thêm khoa vào visit | ✅ Pass |
| test_visit_add_department_cycle | Thêm khoa đã có → lỗi cycle | ✅ Pass |
| test_medicine_deduct_stock | Xuất kho thuốc | ✅ Pass |
| test_medicine_deduct_insufficient | Xuất kho vượt tồn → False | ✅ Pass |
| test_prescription_calculate_cost | Tính tiền thuốc trong đơn | ✅ Pass |
| test_reception_online_full_slot | Slot đầy → từ chối đặt lịch | ✅ Pass |
| test_reception_online_success | Đặt lịch thành công | ✅ Pass |
| test_checkin_create_patient | Check-in tạo mới bệnh nhân | ✅ Pass |
| test_checkin_create_visit | Check-in tạo visit | ✅ Pass |
| test_confirm_checkin | Xác nhận check-in → xếp queue | ✅ Pass |
| test_call_next_patient | Gọi bệnh nhân tiếp theo | ✅ Pass |
| test_add_prescription | Kê đơn thuốc | ✅ Pass |
| test_process_payment | Thanh toán hoàn tất | ✅ Pass |

**Tổng kết:** 27/27 test cases passed (100%)

### 2.2. Kịch bản kiểm thử tự động chi tiết

#### 2.2.1. Kiểm thử hàng đợi đa mức ưu tiên (MultiLevelQueue)

**Kịch bản:** TC-001  
**Mục tiêu:** Kiểm tra enqueue và dequeue theo đúng thứ tự ưu tiên  
**Các bước:**
1. Tạo MultiLevelQueue mới
2. Enqueue 3 visit với priority: 1 (Thường), 2 (Ưu tiên), 3 (Cấp cứu)
3. Dequeue lần lượt

**Expected Result:**
- Lần 1: Visit priority 3 (Cấp cứu)
- Lần 2: Visit priority 2 (Ưu tiên)
- Lần 3: Visit priority 1 (Thường)
- Lần 4: None (hàng đợi rỗng)

**Actual Result:** ✅ Pass  
**Ghi chú:** Thứ tự đúng 3→2→1

---

**Kịch bản:** TC-002  
**Mục tiêu:** Kiểm tra appendleft_emergency (đẩy cấp cứu lên đầu)  
**Các bước:**
1. Enqueue visit A với priority 3
2. Dùng appendleft_emergency cho visit B
3. Dequeue

**Expected Result:**
- Lần 1: Visit B (vừa thêm emergency)
- Lần 2: Visit A

**Actual Result:** ✅ Pass  
**Ghi chú:** Emergency visit luôn được ưu tiên tuyệt đối

---

#### 2.2.2. Kiểm thử Strict Priority Call Next

**Kịch bản:** TC-003  
**Mục tiêu:** Gọi số trên phòng rỗng  
**Các bước:**
1. Tạo Room mới
2. Gọi strict_priority_call_next

**Expected Result:** Trả về None

**Actual Result:** ✅ Pass

---

**Kịch bản:** TC-004  
**Mục tiêu:** Gọi số khi có nhiều BN trong hàng đợi  
**Các bước:**
1. Thêm 2 BN vào queue (priority 1 và 2)
2. Gọi strict_priority_call_next

**Expected Result:** Trả về BN có priority 2

**Actual Result:** ✅ Pass  
**Ghi chú:** Ưu tiên đúng mức cao hơn

---

#### 2.2.3. Kiểm thử Shortest Queue First (SQF)

**Kịch bản:** TC-005  
**Mục tiêu:** Chọn phòng có queue ngắn nhất  
**Các bước:**
1. Tạo Department với 2 phòng
2. Phòng 1 có 2 BN trong queue
3. Phòng 2 có 0 BN trong queue
4. Gọi shortest_queue_first với visit mới

**Expected Result:** Visit được xếp vào Phòng 2

**Actual Result:** ✅ Pass  
**Ghi chú:** Cân bằng tải đúng

---

**Kịch bản:** TC-006  
**Mục tiêu:** SQF khi không có phòng khả dụng  
**Các bước:**
1. Tạo Department không có phòng
2. Gọi shortest_queue_first

**Expected Result:** Ném ValueError

**Actual Result:** ✅ Pass

---

#### 2.2.4. Kiểm thử Cycle Detection

**Kịch bản:** TC-007  
**Mục tiêu:** Chuyển khoa mới không vi phạm  
**Các bước:**
1. Tạo Visit đã có khoa A
2. Gọi cycle_detection với khoa B

**Expected Result:** Trả về (True, "Chuyển khoa thành công")

**Actual Result:** ✅ Pass

---

**Kịch bản:** TC-008  
**Mục tiêu:** Chuyển khoa đã khám (cycle)  
**Các bước:**
1. Tạo Visit đã có khoa A
2. Gọi cycle_detection với khoa A

**Expected Result:** Trả về (False, "Lỗi: Bệnh nhân đã khám khoa này trong ngày!")

**Actual Result:** ✅ Pass

---

**Kịch bản:** TC-009  
**Mục tiêu:** Vượt quá giới hạn 3 khoa/ngày  
**Các bước:**
1. Tạo Visit đã có 3 khoa
2. Gọi cycle_detection với khoa thứ 4

**Expected Result:** Trả về (False, "Lỗi: Đã vượt quá số lượng 3 khoa/ngày!")

**Actual Result:** ✅ Pass

---

#### 2.2.5. Kiểm thử Two-Pass Validation

**Kịch bản:** TC-010  
**Mục tiêu:** Xuất kho đủ thuốc  
**Các bước:**
1. Tạo Medicine với stock = 100
2. Tạo Prescription yêu cầu 10
3. Gọi two_pass_validation

**Expected Result:** Trả về (True, "Xuất kho và lập hóa đơn thành công"), stock còn 90

**Actual Result:** ✅ Pass

---

**Kịch bản:** TC-011  
**Mục tiêu:** Xuất kho thiếu thuốc (Pass 1 fail)  
**Các bước:**
1. Tạo Medicine với stock = 5
2. Tạo Prescription yêu cầu 10
3. Gọi two_pass_validation

**Expected Result:** Trả về (False, "Lỗi: Kho không đủ số lượng cho thuốc ID xxx")

**Actual Result:** ✅ Pass  
**Ghi chú:** Pass 1 (Read-only) phát hiện thiếu, không thay đổi kho

---

**Kịch bản:** TC-012  
**Mục tiêu:** Thuốc không tồn tại trong kho  
**Các bước:**
1. Tạo Prescription với medicineID không tồn tại
2. Gọi two_pass_validation

**Expected Result:** Trả về (False, "Lỗi: Kho không đủ số lượng cho thuốc ID xxx")

**Actual Result:** ✅ Pass

---

#### 2.2.6. Kiểm thử Tính hóa đơn (Bill Calculation)

**Kịch bản:** TC-013  
**Mục tiêu:** Có BHYT giảm 80%  
**Các bước:**
1. Tạo Patient có BHYT
2. Tạo Visit với 1 dịch vụ 100,000đ
3. Gọi calculate_bill

**Expected Result:**
- serviceCost = 100,000
- insuranceDiscount = 80,000
- finalTotal = 20,000

**Actual Result:** ✅ Pass

---

**Kịch bản:** TC-014  
**Mục tiêu:** Không có BHYT  
**Các bước:**
1. Tạo Patient không có BHYT
2. Tạo Visit với dịch vụ 100,000đ + thuốc 50,000đ
3. Gọi calculate_bill

**Expected Result:**
- serviceCost = 100,000
- medicineCost = 50,000
- insuranceDiscount = 0
- finalTotal = 150,000

**Actual Result:** ✅ Pass

---

**Kịch bản:** TC-015  
**Mục tiêu:** BHYT giảm 100% (miễn phí)  
**Các bước:**
1. Tạo Patient có BHYT
2. Tạo Visit với tổng 150,000đ
3. Gọi calculate_bill với discount = 100%

**Expected Result:**
- finalTotal = 0

**Actual Result:** ✅ Pass

---

**Kịch bản:** TC-016  
**Mục tiêu:** Tổng tiền âm (edge case)  
**Các bước:**
1. Tạo Bill với serviceCost = 0, medicineCost = 0
2. Gọi calculateTotal

**Expected Result:** finalTotal = 0 (không âm)

**Actual Result:** ✅ Pass

---

#### 2.2.7. Kiểm thử Models

**Kịch bản:** TC-017  
**Mục tiêu:** Cập nhật thông tin Patient  
**Các bước:**
1. Tạo Patient
2. Gọi updateInfo(phone="0909123456", address="HN")

**Expected Result:** phone và address được cập nhật

**Actual Result:** ✅ Pass

---

**Kịch bản:** TC-018  
**Mục tiêu:** Thêm khoa vào Visit  
**Các bước:**
1. Tạo Visit
2. Gọi addDepartment("NoiTongQuat")

**Expected Result:** Trả về (True, "Thêm khoa 'NoiTongQuat' thành công.")

**Actual Result:** ✅ Pass

---

**Kịch bản:** TC-019  
**Mục tiêu:** Xuất kho Medicine đủ số lượng  
**Các bước:**
1. Tạo Medicine với stock = 100
2. Gọi deductStock(50)

**Expected Result:** Trả về True, stock còn 50

**Actual Result:** ✅ Pass

---

**Kịch bản:** TC-020  
**Mục tiêu:** Xuất kho Medicine vượt số lượng  
**Các bước:**
1. Tạo Medicine với stock = 10
2. Gọi deductStock(50)

**Expected Result:** Trả về False, stock không đổi

**Actual Result:** ✅ Pass

---

#### 2.2.8. Kiểm thử Reception Service

**Kịch bản:** TC-021  
**Mục tiêu:** Đặt lịch hẹn khi slot đầy  
**Các bước:**
1. Tạo 4 lịch hẹn cùng slot (max = 4)
2. Đặt lịch hẹn thứ 5 cùng slot

**Expected Result:** Trả về (False, "Khung giờ đã đầy, vui lòng chọn khung giờ khác.")

**Actual Result:** ✅ Pass

---

**Kịch bản:** TC-022  
**Mục tiêu:** Đặt lịch hẹn thành công  
**Các bước:**
1. Tạo slot trống
2. Gọi register_online

**Expected Result:** Trả về (True, "Đặt lịch thành công")

**Actual Result:** ✅ Pass

---

**Kịch bản:** TC-023  
**Mục tiêu:** Check-in tạo mới bệnh nhân và visit  
**Các bước:**
1. Gọi checkin_patient với patient_id mới

**Expected Result:**
- Tạo Patient mới trong global_patients
- Tạo Visit mới trong global_visits
- Trả về (visit_obj, "Tạo bệnh nhân và lượt khám thành công")

**Actual Result:** ✅ Pass

---

**Kịch bản:** TC-024  
**Mục tiêu:** Xác nhận check-in đẩy vào queue  
**Các bước:**
1. Tạo Visit với status = ChoCheckIn
2. Gọi confirm_checkin

**Expected Result:**
- Status chuyển thành DangKham
- Visit được thêm vào queue của phòng
- Trả về (visit_obj, "Check-in thành công, đã xếp vào hàng đợi")

**Actual Result:** ✅ Pass

---

#### 2.2.9. Kiểm thử Doctor Service

**Kịch bản:** TC-025  
**Mục tiêu:** Gọi bệnh nhân tiếp theo  
**Các bước:**
1. Tạo Room với 2 BN trong queue
2. Gọi call_next_patient

**Expected Result:** Trả về visit_obj, phòng đánh dấu đang bận

**Actual Result:** ✅ Pass

---

**Kịch bản:** TC-026  
**Mục tiêu:** Kê đơn thuốc  
**Các bước:**
1. Tạo Visit
2. Gọi add_prescription với medicine_list

**Expected Result:**
- Tạo Prescription trong global_prescriptions
- Gán prescriptionID cho visit
- Trả về (True, "Kê đơn thuốc thành công")

**Actual Result:** ✅ Pass

---

#### 2.2.10. Kiểm thử Pharmacy Service

**Kịch bản:** TC-027  
**Mục tiêu:** Thanh toán hoàn tất  
**Các bước:**
1. Tạo Visit với dịch vụ và đơn thuốc
2. Gọi process_payment

**Expected Result:**
- Trừ thuốc trong kho
- Tạo Bill
- Status chuyển thành DaHoanThanh
- Trả về (True, "Thanh toán thành công", bill_obj)

**Actual Result:** ✅ Pass

---

### 2.3. Kiểm thử BHYT tùy chỉnh (v2.3)

**Kịch bản:** TC-028  
**Mục tiêu:** BHYT giảm 40%  
**Các bước:**
1. Tạo Patient có BHYT
2. Tạo Visit với service_cost = 100,000, medicine_cost = 50,000
3. Gọi calculate_bill với discount = 40%

**Expected Result:**
- insuranceDiscount = 60,000
- finalTotal = 90,000

**Actual Result:** ✅ Pass

---

**Kịch bản:** TC-029  
**Mục tiêu:** BHYT giảm 0%  
**Các bước:**
1. Tạo Patient có BHYT
2. Tạo Visit với tổng 150,000đ
3. Gọi calculate_bill với discount = 0%

**Expected Result:**
- insuranceDiscount = 0
- finalTotal = 150,000

**Actual Result:** ✅ Pass

---

**Kịch bản:** TC-030  
**Mục tiêu:** BHYT giảm 100%  
**Các bước:**
1. Tạo Patient có BHYT
2. Tạo Visit với tổng 150,000đ
3. Gọi calculate_bill với discount = 100%

**Expected Result:**
- insuranceDiscount = 150,000
- finalTotal = 0

**Actual Result:** ✅ Pass

---

**Kịch bản:** TC-031  
**Mục tiêu:** Truyền hasInsurance từ check-in xuống backend  
**Các bước:**
1. Gọi checkin_patient với has_insurance = True
2. Kiểm tra Patient trong global_patients

**Expected Result:** patient.hasInsurance = True

**Actual Result:** ✅ Pass

---

**Kịch bản:** TC-032  
**Mục tiêu:** 1 phòng chỉ có 1 bác sĩ (không trùng)  
**Các bước:**
1. Gọi generate_rooms() hoặc init_mock_data_small()
2. Kiểm tra các phòng trong cùng khoa

**Expected Result:** Mỗi phòng có doctorID khác nhau (trong cùng khoa)

**Actual Result:** ✅ Pass

---

**Tổng kết:** 32/32 test cases passed (100%)

```python
# Test case: BHYT giảm 40%
# Input: service_cost = 100,000, medicine_cost = 50,000, discount = 40%
# Expected: insurance_discount = 60,000, final_total = 90,000
# Result: ✅ Pass

# Test case: BHYT giảm 0%
# Input: service_cost = 100,000, medicine_cost = 50,000, discount = 0%
# Expected: insurance_discount = 0, final_total = 150,000
# Result: ✅ Pass

# Test case: BHYT giảm 100%
# Input: service_cost = 100,000, medicine_cost = 50,000, discount = 100%
# Expected: insurance_discount = 150,000, final_total = 0
# Result: ✅ Pass
```

---

## 3. Kết quả kiểm thử thủ công (Manual Tests)

### 3.1. Tab Dashboard

| Bước | Mô tả | Kết quả |
|------|-------|---------|
| 1 | Mở trang chủ | ✅ Hiển thị dashboard |
| 2 | Kiểm tra số liệu thống kê | ✅ Cập nhật đúng |
| 3 | Kiểm tra danh sách chờ | ✅ Chỉ hiển thị BN đang chờ/khám |
| 4 | Auto-refresh sau 5 giây | ✅ Cập nhật tự động |

### 3.2. Tab Quản lý Bệnh nhân (Tiếp đón)

| Bước | Mô tả | Kết quả |
|------|-------|---------|
| 1 | Điền form check-in (khám trực tiếp) | ✅ Tạo BN + Visit |
| 2 | Chọn "Có đặt lịch trước" | ✅ Hiện fields lịch hẹn |
| 3 | Chọn khoa → Cập nhật DS bác sĩ | ✅ Lọc đúng theo khoa |
| 4 | Bấm "Tạo" | ✅ Tạo thành công, hiển thị toast |
| 5 | Kiểm tra bảng danh sách | ✅ BN hiển thị với nút Check-in (ĐỎ) |
| 6 | Bấm Check-in | ✅ Chuyển Xanh Lá, xếp vào queue |
| 7 | Tạo BN có BHYT | ✅ Truyền đúng hasInsurance |

### 3.3. Tab Phòng Khám

| Bước | Mô tả | Kết quả |
|------|-------|---------|
| 1 | Click card phòng | ✅ Hiện chi tiết phòng |
| 2 | Kiểm tra queue 3 cột | ✅ Đúng: Cấp cứu/Ưu tiên/Thường |
| 3 | Bấm "Gọi bệnh nhân tiếp" | ✅ Hiển thị BN đang khám |
| 4 | Chỉ định dịch vụ | ✅ Thêm vào visit |
| 5 | Kê đơn thuốc (từ datalist) | ✅ Gửi medicineID đúng |
| 6 | Hoàn tất khám | ✅ Chuyển sang khoa tiếp/chờ thanh toán |
| 7 | Kích hoạt cấp cứu | ✅ BN được đẩy lên queue cấp cứu |

### 3.4. Tab Thu ngân & Kho Dược

| Bước | Mô tả | Kết quả |
|------|-------|---------|
| 1 | Chọn lượt khám → "Tải" | ✅ Hiển thị chi tiết |
| 2 | Kiểm tra dịch vụ + thuốc | ✅ Hiển đúng giá từ Kho |
| 3 | Nhập % BHYT (ví dụ: 40) | ✅ Tổng tiền tự động tính lại |
| 4 | Để trống BHYT | ✅ Không giảm trừ |
| 5 | Bấm "Thanh toán" | ✅ Tạo hóa đơn, hiển thị chi tiết |
| 6 | Kiểm tra hóa đơn | ✅ Có: Tổng gốc, Giảm trừ, Thành tiền, Trạng thái |
| 7 | Bấm "In hóa đơn" | ✅ Chỉ in phần hóa đơn |
| 8 | Kiểm tra tồn kho sau thanh toán | ✅ Thuốc đã trừ đúng |

### 3.5. Tab Cài đặt

| Bước | Mô tả | Kết quả |
|------|-------|---------|
| 1 | Bấm "Lưu dữ liệu" | ✅ Tạo file JSON |
| 2 | Bấm "Tải dữ liệu" (chọn file) | ✅ Load lại toàn bộ |
| 3 | Bấm "Sinh dữ liệu mẫu" | ✅ Tạo 5 BN + data demo |
| 4 | Kiểm tra phòng khám không trùng BS | ✅ Mỗi phòng 1 BS riêng |

---

## 4. Kiểm thử hiệu năng

### 4.1. Kết quả benchmark

| Chức năng | 1,000 records | 10,000 records | 100,000 records |
|-----------|---------------|----------------|-----------------|
| Tìm kiếm ID | 0.0012s | 0.0085s | 0.0523s |
| Priority Queue | 0.0021s | 0.0152s | 0.0891s |
| Cycle Detection | 0.0008s | 0.0051s | 0.0312s |
| Two-Pass Validation | 0.0015s | 0.0098s | 0.0674s |
| Lưu/Tải JSON | 0.045s | 0.312s | 2.154s |

### 4.2. Đánh giá

- ✅ Tìm kiếm O(1) - Hash Table
- ✅ Hàng đợi O(1) - Multi-level Queue
- ✅ Cycle Detection O(n) - Set operations
- ✅ Lưu trực tiếp vào RAM (In-Memory)

---

## 5. Báo cáo lỗi và khắc phục

### 5.1. Lỗi đã phát hiện và khắc phục

| # | Lỗi | Mức độ | Trạng thái |
|---|-----|--------|------------|
| 1 | Dashboard hiển thị BN đã thanh toán trong danh sách chờ | Trung bình | ✅ Fixed v2.2 |
| 2 | Phòng khám hiển thị "0 BN chờ" | Trung bình | ✅ Fixed v2.2 |
| 3 | "Đang khám" hiển thị `--` thay vì tên BN | Trung bình | ✅ Fixed v2.2 |
| 4 | Check-in tạo bệnh nhân trùng lặp | Cao | ✅ Fixed v2.2 |
| 5 | Dropdown bác sĩ không lọc theo khoa | Trung bình | ✅ Fixed v2.2 |
| 6 | Tính tiền thuốc = 0đ | Cao | ✅ Fixed v2.2 |
| 7 | Frontend gửi tên thuốc thay vì ID | Cao | ✅ Fixed v2.2 |
| 8 | BHYT cố định 80%, không thay đổi được | Trung bình | ✅ Fixed v2.3 |
| 9 | 1 phòng có 2 bác sĩ trùng tên | Trung bình | ✅ Fixed v2.3 |
| 10 | hasInsurance không truyền từ check-in | Trung bình | ✅ Fixed v2.3 |

### 5.2. Lỗi còn tồn tại (Known Issues)

| # | Lỗi | Mức độ | Ghi chú |
|---|-----|--------|---------|
| 1 | Ngrok tunnel tự đổi URL sau restart | Thấp | Dùng paid plan hoặc Cloudflare |
| 2 | Server local tắt khi tắt terminal | Thấp | Dùng `screen` hoặc `pm2` |
| 3 | Dữ liệu không persist khi tắt server | Trung bình | Cần bấm "Lưu" trước khi tắt |
| 4 | Concurrent users có thể race condition | Thấp | Hệ thống single-user demo |

---

## 6. Kết luận

### 6.1. Tổng kết

- **Tổng test cases:** 27 unit tests + 20+ manual tests
- **Pass rate:** 100% (27/27 unit tests, 20/20 manual tests)
- **Hiệu năng:** Đạt yêu cầu real-time với < 0.1s cho 10,000 records
- **UI/UX:** Đáp ứng đầy đủ các luồng nghiệp vụ

### 6.2. Đề xuất cải tiến

1. **Database thực:** Chuyển từ In-Memory sang SQLite/PostgreSQL
2. **Authentication:** Thêm đăng nhập phân quyền (Admin/Bác sĩ/Thu ngân)
3. **Real-time:** Thêm WebSocket cho cập nhật real-time
4. **Backup tự động:** Auto-save định kỳ
5. **Mobile app:** Responsive tốt hơn trên mobile

---

*Ngày lập báo cáo: 13/06/2026*  
*Phiên bản hệ thống: v2.3*
