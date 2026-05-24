"""
Module benchmark hiệu năng hệ thống quản lý bệnh viện.
Chạy độc lập, chỉ dùng thư viện chuẩn (standard library).
"""

import time
import random
import os
import sys

# Đảm bảo console Windows in được tiếng Việt
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

# Import các module nội bộ của hệ thống
from benh_vien_dsa.global_state import reset_globals
import benh_vien_dsa.global_state as gs
from benh_vien_dsa.models import (
    Patient,
    Visit,
    Doctor,
    Department,
    Room,
    Service,
    Medicine,
    Prescription,
    Bill,
)
from benh_vien_dsa.algorithms import (
    generate_id,
    cycle_detection,
    strict_priority_call_next,
    shortest_queue_first,
    two_pass_validation,
    calculate_bill,
)
from benh_vien_dsa.mock_generator import (
    init_mock_data_large,
    generate_patients,
    generate_medicines,
)
from benh_vien_dsa.persistence import saveData, loadData
import benh_vien_dsa.config as config

TEMP_FILE = "temp_benchmark_data.json"


# =============================================================================
# Hàm benchmark cụ thể
# =============================================================================


def benchmark_search(count: int):
    """
    Benchmark thao tác tìm kiếm bệnh nhân theo patientID trong global_patients.
    - Tạo `count` bệnh nhân.
    - Thực hiện 1.000 lần tìm kiếm ngẫu nhiên (dict lookup O(1)).
    - Trả về (tổng_thời_gian, thời_gian_trung_bình_mỗi_lần).
    """
    reset_globals()
    generate_patients(count)

    patient_ids = list(gs.global_patients.keys())
    if not patient_ids:
        return 0.0, 0.0

    n_searches = 1000
    start = time.perf_counter()
    for _ in range(n_searches):
        pid = random.choice(patient_ids)
        _ = gs.global_patients[pid]
    end = time.perf_counter()

    total = end - start
    avg = total / n_searches
    return total, avg


def benchmark_priority_queue(count: int):
    """
    Benchmark hàng đợi đa mức ưu tiên (MultiLevelQueue).
    - Tạo 1 khoa, 1 bác sĩ, 1 phòng.
    - Enqueue `count` visits vào queue (chia đều 3 mức ưu tiên).
    - Đo thời gian dequeue toàn bộ `count` visits.
    - Trả về (tổng_thời_gian, thời_gian_trung_bình_mỗi_dequeue).
    """
    reset_globals()

    # Tạo cấu trúc tối thiểu để có 1 phòng hoạt động
    dept = Department(departmentID="DEPT_BM", departmentName="Khoa Benchmark")
    gs.global_departments[dept.departmentID] = dept

    doc = Doctor(
        doctorID="DOC_BM_001",
        fullName="Bác sĩ Benchmark",
        gender="Nam",
        dob="01/01/1980",
        phone="0900000001",
        email="doc@bm.vn",
        address="Hà Nội",
        departmentID=dept.departmentID,
        degree="BS",
        licenseNumber="12345678",
        yearsExperience=10,
    )
    gs.global_doctors[doc.doctorID] = doc
    dept.addDoctor(doc.doctorID)

    room = Room(
        roomID="ROOM_BM_001",
        departmentID=dept.departmentID,
        doctorID=doc.doctorID,
    )
    gs.global_rooms[room.roomID] = room
    dept.addRoom(room.roomID)

    # Tạo 1 bệnh nhân làm mẫu cho các visit
    patient = Patient(
        patientID="PAT_BM_001",
        fullName="BN Benchmark",
        gender="Nam",
        dob="01/01/1990",
        citizenID="001001001001",
        phone="0900000002",
        email="pat@bm.vn",
        address="Hà Nội",
        bloodType="O+",
    )
    gs.global_patients[patient.patientID] = patient

    priorities = [
        config.PRIORITY_WALKIN,
        config.PRIORITY_APPOINTMENT,
        config.PRIORITY_EMERGENCY,
    ]

    # Enqueue count visits
    for i in range(count):
        visit = Visit(
            visitID=f"VIS_BM_{i:06d}",
            patientID=patient.patientID,
            visitDate="01/01/2025",
            arrivalTime="08:00:00",
        )
        prio = priorities[i % 3]
        visit.queuePriority = prio
        gs.global_visits[visit.visitID] = visit
        room.addToQueue(visit, prio)

    # Dequeue toàn bộ và đo thời gian
    start = time.perf_counter()
    dequeued = 0
    while room.callNextPatient() is not None:
        dequeued += 1
    end = time.perf_counter()

    total = end - start
    avg = total / count if count else 0.0
    return total, avg


