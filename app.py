"""
app.py — Flask API Backend cho hệ thống quản lý bệnh viện (benh_vien_dsa).
Cung cấp REST API JSON cho toàn bộ các nghiệp vụ: tiếp đón, khám bệnh, thanh toán.
"""

from flask import Flask, render_template, jsonify, request
import json
import os

# Import các module nghiệp vụ từ gói benh_vien_dsa
from benh_vien_dsa import (
    config,
    global_state,
    models,
    algorithms,
    services,
    persistence,
    mock_generator,
)
from benh_vien_dsa.global_state import reset_globals
from benh_vien_dsa.services import ReceptionService, DoctorService, PharmacyService
from benh_vien_dsa.mock_generator import init_mock_data_small

# =============================================================================
# Khởi tạo Flask app và các service
# =============================================================================
app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0


@app.after_request
def inject_api_fetch_override(response):
    if response.content_type and "text/html" in response.content_type:
        html = response.get_data(as_text=True)
        if "</body>" in html and "_orig=window.apiFetch" not in html:
            override = (
                "<script>"
                "const _orig=window.apiFetch;"
                "window.apiFetch=async function(u,o){"
                "var d=await _orig(u,o);"
                'if(d&&d.success===false)throw new Error(d.message||"Lỗi");'
                "return d;};"
                "</script>"
            )
            html = html.replace("</body>", override + "</body>")
            response.set_data(html.encode())
    return response


reception_svc = ReceptionService()
doctor_svc = DoctorService()
pharmacy_svc = PharmacyService()


# =============================================================================
# Helper: xử lý lỗi chung cho mọi endpoint
# =============================================================================
def handle_error(e: Exception):
    """Trả về JSON lỗi với status 500."""
    return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# Dashboard & Thống kê
