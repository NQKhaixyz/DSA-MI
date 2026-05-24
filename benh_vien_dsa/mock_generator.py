"""
Module sinh dữ liệu mẫu (mock data) cho hệ thống quản lý bệnh viện.
Dùng cho mục đích demo, kiểm thử và benchmark.
"""

import random
import string
from datetime import datetime, timedelta

try:
    from . import config
    from . import global_state
    from . import models
    from . import algorithms
except ImportError:
    import config
    import global_state
    import models
    import algorithms

try:
    from faker import Faker

    _faker = Faker("vi_VN")
    _HAS_FAKER = True
except ImportError:
    _HAS_FAKER = False
    _faker = None

# =============================================================================
# Danh sách dữ liệu thô phục vụ sinh ngẫu nhiên
# =============================================================================

_HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Vũ", "Đặng", "Bùi", "Đỗ", "Hồ"]
_TEN_DEM = [
    "Văn",
    "Thị",
    "Hồng",
    "Minh",
    "Thanh",
    "Xuân",
    "Lan",
    "Hải",
    "Đức",
    "Như",
    "Anh",
    "Thế",
]
_TEN = [
    "A",
    "B",
    "C",
    "An",
    "Bình",
    "Chi",
    "Dung",
    "Giang",
    "Hà",
    "Hùng",
    "Linh",
    "Mai",
    "Nam",
    "Phương",
    "Quân",
    "Sơn",
    "Tùng",
    "Vy",
    "Yến",
    "Long",
]

_DUONG = [
    "Nguyễn Văn A",
    "Trần Hưng Đạo",
    "Lê Lợi",
    "Quang Trung",
    "Cách Mạng Tháng 8",
    "Phan Đình Phùng",
    "Nguyễn Trãi",
    "Lý Thường Kiệt",
]
_THANH_PHO = ["Hà Nội", "TP.HCM", "Đà Nẵng", "Hải Phòng", "Cần Thơ", "Huế", "Nha Trang"]

_MAU_MEDICINE = [
    "Paracetamol",
    "Ibuprofen",
    "Amoxicillin",
    "Vitamin C",
    "Omeprazole",
    "Metformin",
    "Amlodipine",
    "Salbutamol",
    "Cetirizine",
    "Oral Rehydration",
    "Acetaminophen",
    "Loperamide",
    "Ranitidine",
    "Ceftriaxone",
    "Azithromycin",
]

_SERVICE_BLUEPRINT = {
    "HoiSucCapCuu": [
        ("Cấp cứu đa chấn thương", 500000),
        ("Hồi sức tích cực", 800000),
        ("Xét nghiệm cấp tính", 300000),
    ],
    "NoiTongQuat": [
        ("Khám nội tổng quát", 200000),
        ("Siêu âm bụng", 350000),
        ("Nội soi tiêu hóa", 600000),
    ],
    "NgoaiKhoa": [
        ("Khám ngoại tổng quát", 200000),
        ("Cắt chỉ vết thương", 150000),
        ("Phẫu thuật nhỏ", 900000),
    ],
    "NhiKhoa": [
        ("Khám nhi tổng quát", 180000),
        ("Tiêm chủng", 120000),
        ("Xét nghiệm máu nhi", 250000),
    ],
    "SanKhoa": [
        ("Khám thai định kỳ", 250000),
        ("Siêu âm thai", 400000),
        ("Xét nghiệm sàng lọc", 350000),
    ],
    "TaiMuiHong": [
        ("Khám tai mũi họng", 200000),
        ("Nội soi tai", 350000),
        ("Xét nghiệm dị ứng", 300000),
    ],
    "DaLieu": [
        ("Khám da liễu", 200000),
        ("Soi da", 280000),
        ("Điều trị laser", 700000),
    ],
    "Mat": [
        ("Khám mắt tổng quát", 200000),
        ("Đo khúc xạ", 250000),
        ("Phẫu thuật mắt", 1200000),
    ],
    "ChanThuongChinhHinh": [
        ("Khám chấn thương", 200000),
        ("Chụp X-quang", 300000),
        ("Bó bột", 400000),
    ],
}

_TIME_SLOTS = ["08:00", "09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00"]


# =============================================================================
# Hàm tiện ích nội bộ
# =============================================================================


def _random_date(start_year: int, end_year: int) -> str:
    """Sinh ngày ngẫu nhiên trong khoảng [start_year, end_year], định dạng dd/mm/yyyy."""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta_days = (end - start).days
    random_day = start + timedelta(days=random.randint(0, delta_days))
    return random_day.strftime("%d/%m/%Y")


