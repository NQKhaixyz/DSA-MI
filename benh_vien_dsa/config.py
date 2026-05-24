"""
Module cấu hình toàn cục cho hệ thống quản lý bệnh viện.
Chứa các hằng số, enum đơn giản và danh sách khoa.
"""

# --- Mức độ ưu tiên trong hàng đợi (Queue Priority) ---
PRIORITY_EMERGENCY = 3  # Ưu tiên cấp cứu (cao nhất)
PRIORITY_APPOINTMENT = 2  # Ưu tiên bệnh nhân đặt hẹn trước
PRIORITY_WALKIN = 1  # Ưu tiên bệnh nhân đến trực tiếp (thấp nhất)

# --- Trạng thái bệnh nhân / lượt khám ---
STATUS_ACTIVE = "DangKham"  # Đang trong quá trình khám
STATUS_DISCHARGED = "DaXuatVien"  # Đã xuất viện / kết thúc khám
STATUS_EMERGENCY = "CapCuu"  # Trạng thái cấp cứu

# --- Giới hạn hệ thống ---
MAX_DEPARTMENTS_PER_DAY = 3  # Số khoa tối đa bệnh nhân có thể khám trong một ngày
MAX_SLOT_PER_TIMESLOT = 4  # Số bệnh nhân tối đa trong một khung giờ khám

# --- Danh sách các khoa trong bệnh viện ---
DEPARTMENTS = [
    "HoiSucCapCuu",  # Hồi sức cấp cứu
    "NoiTongQuat",  # Nội tổng quát
    "NgoaiKhoa",  # Ngoại khoa
    "NhiKhoa",  # Nhi khoa
    "SanKhoa",  # Sản khoa
    "TaiMuiHong",  # Tai mũi họng
    "DaLieu",  # Da liễu
    "Mat",  # Mắt
    "ChanThuongChinhHinh",  # Chấn thương chỉnh hình
]