# =============================================================================
@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    """Trả về các chỉ số tổng quan của hệ thống."""
    try:
        from datetime import datetime

        now = datetime.now()

        active_visits = 0
        emergency_count = 0
        waiting_list = []

        for v in global_state.global_visits.values():
            if v.status in (
                config.STATUS_WAITING_CHECKIN,
                config.STATUS_ACTIVE,
                config.STATUS_EMERGENCY,
            ):
                active_visits += 1
                if v.status == config.STATUS_EMERGENCY:
                    emergency_count += 1

                # Thêm vào danh sách chờ nếu đang trong hàng đợi
                patient = global_state.global_patients.get(v.patientID)
                room = (
                    global_state.global_rooms.get(v.assignedRoomID)
                    if v.assignedRoomID
                    else None
                )

                # Bỏ qua nếu bệnh nhân đang được khám (không phải "đang chờ")
                if room and room.currentVisitID == v.visitID:
                    continue

                dept_name = "--"
                if room and room.departmentID in global_state.global_departments:
                    dept_name = global_state.global_departments[
                        room.departmentID
                    ].departmentName

                # Tính thời gian chờ
                wait_time_str = "--"
                if v.arrivalTime:
                    try:
                        arr = datetime.strptime(v.arrivalTime, "%H:%M:%S")
                        delta = now - arr.replace(
                            year=now.year, month=now.month, day=now.day
                        )
                        if delta.total_seconds() < 0:
                            delta = now - arr.replace(
                                year=now.year, month=now.month, day=now.day - 1
                            )
                        mins = int(delta.total_seconds() // 60)
                        wait_time_str = f"{mins} phút"
                    except:
                        pass

                waiting_list.append(
                    {
                        "visitID": v.visitID,
                        "patientName": patient.fullName if patient else "Không rõ",
                        "departmentName": dept_name,
                        "roomName": room.roomID if room else "--",
                        "priority": v.queuePriority,
                        "status": v.status,
                        "waitTime": wait_time_str,
                    }
                )

        total_queue_sizes = sum(
            room.getQueueSize() for room in global_state.global_rooms.values()
        )

        return jsonify(
            {
                "success": True,
                "patients_count": len(global_state.global_patients),
                "doctors_count": len(global_state.global_doctors),
                "departments_count": len(global_state.global_departments),
                "rooms_count": len(global_state.global_rooms),
                "active_visits": active_visits,
                "emergency_count": emergency_count,
                "total_queue_sizes": total_queue_sizes,
                "waiting_list": waiting_list,
            }
        )
    except Exception as e:
        return handle_error(e)


# =============================================================================
# Patients — Bệnh nhân
# =============================================================================
@app.route("/api/patients", methods=["GET"])
def api_patients():
    """Lấy danh sách tất cả bệnh nhân."""
    try:
        data = [p.to_dict() for p in global_state.global_patients.values()]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return handle_error(e)


@app.route("/api/patients", methods=["POST"])
def api_patients_create():
    """Tạo bệnh nhân mới từ JSON body."""
    try:
        body = request.get_json(force=True) or {}
        patient_id = algorithms.generate_id("BN")
        patient = models.Patient(
            patientID=patient_id,
            fullName=body.get("fullName", "Chưa cập nhật"),
            gender=body.get("gender", "Không rõ"),
            dob=body.get("dob", "01/01/1970"),
            citizenID=body.get("citizenID", "000000000000"),
            phone=body.get("phone", "0000000000"),
            email=body.get("email", "unknown@example.com"),
            address=body.get("address", "Không rõ"),
            bloodType=body.get("bloodType", "O+"),
            hasInsurance=body.get("hasInsurance", False),
        )
        global_state.global_patients[patient_id] = patient
        return jsonify({"success": True, "data": patient.to_dict()}), 201
    except Exception as e:
        return handle_error(e)


# =============================================================================
# Doctors — Bác sĩ
# =============================================================================
@app.route("/api/doctors", methods=["GET"])
def api_doctors():
    """Lấy danh sách tất cả bác sĩ."""
    try:
        data = [d.to_dict() for d in global_state.global_doctors.values()]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return handle_error(e)


# =============================================================================
# Departments — Khoa
# =============================================================================
@app.route("/api/departments", methods=["GET"])
def api_departments():
    """Lấy danh sách tất cả khoa."""
    try:
        data = [d.to_dict() for d in global_state.global_departments.values()]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return handle_error(e)


@app.route("/api/departments/<id>/rooms", methods=["GET"])
def api_department_rooms(id):
    """Lấy danh sách phòng thuộc một khoa."""
    try:
        rooms = [
            r.to_dict()
            for r in global_state.global_rooms.values()
            if r.departmentID == id
        ]
        return jsonify({"success": True, "data": rooms})
    except Exception as e:
        return handle_error(e)


@app.route("/api/departments/<id>/doctors", methods=["GET"])
def api_department_doctors(id):
    """Lấy danh sách bác sĩ thuộc một khoa."""
    try:
        doctors = [
            d.to_dict()
            for d in global_state.global_doctors.values()
            if d.departmentID == id
        ]
        return jsonify({"success": True, "data": doctors})
    except Exception as e:
        return handle_error(e)


# =============================================================================
# Rooms & Queue — Phòng khám và hàng đợi
# =============================================================================
@app.route("/api/rooms", methods=["GET"])
def api_rooms():
    """Lấy danh sách tất cả phòng khám."""
    try:
        data = [r.to_dict() for r in global_state.global_rooms.values()]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return handle_error(e)


@app.route("/api/rooms/<id>/queue", methods=["GET"])
def api_room_queue(id):
    """Trả chi tiết hàng đợi của một phòng: các mức ưu tiên và lượt khám hiện tại."""
    try:
        room = global_state.global_rooms.get(id)
        if not room:
            return jsonify({"success": False, "error": "Không tìm thấy phòng"}), 404

        def _visit_to_queue_item(v):
            """Chuyển Visit thành object gọn nhẹ cho queue display."""
            patient = global_state.global_patients.get(v.patientID)
            return {
                "visitID": v.visitID,
                "patientID": v.patientID,
                "patientName": patient.fullName if patient else "Không rõ",
                "queuePriority": v.queuePriority,
                "priorityLabel": (
                    "Cấp cứu"
                    if v.queuePriority == 3
                    else ("Ưu tiên" if v.queuePriority == 2 else "Thường")
                ),
                "severity": v.severity,
                "status": v.status,
            }

        queue_data = {
            "priority3": [
                _visit_to_queue_item(v) for v in room.queues.queues.get(3, [])
            ],
            "priority2": [
                _visit_to_queue_item(v) for v in room.queues.queues.get(2, [])
            ],
            "priority1": [
                _visit_to_queue_item(v) for v in room.queues.queues.get(1, [])
            ],
            "currentVisit": room.currentVisitID,
            "currentVisitInfo": None,
        }

        # Thêm thông tin chi tiết của bệnh nhân đang khám
        if room.currentVisitID:
            current_visit = global_state.global_visits.get(room.currentVisitID)
            if current_visit:
                patient = global_state.global_patients.get(current_visit.patientID)
                queue_data["currentVisitInfo"] = {
                    "patientName": patient.fullName if patient else "Không rõ",
                    "stt": room.getQueueSize()
                    + 1,  # STT = số người chờ + người đang khám
                    "visitedDepartments": list(current_visit.visited_departments),
                    "departmentSequence": current_visit.departmentSequence,
                }

        return jsonify({"success": True, "data": queue_data})
    except Exception as e:
        return handle_error(e)


# =============================================================================
# Services — Dịch vụ y tế
# =============================================================================
@app.route("/api/services", methods=["GET"])
def api_services():
    """Lấy danh sách tất cả dịch vụ y tế."""
    try:
        data = [s.to_dict() for s in global_state.global_services.values()]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return handle_error(e)


# =============================================================================
# Medicines — Thuốc trong kho
# =============================================================================
@app.route("/api/medicines", methods=["GET"])
def api_medicines():
    """Lấy danh sách tất cả thuốc trong kho."""
    try:
        data = [m.to_dict() for m in global_state.global_inventory.values()]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return handle_error(e)


# =============================================================================
# Appointments & Check-in — Lễ tân
# =============================================================================
@app.route("/api/appointments", methods=["POST"])
def api_appointments():
    """Đăng ký lịch hẹn khám online."""
    try:
        body = request.get_json(force=True) or {}
        ok, msg = reception_svc.register_online(
            patient_id=body.get("patient_id", ""),
            department_sequence=body.get("department_sequence", []),
            selected_doctor_id=body.get("selected_doctor_id", ""),
            appointment_date=body.get("date", ""),
            time_slot=body.get("time_slot", ""),
        )
        return jsonify({"success": ok, "message": msg})
    except Exception as e:
        return handle_error(e)


@app.route("/api/checkin", methods=["POST"])
def api_checkin():
    """Tạo bệnh nhân + lượt khám mới từ form tiếp đón (chưa xếp queue)."""
    try:
        body = request.get_json(force=True) or {}
        # Nếu frontend không gửi patient_id, tự động tạo ID duy nhất
        patient_id = body.get("patient_id", "")
        if not patient_id:
            patient_id = algorithms.generate_id("BN")
        visit, msg = reception_svc.checkin_patient(
            patient_id=patient_id,
            full_name=body.get("full_name"),
            gender=body.get("gender"),
            dob=body.get("dob"),
            citizen_id=body.get("citizen_id"),
            phone=body.get("phone"),
            address=body.get("address"),
            blood_type=body.get("blood_type"),
            severity=body.get("severity", "BinhThuong"),
            department_sequence=body.get("department_sequence", []),
            is_appointment=body.get("is_appointment", False),
            appointment_date=body.get("appointment_date"),
            time_slot=body.get("time_slot"),
            selected_doctor_id=body.get("selected_doctor_id"),
            has_insurance=body.get("hasInsurance", False),
        )
        return jsonify(
            {
                "success": visit is not None,
                "message": msg,
                "visit": visit.to_dict() if visit else None,
            }
        )
    except Exception as e:
        return handle_error(e)


@app.route("/api/confirm-checkin/<visit_id>", methods=["POST"])
def api_confirm_checkin(visit_id):
    """Xác nhận check-in: đẩy bệnh nhân vào hàng đợi phòng khám."""
    try:
        visit, msg = reception_svc.confirm_checkin(visit_id)
        return jsonify(
            {
                "success": visit is not None,
                "message": msg,
                "visit": visit.to_dict() if visit else None,
            }
        )
    except Exception as e:
        return handle_error(e)


@app.route("/api/today-visits", methods=["GET"])
def api_today_visits():
    """Trả danh sách lượt khám trong ngày (cả trực tiếp và đặt lịch) kèm thông tin BN."""
    try:
        from datetime import datetime

        today_str = datetime.now().strftime("%d/%m/%Y")
        data = []
        for visit in global_state.global_visits.values():
            if visit.visitDate == today_str:
                patient = global_state.global_patients.get(visit.patientID)
                dept_name = "--"
                current_dept = visit.getCurrentDepartment()
                if current_dept and current_dept in global_state.global_departments:
                    dept_name = global_state.global_departments[
                        current_dept
                    ].departmentName

                # Xác định hình thức tiếp đón
                reception_type = "Khám trực tiếp"
                if getattr(visit, "appointmentID", None):
                    reception_type = "Có đặt lịch trước"
                elif visit.queuePriority == config.PRIORITY_APPOINTMENT:
                    reception_type = "Có đặt lịch trước"

                data.append(
                    {
                        "visitID": visit.visitID,
                        "patientID": visit.patientID,
                        "patientName": patient.fullName if patient else "Không rõ",
                        "receptionType": reception_type,
                        "departmentName": dept_name,
                        "status": visit.status,
                        "queuePriority": visit.queuePriority,
                    }
                )
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return handle_error(e)


@app.route("/api/rooms/<id>/services", methods=["GET"])
def api_room_services(id):
    """Trả danh sách dịch vụ thuộc khoa của phòng khám."""
    try:
        room = global_state.global_rooms.get(id)
        if not room:
            return jsonify({"success": False, "error": "Không tìm thấy phòng"}), 404
        services = [
            s.to_dict()
            for s in global_state.global_services.values()
            if s.departmentID == room.departmentID
        ]
        return jsonify({"success": True, "data": services})
    except Exception as e:
        return handle_error(e)


@app.route("/api/emergency", methods=["POST"])
def api_emergency():
    """Kích hoạt chế độ cấp cứu cho một lượt khám."""
    try:
        body = request.get_json(force=True) or {}
        ok, msg = reception_svc.activate_emergency(body.get("visit_id", ""))
        return jsonify({"success": ok, "message": msg})
    except Exception as e:
        return handle_error(e)


# =============================================================================
# Doctor actions — Bác sĩ
# =============================================================================
@app.route("/api/call-next", methods=["POST"])
def api_call_next():
    """Gọi bệnh nhân tiếp theo trong phòng khám."""
    try:
        body = request.get_json(force=True) or {}
        visit, msg = doctor_svc.call_next_patient(body.get("room_id", ""))
        return jsonify(
            {
                "success": visit is not None,
                "message": msg,
                "visit": visit.to_dict() if visit else None,
            }
        )
    except Exception as e:
        return handle_error(e)


@app.route("/api/add-service", methods=["POST"])
def api_add_service():
    """Thêm dịch vụ y tế vào lượt khám."""
    try:
        body = request.get_json(force=True) or {}
        visit_id = body.get("visit_id", "")
        service_ids = body.get("service_ids", [])
        results = []
        for sid in service_ids:
            ok, msg = doctor_svc.add_service(visit_id, sid)
            results.append({"service_id": sid, "success": ok, "message": msg})
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return handle_error(e)


@app.route("/api/add-prescription", methods=["POST"])
def api_add_prescription():
    """Kê đơn thuốc cho lượt khám."""
    try:
        body = request.get_json(force=True) or {}
        ok, msg = doctor_svc.add_prescription(
            visit_id=body.get("visit_id", ""),
            doctor_id=body.get("doctor_id", ""),
            medicine_list=body.get("medicine_list", {}),
            note=body.get("note", ""),
        )
        return jsonify({"success": ok, "message": msg})
    except Exception as e:
        return handle_error(e)


@app.route("/api/transfer", methods=["POST"])
def api_transfer():
    """Chuyển bệnh nhân sang khoa mới."""
    try:
        body = request.get_json(force=True) or {}
        ok, msg = doctor_svc.transfer_department(
            body.get("visit_id", ""), body.get("new_dept_id", "")
        )
        return jsonify({"success": ok, "message": msg})
    except Exception as e:
        return handle_error(e)


@app.route("/api/complete", methods=["POST"])
def api_complete():
    """Hoàn tất khám cho lượt khám hiện tại."""
    try:
        body = request.get_json(force=True) or {}
        ok, msg = doctor_svc.complete_examination(body.get("visit_id", ""))
        return jsonify({"success": ok, "message": msg})
    except Exception as e:
        return handle_error(e)


# =============================================================================
# Pharmacy & Payment — Nhà thuốc / Thanh toán
# =============================================================================
@app.route("/api/patient-visits/<patient_id>", methods=["GET"])
def api_patient_visits(patient_id):
    """Tìm lượt khám chưa xuất viện của bệnh nhân."""
    try:
        visit = pharmacy_svc.get_visit_by_patient(patient_id)
        return jsonify(
            {
                "success": True,
                "visit": visit.to_dict() if visit else None,
            }
        )
    except Exception as e:
        return handle_error(e)


@app.route("/api/payment-detail/<visit_id>", methods=["GET"])
def api_payment_detail(visit_id):
    """
    Trả về thông tin đầy đủ để thanh toán:
    - Tên bệnh nhân, bác sĩ, khoa
    - Danh sách dịch vụ (tên + giá)
    - Danh sách thuốc (tên + đơn giá + số lượng) — lấy từ Kho dược
    - Trạng thái BHYT
    """
    try:
        visit = global_state.global_visits.get(visit_id)
        if not visit:
            return jsonify({"success": False, "error": "Không tìm thấy lượt khám"}), 404

        patient = global_state.global_patients.get(visit.patientID)

        # Dịch vụ đã dùng
        services_list = []
        for sid in visit.usedServiceIDs:
            svc = global_state.global_services.get(sid)
            if svc:
                services_list.append(
                    {
                        "serviceID": sid,
                        "serviceName": svc.serviceName,
                        "price": svc.price,
                    }
                )

        # Thuốc trong đơn — lấy đơn giá từ Kho dược (Medicine Inventory)
        medicines_list = []
        if visit.prescriptionID:
            pres = global_state.global_prescriptions.get(visit.prescriptionID)
            if pres:
                for med_id, qty in pres.medicineList.items():
                    med = global_state.global_inventory.get(med_id)
                    if med:
                        medicines_list.append(
                            {
                                "medicineID": med_id,
                                "medicineName": med.medicineName,
                                "unitPrice": med.unitPrice,
                                "quantity": qty,
                                "total": med.unitPrice * qty,
                            }
                        )

        # Tìm bác sĩ và khoa
        doctor_name = "--"
        dept_name = "--"
        if visit.assignedDoctorIDs:
            doc = global_state.global_doctors.get(visit.assignedDoctorIDs[0])
            if doc:
                doctor_name = doc.fullName
                dept = global_state.global_departments.get(doc.departmentID)
                if dept:
                    dept_name = dept.departmentName

        return jsonify(
            {
                "success": True,
                "visit": {
                    "visitID": visit.visitID,
                    "patientID": visit.patientID,
                    "patientName": patient.fullName if patient else "--",
                    "hasInsurance": patient.hasInsurance if patient else False,
                    "doctorName": doctor_name,
                    "departmentName": dept_name,
                    "services": services_list,
                    "medicines": medicines_list,
                    "status": visit.status,
                },
            }
        )
    except Exception as e:
        return handle_error(e)


@app.route("/api/active-visits", methods=["GET"])
def api_active_visits():
    """Trả danh sách các lượt khám đang hoạt động (chưa thanh toán/xuất viện)."""
    try:
        active = []
        for visit in global_state.global_visits.values():
            if visit.status not in (config.STATUS_DISCHARGED, config.STATUS_COMPLETED):
                patient = global_state.global_patients.get(visit.patientID)
                active.append(
                    {
                        "visitID": visit.visitID,
                        "patientID": visit.patientID,
                        "patientName": patient.fullName if patient else "--",
                        "status": visit.status,
                    }
                )
        return jsonify({"success": True, "data": active})
    except Exception as e:
        return handle_error(e)


@app.route("/api/pay", methods=["POST"])
def api_pay():
    """Xử lý thanh toán cho lượt khám — giữ nguyên bản ghi trong DB."""
    try:
        body = request.get_json(force=True) or {}
        insurance_discount = float(body.get("insurance_discount", 80))
        ok, msg, bill = pharmacy_svc.process_payment(
            body.get("visit_id", ""), insurance_discount
        )
        return jsonify(
            {
                "success": ok,
                "message": msg,
                "bill": bill.to_dict() if bill else None,
            }
        )
    except Exception as e:
        return handle_error(e)


# =============================================================================
# Persistence — Lưu / Tải / Mock dữ liệu
# =============================================================================
@app.route("/api/save", methods=["POST"])
def api_save():
    """Lưu toàn bộ dữ liệu hệ thống ra file JSON."""
    try:
        ok, msg = persistence.saveData()
        return jsonify({"success": ok, "message": msg})
    except Exception as e:
        return handle_error(e)


@app.route("/api/load", methods=["POST"])
def api_load():
    """Tải toàn bộ dữ liệu hệ thống từ file JSON."""
    try:
        ok, msg = persistence.loadData()
        return jsonify({"success": ok, "message": msg})
    except Exception as e:
        return handle_error(e)


@app.route("/api/mock", methods=["POST"])
def api_mock():
    """Tạo dữ liệu mẫu cho hệ thống."""
    try:
        init_mock_data_small()
        return jsonify({"success": True, "message": "Đã tạo dữ liệu mẫu"})
    except Exception as e:
        return handle_error(e)


# =============================================================================
# Visit detail — Chi tiết lượt khám
# =============================================================================
@app.route("/api/visits/<id>", methods=["GET"])
def api_visit_detail(id):
    """Trả thông tin chi tiết của một lượt khám kèm thông tin bệnh nhân."""
    try:
        visit = global_state.global_visits.get(id)
        if not visit:
            return jsonify({"success": False, "error": "Không tìm thấy lượt khám"}), 404

        result = visit.to_dict()
        patient = global_state.global_patients.get(visit.patientID)
        if patient:
            result["patientName"] = patient.fullName
            result["hasInsurance"] = patient.hasInsurance
        else:
            result["patientName"] = None
            result["hasInsurance"] = None

        return jsonify({"success": True, "data": result})
    except Exception as e:
        return handle_error(e)


# =============================================================================
# Main page — Trang chính
# =============================================================================
@app.route("/", methods=["GET"])
def index():
    """Render trang index HTML."""
    return render_template("index.html")


import os

# =============================================================================
# Khởi tạo dữ liệu mẫu khi module được import (không phụ thuộc __main__)
# =============================================================================
reset_globals()
init_mock_data_small()

# =============================================================================
# Khởi chạy server
# =============================================================================
if __name__ == "__main__":
    # Render và các nền tảng cloud cung cấp PORT qua biến môi trường
    port = int(os.environ.get("PORT", 5000))
    # Tắt debug khi deploy production (RENDER env tồn tại)
    debug_mode = os.environ.get("RENDER") is None
    app.run(debug=debug_mode, host="0.0.0.0", port=port)