def _random_name() -> str:
    """Sinh họ tên ngẫu nhiên (tiếng Việt); dùng faker nếu có."""
    if _HAS_FAKER and _faker:
        return _faker.name()
    return f"{random.choice(_HO)} {random.choice(_TEN_DEM)} {random.choice(_TEN)}"


def _random_address() -> str:
    """Sinh địa chỉ ngẫu nhiên; dùng faker nếu có."""
    if _HAS_FAKER and _faker:
        return _faker.address()
    return (
        f"{random.randint(1, 200)} {random.choice(_DUONG)}, {random.choice(_THANH_PHO)}"
    )


def _random_phone() -> str:
    """Sinh SĐT ngẫu nhiên dạng 09xxxxxxxx."""
    return "09" + "".join(random.choices(string.digits, k=8))


def _random_citizen_id() -> str:
    """Sinh CCCD ngẫu nhiên 12 chữ số."""
    return "".join(random.choices(string.digits, k=12))


def _get_or_create_dept(dept_id: str) -> models.Department:
    """Lấy khoa từ global_departments; nếu chưa có thì tạo mới."""
    if dept_id not in global_state.global_departments:
        dept = models.Department(departmentID=dept_id, departmentName=dept_id)
        global_state.global_departments[dept_id] = dept
    return global_state.global_departments[dept_id]


def _create_services_for_depts(dept_ids: list[str]) -> None:
    """Tạo dịch vụ theo blueprint cho danh sách khoa chỉ định."""
    for dept_id in dept_ids:
        dept = _get_or_create_dept(dept_id)
        services = _SERVICE_BLUEPRINT.get(
            dept_id,
            [
                (f"Dịch vụ {dept_id} 1", random.randint(100, 5000) * 100),
                (f"Dịch vụ {dept_id} 2", random.randint(100, 5000) * 100),
                (f"Dịch vụ {dept_id} 3", random.randint(100, 5000) * 100),
            ],
        )
        for svc_name, price in services:
            svc = models.Service(
                serviceID=algorithms.generate_id("SVC"),
                serviceName=svc_name,
                departmentID=dept_id,
                price=float(price),
            )
            global_state.global_services[svc.serviceID] = svc
            dept.addService(svc.serviceID)


# =============================================================================
# Các hàm sinh dữ liệu chính
# =============================================================================


def init_mock_data_small() -> None:
    """
    Tạo dữ liệu demo nhỏ cho CLI chạy thử.
    Bao gồm: 5 khoa đầu tiên, mỗi khoa 1-2 phòng, 2 bác sĩ,
    ít nhất 3 dịch vụ mỗi khoa, 10 loại thuốc, 5 bệnh nhân.
    Không tạo visits/appointments trong hàm này.
    """
    # --- 1. Tạo 5 khoa đầu tiên ---
    small_depts = config.DEPARTMENTS[:5]
    for dept_name in small_depts:
        _get_or_create_dept(dept_name)

    # --- 2. Tạo 2 bác sĩ mỗi khoa ---
    for dept_name in small_depts:
        dept = global_state.global_departments[dept_name]
        for i in range(2):
            doc = models.Doctor(
                doctorID=algorithms.generate_id("DOC"),
                fullName=_random_name(),
                gender=random.choice(["Nam", "Nữ"]),
                dob=_random_date(1960, 1995),
                phone=_random_phone(),
                email=f"doctor_{dept_name.lower()}_{i}@hospital.vn",
                address=_random_address(),
                departmentID=dept_name,
                degree=random.choice(["BS", "ThS", "TS", "PGS", "GS"]),
                licenseNumber="".join(random.choices(string.digits, k=8)),
                yearsExperience=random.randint(1, 30),
            )
            global_state.global_doctors[doc.doctorID] = doc
            dept.addDoctor(doc.doctorID)

    # --- 3. Tạo 1-2 phòng mỗi khoa ---
    for dept_name in small_depts:
        dept = global_state.global_departments[dept_name]
        num_rooms = random.randint(1, 2)
        docs_in_dept = [
            d_id for d_id in dept.doctorIDs if d_id in global_state.global_doctors
        ]
        for _ in range(num_rooms):
            doc_id = (
                random.choice(docs_in_dept)
                if docs_in_dept
                else algorithms.generate_id("DOC")
            )
            room = models.Room(
                roomID=algorithms.generate_id("ROOM"),
                departmentID=dept_name,
                doctorID=doc_id,
            )
            global_state.global_rooms[room.roomID] = room
            dept.addRoom(room.roomID)
            # Cập nhật roomID cho bác sĩ nếu chưa có
            if doc_id in global_state.global_doctors:
                doc = global_state.global_doctors[doc_id]
                if doc.roomID is None:
                    doc.roomID = room.roomID

    # --- 4. Tạo dịch vụ theo blueprint ---
    _create_services_for_depts(small_depts)

    # --- 5. Tạo 10 loại thuốc ---
    generate_medicines(10)

    # --- 6. Tạo 5 bệnh nhân ---
    generate_patients(5)