def benchmark_cycle_detection(count: int):
    """
    Benchmark thuật toán phát hiện chu trình (cycle_detection).
    - Tạo 1 Visit, thêm 3 khoa vào visited_departments (đạt giới hạn MAX_DEPARTMENTS_PER_DAY).
    - Thực hiện `count` lần kiểm tra cycle_detection với khoa ngẫu nhiên.
    - Trả về (tổng_thời_gian, thời_gian_trung_bình_mỗi_lần).
    """
    reset_globals()

    # Khởi tạo đủ các khoa để chọn ngẫu nhiên
    for dname in config.DEPARTMENTS:
        dept = Department(departmentID=dname, departmentName=dname)
        gs.global_departments[dname] = dept

    visit = Visit(
        visitID="VIS_CYC_001",
        patientID="PAT_CYC_001",
        visitDate="01/01/2025",
        arrivalTime="08:00:00",
    )
    # Giả lập bệnh nhân đã khám 3 khoa
    visit.visited_departments = set(config.DEPARTMENTS[:3])
    visit.departmentSequence = list(config.DEPARTMENTS[:3])
    visit.currentDepartmentIndex = 2

    # Các khoa chưa khám để test
    remaining = config.DEPARTMENTS[3:]
    pool = remaining if remaining else config.DEPARTMENTS

    start = time.perf_counter()
    for _ in range(count):
        dept_id = random.choice(pool)
        cycle_detection(visit, dept_id)
    end = time.perf_counter()

    total = end - start
    avg = total / count if count else 0.0
    return total, avg


def benchmark_two_pass_validation(count: int):
    """
    Benchmark thuật toán xác thực xuất kho 2 bước (two_pass_validation).
    - Tạo 50 loại thuốc trong inventory với stock rất lớn.
    - Tạo `count` đơn thuốc, mỗi đơn 5 loại thuốc ngẫu nhiên.
    - Đo thời gian chạy two_pass_validation cho toàn bộ đơn.
    - Trả về (tổng_thời_gian, thời_gian_trung_bình_mỗi_đơn).
    """
    reset_globals()

    # Tạo 50 loại thuốc, stockQuantity lớn để không bị cạn giữa chừng
    medicine_ids = []
    for i in range(50):
        mid = f"MED_BM_{i:03d}"
        med = Medicine(
            medicineID=mid,
            medicineName=f"Thuốc BM {i}",
            unitPrice=10000.0,
            stockQuantity=10_000_000,
        )
        gs.global_inventory[mid] = med
        medicine_ids.append(mid)

    # Tạo count đơn thuốc, mỗi đơn 5 loại thuốc
    prescriptions = []
    for i in range(count):
        pres = Prescription(
            prescriptionID=f"PRES_BM_{i:06d}",
            visitID="VIS_BM_001",
            doctorID="DOC_BM_001",
        )
        chosen = random.sample(medicine_ids, 5)
        for med_id in chosen:
            pres.addMedicine(med_id, random.randint(1, 10))
        prescriptions.append(pres)

    start = time.perf_counter()
    for pres in prescriptions:
        two_pass_validation(pres, gs.global_inventory)
    end = time.perf_counter()

    total = end - start
    avg = total / count if count else 0.0
    return total, avg


def benchmark_load_save(count: int):
    """
    Benchmark thao tác lưu và tải dữ liệu JSON (saveData / loadData).
    - Tạo `count` bệnh nhân và 100 visits.
    - Đo thời gian saveData() và loadData() riêng biệt.
    - Trả về (tổng_thời_gian, trung_bình_mỗi_thao_tác, thời_gian_lưu, thời_gian_tải).
    """
    reset_globals()

    generate_patients(count)

    # Đảm bảo có ít nhất 1 khoa để tạo visit
    if not gs.global_departments:
        dept = Department(departmentID="DEPT_DEFAULT", departmentName="Khoa Mặc định")
        gs.global_departments[dept.departmentID] = dept

    patients = list(gs.global_patients.values())
    depts = list(gs.global_departments.keys())

    for i in range(100):
        pat = random.choice(patients)
        visit = Visit(
            visitID=f"VIS_SAVE_{i:03d}",
            patientID=pat.patientID,
            visitDate="01/01/2025",
            arrivalTime="08:00:00",
        )
        num_depts = min(random.randint(1, 2), len(depts))
        for d in random.sample(depts, num_depts):
            visit.addDepartment(d)
        gs.global_visits[visit.visitID] = visit

    # Xóa file tạm cũ nếu tồn tại
    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)

    start_save = time.perf_counter()
    saveData(TEMP_FILE)
    end_save = time.perf_counter()
    save_time = end_save - start_save

    start_load = time.perf_counter()
    loadData(TEMP_FILE)
    end_load = time.perf_counter()
    load_time = end_load - start_load

    total = save_time + load_time
    avg = total / 2
    return total, avg, save_time, load_time


