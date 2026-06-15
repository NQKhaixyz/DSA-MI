"""
Module quản lý trạng thái toàn cục (singleton pattern ở mức module).
Tất cả các dict lưu trữ dữ liệu hệ thống được khởi tạo tại đây.
"""

# --- Các từ điển toàn cục lưu trữ dữ liệu hệ thống ---

# Key: patientID (str) -> Value: đối tượng Patient
global_patients = {}

# Key: doctorID (str) -> Value: đối tượng Doctor
global_doctors = {}

# Key: departmentID (str) -> Value: đối tượng Department
global_departments = {}

# Key: serviceID (str) -> Value: đối tượng Service
global_services = {}

# Key: medicineID (str) -> Value: đối tượng Medicine
global_inventory = {}

# Key: (doctorID, date_str, timeSlot) -> Value: list[patientID]
global_appointments = {}

# Key: (departmentID, time_slot) -> int: số bệnh nhân đang check-in và khám
# Dùng để giới hạn tối đa MAX_SLOT_PER_TIMESLOT bệnh nhân/khoa/khung giờ
global_dept_timeslot_counts = {}

# Key: visitID (str) -> Value: đối tượng Visit
global_visits = {}

# Key: roomID (str) -> Value: đối tượng Room
global_rooms = {}

# Key: prescriptionID (str) -> Value: đối tượng Prescription
global_prescriptions = {}

# Key: billID (str) -> Value: đối tượng Bill
global_bills = {}


def reset_globals() -> None:
    """
    Xóa toàn bộ dữ liệu trong các từ điển toàn cục.
    Dùng khi cần reset hệ thống về trạng thái ban đầu (ví dụ: chạy test).
    """
    global_patients.clear()
    global_doctors.clear()
    global_departments.clear()
    global_services.clear()
    global_inventory.clear()
    global_appointments.clear()
    global_dept_timeslot_counts.clear()
    global_visits.clear()
    global_rooms.clear()
    global_prescriptions.clear()
    global_bills.clear()
