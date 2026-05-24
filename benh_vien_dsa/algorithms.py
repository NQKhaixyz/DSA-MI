"""
Module thuật toán cốt lõi cho hệ thống quản lý bệnh viện.
Chứa các hàm xử lý nghiệp vụ quan trọng như gọi số, cân bằng tải,
xác thực kho thuốc, phát hiện chu trình khám, và tính toán hóa đơn.
"""

from __future__ import annotations

import time
import random
import uuid
from typing import Optional, Tuple

try:
    from . import config
    from . import global_state
    from . import models
    from . import data_structures
except ImportError:
    import config
    import global_state
    import models
    import data_structures


def strict_priority_call_next(room: models.Room) -> Optional[models.Visit]:
    """
    Gọi bệnh nhân tiếp theo theo thuật toán Strict Priority Scheduling.

    Thuật toán này ưu tiên tuyệt đối theo thứ tự:
      - Mức 3 (Cấp cứu - PRIORITY_EMERGENCY)
      - Mức 2 (Hẹn trước - PRIORITY_APPOINTMENT)
      - Mức 1 (Tới trực tiếp - PRIORITY_WALKIN)

    Nếu lấy được lượt khám, cập nhật currentVisitID của phòng
    để đánh dấu phòng đang phụ trách lượt khám này.

    Args:
        room: Đối tượng Room cần gọi bệnh nhân.

    Returns:
        Đối tượng Visit nếu có bệnh nhân trong hàng đợi,
        None nếu hàng đợi trống.
    """
    # Gọi dequeue trên hàng đợi đa mức ưu tiên của phòng
    # Hàng đợi đã tự động xử lý thứ tự ưu tiên: 3 -> 2 -> 1
    visit = room.queues.dequeue()

    if visit is not None:
        # Cập nhật lượt khám hiện tại cho phòng
        room.currentVisitID = visit.visitID

    return visit


def shortest_queue_first(
    department: models.Department,
    visit_obj: models.Visit,
) -> models.Room:
    """
    Thuật toán cân bằng tải "Hàng đợi ngắn nhất" (Shortest Queue First - SQF).

    Lặp qua danh sách phòng thuộc khoa, tính tổng số bệnh nhân đang chờ
    trong mỗi phòng, sau đó chọn phòng có hàng đợi ngắn nhất để thêm
    lượt khám mới. Điều này giúp phân bổ đều tải và giảm thời gian chờ.

    Args:
        department: Đối tượng Department chứa các phòng.
        visit_obj: Đối tượng Visit cần được xếp vào phòng.

    Returns:
        Đối tượng Room được chọn (có hàng đợi ngắn nhất).

    Raises:
        ValueError: Nếu khoa không có phòng nào khả dụng.
    """
    best_room: Optional[models.Room] = None
    min_waiting = float("inf")

    # Duyệt qua tất cả các phòng thuộc khoa
    for room_id in department.roomIDs:
        try:
            room = global_state.global_rooms[room_id]
        except KeyError:
            # Bỏ qua nếu roomID không tồn tại trong hệ thống
            continue

        # Tính tổng số bệnh nhân đang chờ trong phòng
        total_waiting = room.getQueueSize()

        # Cập nhật phòng tốt nhất nếu tìm được hàng đợi ngắn hơn
        if total_waiting < min_waiting:
            min_waiting = total_waiting
            best_room = room

    if best_room is None:
        raise ValueError(
            f"Khoa '{department.departmentID}' không có phòng khả dụng nào."
        )

    # Thêm lượt khám vào hàng đợi của phòng được chọn với mức ưu tiên hiện tại
    best_room.addToQueue(visit_obj, visit_obj.queuePriority)

    # Cập nhật phòng được phân công cho lượt khám
    visit_obj.assignedRoomID = best_room.roomID

    return best_room


def two_pass_validation(
    prescription: models.Prescription,
    global_inventory: dict[str, models.Medicine],
) -> Tuple[bool, str]:
    """
    Thuật toán xác thực toàn vẹn 2 bước (Two-Pass Validation) cho xuất kho thuốc.

    Bước 1 - Đọc (Read-only): Kiểm tra tồn kho cho TẤT CẢ các thuốc trong đơn.
    Nếu bất kỳ loại thuốc nào không đủ số lượng hoặc không tồn tại,
    trả về lỗi ngay lập tức mà KHÔNG thay đổi kho.
    Điều này đảm bảo tính nguyên tử của giao dịch.

    Bước 2 - Ghi (Write): Nếu bước 1 thành công, tiến hành trừ kho
    cho từng loại thuốc một cách an toàn.

    Args:
        prescription: Đơn thuốc cần xác thực.
        global_inventory: Từ điển toàn cục chứa các đối tượng Medicine.

    Returns:
        Tuple (success: bool, message: str).
    """
    # --- BƯỚC 1: Kiểm tra tồn kho (Read-only) ---
    for med_id, required_qty in prescription.medicineList.items():
        try:
            medicine = global_inventory[med_id]
        except KeyError:
            return False, f"Lỗi: Kho không đủ số lượng cho thuốc ID {med_id}"

        if medicine.stockQuantity < required_qty:
            return False, f"Lỗi: Kho không đủ số lượng cho thuốc ID {med_id}"

    # --- BƯỚC 2: Xuất kho (Write) ---
    for med_id, required_qty in prescription.medicineList.items():
        medicine = global_inventory[med_id]
        # deductStock trả về False nếu không đủ (không nên xảy ra sau bước 1)
        if not medicine.deductStock(required_qty):
            return False, f"Lỗi: Xuất kho thất bại cho thuốc ID {med_id}"

    return True, "Xuất kho và lập hóa đơn thành công"