def generate_patients(count: int = 10000) -> None:
    """
    Sinh `count` bệnh nhân ngẫu nhiên và thêm vào global_patients.
    Tên: ngẫu nhiên từ danh sách họ + tên đệm + tên (hoặc faker).
    SĐT: 09 + 8 chữ số.
    CCCD: 12 chữ số.
    Ngày sinh: ngẫu nhiên 1950-2010.
    BHYT: ~30% có.
    """
    for _ in range(count):
        patient = models.Patient(
            patientID=algorithms.generate_id("PAT"),
            fullName=_random_name(),
            gender=random.choice(["Nam", "Nữ"]),
            dob=_random_date(1950, 2010),
            citizenID=_random_citizen_id(),
            phone=_random_phone(),
            email=f"patient{random.randint(1, 999999)}@email.com",
            address=_random_address(),
            bloodType=random.choice(["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]),
            hasInsurance=random.random() < 0.30,
        )
        global_state.global_patients[patient.patientID] = patient


def generate_doctors(count: int = 20) -> None:
    """
    Sinh `count` bác sĩ ngẫu nhiên, gán vào các khoa DEPARTMENTS (round-robin/ngẫu nhiên).
    Mỗi bác sĩ gán vào 1 phòng của khoa đó nếu phòng đã tạo.
    """
    if not global_state.global_departments:
        for dept_name in config.DEPARTMENTS:
            _get_or_create_dept(dept_name)

    dept_ids = list(global_state.global_departments.keys())

    for i in range(count):
        dept_id = random.choice(dept_ids)
        doc = models.Doctor(
            doctorID=algorithms.generate_id("DOC"),
            fullName=_random_name(),
            gender=random.choice(["Nam", "Nữ"]),
            dob=_random_date(1960, 1995),
            phone=_random_phone(),
            email=f"doctor{i}@hospital.vn",
            address=_random_address(),
            departmentID=dept_id,
            degree=random.choice(["BS", "ThS", "TS", "PGS", "GS"]),
            licenseNumber="".join(random.choices(string.digits, k=8)),
            yearsExperience=random.randint(1, 40),
        )

        dept = global_state.global_departments[dept_id]
        if dept.roomIDs:
            room_id = random.choice(dept.roomIDs)
            doc.roomID = room_id

        global_state.global_doctors[doc.doctorID] = doc
        dept.addDoctor(doc.doctorID)


def generate_rooms() -> None:
    """
    Với mỗi khoa trong DEPARTMENTS, tạo 1-2 phòng (Room).
    Gán doctorID ngẫu nhiên thuộc khoa đó; nếu chưa có bác sĩ thì tạo tạm.
    """
    for dept_id in config.DEPARTMENTS:
        dept = _get_or_create_dept(dept_id)
        num_rooms = random.randint(1, 2)

        for _ in range(num_rooms):
            docs_in_dept = [
                d_id for d_id in dept.doctorIDs if d_id in global_state.global_doctors
            ]
            if docs_in_dept:
                doc_id = random.choice(docs_in_dept)
            else:
                # Tạo tạm bác sĩ nếu khoa chưa có ai
                doc = models.Doctor(
                    doctorID=algorithms.generate_id("DOC"),
                    fullName=_random_name(),
                    gender=random.choice(["Nam", "Nữ"]),
                    dob=_random_date(1960, 1995),
                    phone=_random_phone(),
                    email=f"temp@{dept_id.lower()}.vn",
                    address=_random_address(),
                    departmentID=dept_id,
                    degree="BS",
                    licenseNumber="".join(random.choices(string.digits, k=8)),
                    yearsExperience=random.randint(1, 10),
                )
                global_state.global_doctors[doc.doctorID] = doc
                dept.addDoctor(doc.doctorID)
                doc_id = doc.doctorID

            room = models.Room(
                roomID=algorithms.generate_id("ROOM"),
                departmentID=dept_id,
                doctorID=doc_id,
            )
            global_state.global_rooms[room.roomID] = room
            dept.addRoom(room.roomID)

            # Cập nhật roomID cho bác sĩ nếu chưa có
            doc = global_state.global_doctors[doc_id]
            if doc.roomID is None:
                doc.roomID = room.roomID


def generate_services() -> None:
    """
    Tạo dịch vụ theo blueprint (mỗi khoa ít nhất 3 dịch vụ).
    Dùng giá cụ thể từ blueprint hoặc giá ngẫu nhiên nếu không có.
    """
    _create_services_for_depts(config.DEPARTMENTS)


def generate_medicines(count: int = 50) -> None:
    """
    Sinh `count` loại thuốc ngẫu nhiên: tên ngẫu nhiên,
    unitPrice trong khoảng 10.000 - 500.000,
    stockQuantity trong khoảng 50 - 1.000.
    """
    for _ in range(count):
        name = f"{random.choice(_MAU_MEDICINE)} {random.choice(string.ascii_uppercase)}{random.randint(1, 999)}"
        medicine = models.Medicine(
            medicineID=algorithms.generate_id("MED"),
            medicineName=name,
            unitPrice=float(random.randint(100, 5000) * 100),
            stockQuantity=random.randint(50, 1000),
        )
        global_state.global_inventory[medicine.medicineID] = medicine


def generate_visits(count: int = 1000) -> None:
    """
    Sinh `count` visits ngẫu nhiên cho các bệnh nhân đã có:
    - Chọn random patient.
    - Chọn 1-3 khoa ngẫu nhiên.
    - Priority random (1 hoặc 2).
      Nếu priority=2 thì tạo Appointment luôn (nếu slot < 4).
    - Gọi shortest_queue_first để xếp vào phòng của khoa đầu tiên.
    Lưu vào global_visits.
    """
    patients = list(global_state.global_patients.values())
    if not patients:
        return

    depts = list(global_state.global_departments.values())
    if not depts:
        return

    for _ in range(count):
        patient = random.choice(patients)
        num_depts = random.randint(1, 3)
        chosen_depts = random.sample(depts, min(num_depts, len(depts)))
        chosen_dept_ids = [d.departmentID for d in chosen_depts]
        if not chosen_dept_ids:
            continue

        priority = random.choice([config.PRIORITY_WALKIN, config.PRIORITY_APPOINTMENT])
        visit_date = _random_date(2024, 2025)
        arrival_time = f"{random.randint(7, 17):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"

        # Nếu priority=2, thử tạo Appointment cho khoa đầu tiên
        if priority == config.PRIORITY_APPOINTMENT:
            first_dept = global_state.global_departments.get(chosen_dept_ids[0])
            if first_dept and first_dept.doctorIDs:
                doc_id = random.choice(first_dept.doctorIDs)
                # Thử tìm slot còn trống (tối đa 5 lần)
                for _ in range(5):
                    slot = random.choice(_TIME_SLOTS)
                    apt_key = (doc_id, visit_date, slot)
                    slot_list = global_state.global_appointments.setdefault(apt_key, [])
                    if len(slot_list) < config.MAX_SLOT_PER_TIMESLOT:
                        apt = models.Appointment(
                            appointmentID=algorithms.generate_id("APT"),
                            patientID=patient.patientID,
                            departmentSequence=chosen_dept_ids,
                            selectedDoctorID=doc_id,
                            appointmentDate=visit_date,
                            timeSlot=slot,
                        )
                        slot_list.append(apt)
                        break

        visit_id = algorithms.generate_id("VISIT")
        visit = models.Visit(
            visitID=visit_id,
            patientID=patient.patientID,
            visitDate=visit_date,
            arrivalTime=arrival_time,
        )
        visit.queuePriority = priority

        for dept_id in chosen_dept_ids:
            ok, _ = visit.addDepartment(dept_id)
            if not ok:
                break

        if visit.departmentSequence:
            visit.currentDepartmentIndex = 0
            first_dept_id = visit.departmentSequence[0]
            try:
                dept = global_state.global_departments[first_dept_id]
                algorithms.shortest_queue_first(dept, visit)
            except (KeyError, ValueError):
                # Khoa không có phòng hoặc lỗi khác: bỏ qua
                pass

            global_state.global_visits[visit.visitID] = visit


def init_mock_data_large(patient_count: int = 10000, visit_count: int = 5000) -> None:
    """
    Sinh bộ dữ liệu lớn để benchmark / test hiệu năng.
    Gọi lần lượt: patients -> doctors -> rooms -> services -> medicines -> visits.
    """
    generate_patients(patient_count)
    generate_doctors(30)
    generate_rooms()
    generate_services()
    generate_medicines(100)
    generate_visits(visit_count)
