"""
Module persistence.py: Đọc/ghi dữ liệu hệ thống ra file JSON.
Cung cấp hai hàm chính: saveData() và loadData().
"""

import json
import os

# Import tất cả các từ điển toàn cục từ global_state
from .global_state import (
    global_patients,
    global_doctors,
    global_departments,
    global_services,
    global_inventory,
    global_appointments,
    global_visits,
    global_rooms,
    global_prescriptions,
    global_bills,
)
from .global_state import reset_globals

# Import tất cả các model đã có to_dict() / from_dict()
from .models import (
    Patient,
    Doctor,
    Department,
    Service,
    Medicine,
    Appointment,
    Visit,
    Room,
    Prescription,
    Bill,
)


def saveData(filepath="hospital_data.json"):
    """
    Lưu toàn bộ dữ liệu hệ thống ra file JSON.

    Args:
        filepath (str): Đường dẫn file JSON cần ghi (mặc định "hospital_data.json").

    Returns:
        tuple: (bool, str) – (True, thông báo thành công) hoặc (False, thông báo lỗi).
    """
    try:
        # 1. Tạo dict chứa dữ liệu của toàn bộ hệ thống
        data_container = {
            "patients": {},
            "doctors": {},
            "departments": {},
            "services": {},
            "inventory": {},
            "appointments": {},
            "visits": {},
            "rooms": {},
            "prescriptions": {},
            "bills": {},
        }

        # 2. Lặp qua từng global dict và gọi to_dict() cho từng đối tượng
        for key, obj in global_patients.items():
            data_container["patients"][key] = obj.to_dict()
        for key, obj in global_doctors.items():
            data_container["doctors"][key] = obj.to_dict()
        for key, obj in global_departments.items():
            data_container["departments"][key] = obj.to_dict()
        for key, obj in global_services.items():
            data_container["services"][key] = obj.to_dict()
        for key, obj in global_inventory.items():
            data_container["inventory"][key] = obj.to_dict()

        # Đặc biệt với appointments: key là tuple -> chuyển thành string "doctorID|date|timeSlot"
        for (doctorID, date, timeSlot), app_list in global_appointments.items():
            serializable_key = f"{doctorID}|{date}|{timeSlot}"
            data_container["appointments"][serializable_key] = [
                app.to_dict() for app in app_list
            ]

        for key, obj in global_visits.items():
            data_container["visits"][key] = obj.to_dict()
        for key, obj in global_rooms.items():
            data_container["rooms"][key] = obj.to_dict()
        for key, obj in global_prescriptions.items():
            data_container["prescriptions"][key] = obj.to_dict()
        for key, obj in global_bills.items():
            data_container["bills"][key] = obj.to_dict()

        # 3. Ghi ra file JSON với định dạng đẹp, hỗ trợ Unicode
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data_container, f, ensure_ascii=False, indent=2)

        # 4. Trả về kết quả thành công
        return (True, f"Đã lưu dữ liệu ra {filepath}")

    except Exception as e:
        return (False, f"Lỗi khi lưu dữ liệu: {str(e)}")


def loadData(filepath="hospital_data.json"):
    """
    Tải toàn bộ dữ liệu hệ thống từ file JSON.

    Args:
        filepath (str): Đường dẫn file JSON cần đọc (mặc định "hospital_data.json").

    Returns:
        tuple: (bool, str) – (True, thông báo thành công) hoặc (False, thông báo lỗi).
    """
    # 1. Kiểm tra file tồn tại
    if not os.path.exists(filepath):
        return (False, "File không tồn tại")

    try:
        # 2. Đọc nội dung JSON từ file
        with open(filepath, "r", encoding="utf-8") as f:
            data_container = json.load(f)
    except json.JSONDecodeError:
        return (False, "File JSON không hợp lệ")
    except Exception as e:
        return (False, f"Lỗi khi đọc file: {str(e)}")

    # 3. Xóa dữ liệu cũ trong các từ điển toàn cục
    reset_globals()

    # 4. Load dữ liệu theo thứ tự

    # --- Patients ---
    for pid, pdata in data_container.get("patients", {}).items():
        patient_obj = Patient.from_dict(pdata)
        global_patients[pid] = patient_obj

    # --- Doctors ---
    for did, ddata in data_container.get("doctors", {}).items():
        doctor_obj = Doctor.from_dict(ddata)
        global_doctors[did] = doctor_obj

    # --- Departments ---
    for dept_id, dept_data in data_container.get("departments", {}).items():
        dept_obj = Department.from_dict(dept_data)
        global_departments[dept_id] = dept_obj

    # --- Services ---
    for sid, sdata in data_container.get("services", {}).items():
        service_obj = Service.from_dict(sdata)
        global_services[sid] = service_obj

    # --- Inventory (Medicine) ---
    for mid, mdata in data_container.get("inventory", {}).items():
        medicine_obj = Medicine.from_dict(mdata)
        global_inventory[mid] = medicine_obj

    # --- Appointments ---
    # Key string "doctorID|date|timeSlot" -> split thành tuple làm key cho global_appointments
    for key_str, app_list in data_container.get("appointments", {}).items():
        parts = key_str.split("|")
        if len(parts) == 3:
            tuple_key = (parts[0], parts[1], parts[2])
            global_appointments[tuple_key] = [
                Appointment.from_dict(app_data) for app_data in app_list
            ]

    # --- Visits ---
    for vid, vdata in data_container.get("visits", {}).items():
        visit_obj = Visit.from_dict(vdata)
        global_visits[vid] = visit_obj

    # --- Rooms ---
    for rid, rdata in data_container.get("rooms", {}).items():
        room_obj = Room.from_dict(rdata)
        # Lưu trữ tạm thời dữ liệu hàng đợi để refill sau
        room_obj.queue_data = rdata.get("queues", {})
        global_rooms[rid] = room_obj

    # Refill queue cho từng Room sau khi đã load xong global_visits
    for room_obj in global_rooms.values():
        queue_data = getattr(room_obj, "queue_data", {})
        for priority_str, visit_ids in queue_data.items():
            priority = int(priority_str)
            for visit_id in visit_ids:
                visit_obj = global_visits.get(visit_id)
                if visit_obj is not None:
                    room_obj.queues.enqueue(visit_obj, priority)
        # Xóa thuộc tính tạm sau khi đã refill (tùy chọn, giữ lại cũng không sao)
        if hasattr(room_obj, "queue_data"):
            delattr(room_obj, "queue_data")

    # --- Prescriptions ---
    for prid, prdata in data_container.get("prescriptions", {}).items():
        pres_obj = Prescription.from_dict(prdata)
        global_prescriptions[prid] = pres_obj

    # --- Bills ---
    for bid, bdata in data_container.get("bills", {}).items():
        bill_obj = Bill.from_dict(bdata)
        global_bills[bid] = bill_obj

    # 5. Trả về kết quả thành công
    return (True, "Đã tải dữ liệu thành công")