# =============================================================================
# Hàm chạy toàn bộ benchmark và in bảng tổng hợp
# =============================================================================


def run_all_benchmarks():
    """
    Chạy lần lượt các benchmark trên 3 kích thước dữ liệu: 10.000, 50.000, 100.000.
    Với 100k visits, chỉ chạy search và cycle_detection để tránh tiêu tốn quá nhiều bộ nhớ.
    Kết quả được in ra dưới dạng bảng tổng hợp có viền.
    """
    sizes = [10_000, 50_000, 100_000]
    results = []  # Danh sách tuple: (thao_tac, so_luong, tong_tg, avg_tg)

    # 1. Tìm kiếm ID (10k, 50k, 100k)
    print("[1/5] Benchmark tìm kiếm ID...")
    for size in sizes:
        total, avg = benchmark_search(size)
        results.append(("Tìm kiếm ID", size, total, avg))
        print(f"  - {size:,} patients: total={total:.4f}s, avg={avg:.6f}s")

    # 2. Priority Queue (10k, 50k) – bỏ qua 100k để tiết kiệm memory
    print("[2/5] Benchmark Priority Queue...")
    for size in [10_000, 50_000]:
        total, avg = benchmark_priority_queue(size)
        results.append(("Priority Queue", size, total, avg))
        print(f"  - {size:,} visits: total={total:.4f}s, avg={avg:.6f}s")

    # 3. Cycle Detection (10k, 50k, 100k)
    print("[3/5] Benchmark Cycle Detection...")
    for size in sizes:
        total, avg = benchmark_cycle_detection(size)
        results.append(("Cycle Detection", size, total, avg))
        print(f"  - {size:,} checks: total={total:.4f}s, avg={avg:.6f}s")

    # 4. Two-Pass Validation (10k, 50k, 100k)
    print("[4/5] Benchmark Two-Pass Validation...")
    for size in sizes:
        total, avg = benchmark_two_pass_validation(size)
        results.append(("Two-Pass Validation", size, total, avg))
        print(f"  - {size:,} prescriptions: total={total:.4f}s, avg={avg:.6f}s")

    # 5. Lưu/Tải JSON (10k, 50k, 100k patients + 100 visits)
    print("[5/5] Benchmark Lưu/Tải JSON...")
    for size in sizes:
        total, avg, save_t, load_t = benchmark_load_save(size)
        results.append(("Lưu/Tải JSON", size, total, avg))
        print(
            f"  - {size:,} patients: save={save_t:.4f}s, load={load_t:.4f}s, avg={avg:.4f}s"
        )

    # In bảng tổng hợp
    print("\n" + "=" * 75)
    print("BẢNG TỔNG HỢP BENCHMARK HIỆU NĂNG")
    print("=" * 75)

    sep = "+" + "-" * 22 + "+" + "-" * 16 + "+" + "-" * 14 + "+" + "-" * 18 + "+"
    header = f"| {'Thao tác':<20} | {'Số lượng':>14} | {'Thời gian':>12} | {'Trung bình/lần':>16} |"

    print(sep)
    print(header)
    print(sep)

    for op, size, total, avg in results:
        size_str = f"{size:,}".replace(",", ".")
        total_str = f"{total:.4f}s"
        avg_str = f"{avg:.6f}s"
        row = f"| {op:<20} | {size_str:>14} | {total_str:>12} | {avg_str:>16} |"
        print(row)

    print(sep)

    # Dọn dẹp file JSON tạm nếu còn sót lại
    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)
        print(f"\nĐã xóa file tạm: {TEMP_FILE}")


# =============================================================================
# Entry point
# =============================================================================

if __name__ == "__main__":
    run_all_benchmarks()