def cycle_detection(
    visit: models.Visit,
    dept_id: str,
) -> Tuple[bool, str]:
    """
    Thuật toán phát hiện chu trình (cycle detection) trong chuỗi khám khoa.

    Kiểm tra xem bệnh nhân đã khám khoa này trong ngày chưa (tránh lặp lại)
    và có vượt quá giới hạn số khoa tối đa cho phép trong một ngày không.

    Args:
        visit: Đối tượng Visit hiện tại của bệnh nhân.
        dept_id: ID của khoa muốn chuyển đến.

    Returns:
        Tuple (success: bool, message: str).
        success=True nếu cho phép chuyển khoa, False nếu vi phạm quy tắc.
    """
    # Kiểm tra xem khoa này đã được khám trong lượt khám hiện tại chưa
    if dept_id in visit.visited_departments:
        return False, "Lỗi: Bệnh nhân đã khám khoa này trong ngày!"

    # Kiểm tra giới hạn số khoa tối đa mỗi ngày
    if len(visit.visited_departments) >= config.MAX_DEPARTMENTS_PER_DAY:
        return False, "Lỗi: Đã vượt quá số lượng 3 khoa/ngày!"

    # Thêm khoa mới vào tập đã khám
    visit.visited_departments.add(dept_id)

    return True, "Chuyển khoa thành công"


def calculate_bill(
    visit: models.Visit,
    global_services: dict[str, models.Service],
    global_inventory: dict[str, models.Medicine],
) -> models.Bill:
    """
    Tính toán hóa đơn cho một lượt khám dựa trên dịch vụ đã sử dụng và thuốc đã kê.

    Tổng tiền dịch vụ = tổng giá của các dịch vụ trong visit.usedServiceIDs.
    Tổng tiền thuốc = tổng chi phí thuốc từ đơn thuốc (nếu có).
    Nếu bệnh nhân có BHYT, áp dụng giảm trừ 80%.

    Args:
        visit: Đối tượng Visit cần lập hóa đơn.
        global_services: Từ điển toàn cục chứa các đối tượng Service.
        global_inventory: Từ điển toàn cục chứa các đối tượng Medicine.

    Returns:
        Đối tượng Bill đã được tính toán đầy đủ và lưu vào global_bills.
    """
    service_cost = 0.0

    # Tính tổng chi phí dịch vụ y tế đã sử dụng
    for service_id in visit.usedServiceIDs:
        try:
            service = global_services[service_id]
            service_cost += service.price
        except KeyError:
            # Bỏ qua nếu dịch vụ không tồn tại trong hệ thống
            continue

    medicine_cost = 0.0

    # Tính tổng chi phí thuốc nếu có đơn thuốc
    if visit.prescriptionID:
        try:
            prescription = global_state.global_prescriptions[visit.prescriptionID]
            medicine_cost = prescription.calculateMedicineCost(global_inventory)
        except KeyError:
            # Đơn thuốc không tồn tại, coi như chi phí thuốc = 0
            medicine_cost = 0.0

    # Tạo hóa đơn mới với ID duy nhất
    bill_id = generate_id("BILL", global_state.global_bills)
    bill = models.Bill(bill_id, visit.visitID)
    bill.serviceCost = service_cost
    bill.medicineCost = medicine_cost

    # Kiểm tra bảo hiểm y tế của bệnh nhân
    try:
        patient = global_state.global_patients[visit.patientID]
        if patient.hasInsurance:
            bill.applyInsurance(True)
    except KeyError:
        # Bệnh nhân không tồn tại, tiếp tục không áp dụng BHYT
        pass

    # Tính tổng tiền cuối cùng
    bill.calculateTotal()

    # Gán hóa đơn cho lượt khám và lưu vào hệ thống
    visit.billID = bill.billID
    global_state.global_bills[bill.billID] = bill

    return bill


def generate_id(
    prefix: str,
    existing_dict: dict | None = None,
) -> str:
    """
    Tạo mã định danh duy nhất cho các đối tượng trong hệ thống.

    ID được tạo theo định dạng: {prefix}_{timestamp}_{random}
    Nếu truyền existing_dict, hàm sẽ đảm bảo ID chưa tồn tại trong dict.

    Args:
        prefix: Tiền tố của ID (ví dụ: "BILL", "VISIT", "PRES").
        existing_dict: Từ điển chứa các ID đã tồn tại (tùy chọn).

    Returns:
        Chuỗi ID duy nhất.
    """
    max_attempts = 100

    for _ in range(max_attempts):
        # Tạo ID theo định dạng prefix_timestamp_random
        timestamp = int(time.time())
        rand_suffix = random.randint(1000, 9999)
        new_id = f"{prefix}_{timestamp}_{rand_suffix}"

        # Nếu không có existing_dict hoặc ID chưa tồn tại, trả về
        if existing_dict is None or new_id not in existing_dict:
            return new_id

    # Trường hợp xung đột cực kỳ hiếm (100 lần), fallback sang UUID
    fallback_id = f"{prefix}_{uuid.uuid4().hex[:8].upper()}"

    if existing_dict is not None:
        while fallback_id in existing_dict:
            fallback_id = f"{prefix}_{uuid.uuid4().hex[:8].upper()}"

    return fallback_id
