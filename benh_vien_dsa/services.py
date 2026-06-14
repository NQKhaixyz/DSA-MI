"""
Module nghiệp vụ (business logic) cho hệ thống quản lý bệnh viện.
Cung cấp các lớp Service xử lý quy trình tiếp đón, khám bệnh và thanh toán.
"""

from datetime import datetime
from typing import Optional, Tuple

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


class ReceptionService:
    """
    Dịch vụ tiếp đón: đăng ký khám online, check-in bệnh nhân,
    kích hoạt cấp cứu và hiển thị danh sách chờ.
    """

    def register_online(
        self,
        patient_id: str,
        department_sequence: list[str],
        selected_doctor_id: str,
        appointment_date: str,
        time_slot: str,
    ) -> Tuple[bool, str]:
        """
        Đăng ký lịch hẹn khám online cho bệnh nhân.

        - Tạo mã lịch hẹn duy nhất bằng generate_id("APT").
        - Kiểm tra slot theo khóa (selected_doctor_id, appointment_date, time_slot)
          trong global_appointments. Nếu danh sách tại slot đã đạt
          MAX_SLOT_PER_TIMESLOT thì từ chối.
        - Nếu còn slot, lưu đối tượng Appointment vào danh sách slot.

        Trả về:
            (True, "Đặt lịch thành công") nếu thành công.
            (False, message) nếu slot đã đầy hoặc có lỗi.
        """
        try:
            # Tạo mã lịch hẹn duy nhất
            apt_id = algorithms.generate_id("APT")

            # Khởi tạo đối tượng Appointment
            appointment = models.Appointment(
                appointmentID=apt_id,
                patientID=patient_id,
                departmentSequence=department_sequence,
                selectedDoctorID=selected_doctor_id,
                appointmentDate=appointment_date,
                timeSlot=time_slot,
            )

            # Khóa tra cứu slot: (bác sĩ, ngày, khung giờ)
            slot_key = (selected_doctor_id, appointment_date, time_slot)

            # Lấy hoặc khởi tạo danh sách lịch hẹn tại slot này
            slot_list = global_state.global_appointments.setdefault(slot_key, [])

            # Kiểm tra giới hạn số bệnh nhân tối đa trong một khung giờ
            if len(slot_list) >= config.MAX_SLOT_PER_TIMESLOT:
                return False, "Khung giờ đã đầy, vui lòng chọn khung giờ khác."

            # Thêm lịch hẹn vào danh sách slot
            slot_list.append(appointment)

            return True, "Đặt lịch thành công"

        except Exception as e:
            return False, f"Lỗi đặt lịch: {str(e)}"

    def checkin_patient(
        self,
        patient_id: str,
        full_name: Optional[str] = None,
        gender: Optional[str] = None,
        dob: Optional[str] = None,
        citizen_id: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        blood_type: Optional[str] = None,
        severity: str = "BinhThuong",
        department_sequence: Optional[list[str]] = None,
        is_appointment: bool = False,
        appointment_date: Optional[str] = None,
        time_slot: Optional[str] = None,
        selected_doctor_id: Optional[str] = None,
        has_insurance: bool = False,
    ) -> Tuple[Optional[models.Visit], str]:
        """
        Check-in bệnh nhân tại quầy tiếp đón.

        - Nếu bệnh nhân chưa có trong global_patients, tự động tạo mới
          với thông tin truyền vào (dùng placeholder nếu thiếu).
        - Tạo Visit mới với visitID = generate_id("VISIT").
        - Xác định queuePriority dựa trên severity / is_appointment.
        - Nếu có đặt lịch trước, lưu thông tin lịch hẹn vào visit.
        - Visit được tạo với status = ChoCheckIn (chưa xếp hàng đợi).
          Hàng đợi chỉ được xếp khi bấm nút Check-in tại danh sách.

        Trả về:
            (visit_obj, "Check-in thành công") nếu thành công.
            (None, message) nếu có lỗi.
        """
        try:
            # --- Tạo hoặc lấy thông tin bệnh nhân ---
            if patient_id not in global_state.global_patients:
                patient = models.Patient(
                    patientID=patient_id,
                    fullName=full_name or "Chưa cập nhật",
                    gender=gender or "Không rõ",
                    dob=dob or "01/01/1970",
                    citizenID=citizen_id or "000000000000",
                    phone=phone or "0000000000",
                    email="unknown@example.com",
                    address=address or "Không rõ",
                    bloodType=blood_type or "O+",
                    hasInsurance=has_insurance,
                )
                global_state.global_patients[patient_id] = patient

            # --- Tạo lượt khám mới ---
            now = datetime.now()
            today_str = now.strftime("%d/%m/%Y")
            now_str = now.strftime("%H:%M:%S")

            visit_id = algorithms.generate_id("VISIT")
            visit = models.Visit(
                visitID=visit_id,
                patientID=patient_id,
                visitDate=today_str,
                arrivalTime=now_str,
            )
            visit.severity = severity

            # --- Xác định mức ưu tiên ---
            if severity in ("3", "NguyKich", "Nguy Kịch", "nguykich"):
                visit.queuePriority = config.PRIORITY_EMERGENCY
                visit.status = config.STATUS_EMERGENCY
            elif is_appointment or severity in ("2", "UuTien", "Ưu tiên"):
                visit.queuePriority = config.PRIORITY_APPOINTMENT
                visit.status = config.STATUS_WAITING_CHECKIN
            else:
                visit.queuePriority = config.PRIORITY_WALKIN
                visit.status = config.STATUS_WAITING_CHECKIN

            # --- Nếu có đặt lịch trước, lưu thông tin lịch hẹn ---
            if is_appointment and selected_doctor_id and appointment_date and time_slot:
                apt_id = algorithms.generate_id("APT")
                appointment = models.Appointment(
                    appointmentID=apt_id,
                    patientID=patient_id,
                    departmentSequence=department_sequence or [],
                    selectedDoctorID=selected_doctor_id,
                    appointmentDate=appointment_date,
                    timeSlot=time_slot,
                )
                # Lưu lịch hẹn vào hệ thống (dùng slot_key giống register_online)
                slot_key = (selected_doctor_id, appointment_date, time_slot)
                slot_list = global_state.global_appointments.setdefault(slot_key, [])
                if len(slot_list) < config.MAX_SLOT_PER_TIMESLOT:
                    slot_list.append(appointment)
                # Gắn appointmentID vào visit để truy vết
                visit.appointmentID = apt_id

            # --- Thêm chuỗi khoa khám (chưa xếp queue) ---
            if department_sequence:
                for dept_id in department_sequence:
                    visit.addDepartment(dept_id)
                visit.currentDepartmentIndex = 0

            # --- Lưu lượt khám vào hệ thống ---
            global_state.global_visits[visit_id] = visit

            return visit, "Tạo bệnh nhân và lượt khám thành công"

        except KeyError as e:
            return None, f"Không tìm thấy dữ liệu: {str(e)}"
        except ValueError as e:
            return None, str(e)
        except Exception as e:
            return None, f"Lỗi check-in: {str(e)}"

    def confirm_checkin(self, visit_id: str) -> Tuple[Optional[models.Visit], str]:
        """
        Xác nhận check-in từ danh sách tiếp đón: chuyển visit sang status DangKham
        và xếp vào hàng đợi phòng khám của khoa hiện tại.

        Trả về:
            (visit_obj, message) nếu thành công.
            (None, message) nếu lỗi.
        """
        try:
            visit = global_state.global_visits[visit_id]

            if visit.status != config.STATUS_WAITING_CHECKIN:
                return (
                    None,
                    f"Lượt khám đã ở trạng thái {visit.status}, không thể check-in lại",
                )

            # Chuyển trạng thái
            if visit.queuePriority == config.PRIORITY_EMERGENCY:
                visit.status = config.STATUS_EMERGENCY
            else:
                visit.status = config.STATUS_ACTIVE

            # Xếp vào phòng của khoa hiện tại (nếu có)
            first_dept_id = visit.getCurrentDepartment()
            if first_dept_id:
                visit.visited_departments.add(first_dept_id)
                dept = global_state.global_departments[first_dept_id]
                algorithms.shortest_queue_first(dept, visit)

            return visit, "Check-in thành công, đã xếp vào hàng đợi"

        except KeyError:
            return None, f"Không tìm thấy lượt khám ID {visit_id}"
        except Exception as e:
            return None, f"Lỗi xác nhận check-in: {str(e)}"

    def activate_emergency(self, visit_id: str) -> Tuple[bool, str]:
        """
        Kích hoạt chế độ cấp cứu cho một lượt khám.

        - Kiểm tra nếu đã là cấp cứu thì từ chối.
        - Tìm phòng hiện tại (nếu có) và gọi emergencyPreempt(visit).
        - Cập nhật queuePriority = 3, status = STATUS_EMERGENCY.

        Trả về:
            (True, "Kích hoạt cấp cứu thành công") nếu thành công.
            (False, message) nếu đã là cấp cứu hoặc có lỗi.
        """
        try:
            visit = global_state.global_visits[visit_id]

            if (
                visit.status == config.STATUS_EMERGENCY
                and visit.queuePriority == config.PRIORITY_EMERGENCY
            ):
                return False, "Đã là cấp cứu"

            room_id = visit.assignedRoomID
            if room_id and room_id in global_state.global_rooms:
                room = global_state.global_rooms[room_id]
                try:
                    room.emergencyPreempt(visit)
                except ValueError:
                    # Visit có thể không còn trong hàng đợi (đang được khám)
                    pass

            visit.queuePriority = config.PRIORITY_EMERGENCY
            visit.status = config.STATUS_EMERGENCY

            return True, "Kích hoạt cấp cứu thành công"

        except KeyError:
            return False, f"Không tìm thấy lượt khám ID {visit_id}"
        except Exception as e:
            return False, f"Lỗi kích hoạt cấp cứu: {str(e)}"

    def display_waiting_list(self, room_id: str) -> str:
        """
        Hiển thị danh sách bệnh nhân đang chờ trong một phòng khám.

        Trả về chuỗi mô tả số lượng chờ theo từng mức ưu tiên,
        hoặc thông báo lỗi nếu phòng không tồn tại.
        """
        try:
            room = global_state.global_rooms[room_id]
            return room.queues.display()
        except KeyError:
            return f"Không tìm thấy phòng ID {room_id}"
        except Exception as e:
            return f"Lỗi hiển thị danh sách chờ: {str(e)}"


class DoctorService:
    """
    Dịch vụ bác sĩ: gọi bệnh nhân, thêm dịch vụ, kê đơn thuốc,
    chuyển khoa và hoàn tất khám.
    """

    def call_next_patient(self, room_id: str) -> Tuple[Optional[models.Visit], str]:
        """
        Gọi bệnh nhân tiếp theo theo thuật toán Strict Priority.

        - Kiểm tra phòng đang bận thì từ chối.
        - Gọi strict_priority_call_next(room) để lấy Visit từ hàng đợi.
        - Ghi nhận bác sĩ vào visit.assignedDoctorIDs.

        Trả về:
            (visit_obj, "Gọi bệnh nhân thành công") nếu có bệnh nhân.
            (None, message) nếu phòng bận hoặc hàng đợi rỗng.
        """
        try:
            room = global_state.global_rooms[room_id]

            if room.isBusy() and room.currentVisitID is not None:
                return None, "Phòng đang khám bệnh nhân khác"

            visit = algorithms.strict_priority_call_next(room)
            if visit is None:
                return None, "Không có bệnh nhân chờ"

            visit.assignedDoctorIDs.append(room.doctorID)

            return visit, "Gọi bệnh nhân thành công"

        except KeyError:
            return None, f"Không tìm thấy phòng ID {room_id}"
        except Exception as e:
            return None, f"Lỗi gọi bệnh nhân: {str(e)}"

    def add_service(self, visit_id: str, service_id: str) -> Tuple[bool, str]:
        """
        Thêm một dịch vụ y tế vào lượt khám.

        Kiểm tra service_id tồn tại trong global_services trước khi thêm.

        Trả về:
            (True, "Thêm dịch vụ thành công") nếu thành công.
            (False, message) nếu có lỗi.
        """
        try:
            visit = global_state.global_visits[visit_id]

            if service_id not in global_state.global_services:
                return False, f"Dịch vụ ID {service_id} không tồn tại"

            visit.addService(service_id)
            return True, "Thêm dịch vụ thành công"

        except KeyError:
            return False, f"Không tìm thấy lượt khám ID {visit_id}"
        except Exception as e:
            return False, f"Lỗi thêm dịch vụ: {str(e)}"

    def add_prescription(
        self,
        visit_id: str,
        doctor_id: str,
        medicine_list: dict[str, int],
        note: str = "",
    ) -> Tuple[bool, str]:
        """
        Kê đơn thuốc cho lượt khám.

        - Tạo Prescription mới với generate_id("PRE").
        - Lặp medicine_list để thêm từng loại thuốc.
        - Lưu prescription vào global_prescriptions,
          gán visit.prescriptionID.

        Trả về:
            (True, "Kê đơn thuốc thành công") nếu thành công.
            (False, message) nếu có lỗi.
        """
        try:
            visit = global_state.global_visits[visit_id]

            pres_id = algorithms.generate_id("PRE")
            prescription = models.Prescription(
                prescriptionID=pres_id,
                visitID=visit_id,
                doctorID=doctor_id,
            )
            prescription.note = note

            for med_id, qty in medicine_list.items():
                prescription.addMedicine(med_id, qty)

            global_state.global_prescriptions[pres_id] = prescription
            visit.prescriptionID = pres_id

            return True, "Kê đơn thuốc thành công"

        except KeyError:
            return False, f"Không tìm thấy lượt khám ID {visit_id}"
        except Exception as e:
            return False, f"Lỗi kê đơn thuốc: {str(e)}"

    def transfer_department(self, visit_id: str, new_dept_id: str) -> Tuple[bool, str]:
        """
        Chuyển bệnh nhân sang khoa mới.

        - Gọi cycle_detection(visit, new_dept_id) để kiểm tra chu trình
          và giới hạn 3 khoa/ngày.
        - Thêm khoa mới vào departmentSequence, cập nhật currentDepartmentIndex.
        - Xếp visit vào phòng có hàng đợi ngắn nhất của khoa mới.

        Trả về:
            (True, "Chuyển khoa thành công") nếu hợp lệ.
            (False, message) nếu vi phạm quy tắc.
        """
        try:
            visit = global_state.global_visits[visit_id]

            current_dept = visit.getCurrentDepartment()
            if new_dept_id == current_dept:
                return False, "Lỗi: Không thể chuyển sang cùng khoa đang khám!"

            ok, msg = algorithms.cycle_detection(visit, new_dept_id)
            if not ok:
                return False, msg

            visit.departmentSequence.append(new_dept_id)
            visit.currentDepartmentIndex = visit.departmentSequence.index(new_dept_id)

            dept = global_state.global_departments[new_dept_id]
            algorithms.shortest_queue_first(dept, visit)

            return True, "Chuyển khoa thành công"

        except KeyError as e:
            return False, f"Không tìm thấy dữ liệu: {str(e)}"
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Lỗi chuyển khoa: {str(e)}"

    def complete_examination(self, visit_id: str) -> Tuple[bool, str]:
        """
        Hoàn tất khám cho lượt khám hiện tại.

        - Giải phóng phòng hiện tại (currentVisitID = None).
        - Gọi visit.moveToNextDepartment(). Nếu còn khoa tiếp theo,
          tự động xếp vào phòng của khoa đó.
        - Nếu không còn khoa, xóa visit khỏi hàng đợi phòng hiện tại (nếu còn sót),
          xóa assignedRoomID, và cập nhật status = "ChoThanhToan".

        Trả về:
            (True, message) nếu thành công.
            (False, message) nếu có lỗi.
        """
        try:
            visit = global_state.global_visits[visit_id]

            # Giải phóng phòng hiện tại nếu có
            current_room_id = visit.assignedRoomID
            if current_room_id and current_room_id in global_state.global_rooms:
                room = global_state.global_rooms[current_room_id]
                room.currentVisitID = None

                # Xóa visit khỏi hàng đợi phòng nếu còn sót (phòng trường hợp chưa được gọi)
                try:
                    room.queues.remove(visit, visit.queuePriority)
                except (ValueError, KeyError):
                    # Visit không còn trong hàng đợi (đã bị pop trước đó)
                    pass

            # Kiểm tra và chuyển sang khoa tiếp theo
            next_dept_id = visit.moveToNextDepartment()
            if next_dept_id is not None:
                dept = global_state.global_departments[next_dept_id]
                algorithms.shortest_queue_first(dept, visit)
                return True, "Hoàn tất khám khoa hiện tại, chuyển sang khoa tiếp theo"

            # Hết chuỗi khoa -> xóa assignedRoomID và chờ thanh toán
            visit.assignedRoomID = None
            visit.status = "ChoThanhToan"
            return True, "Hoàn tất khám, chờ thanh toán"

        except KeyError as e:
            return False, f"Không tìm thấy dữ liệu: {str(e)}"
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Lỗi hoàn tất khám: {str(e)}"


class PharmacyService:
    """
    Dịch vụ nhà thuốc / thanh toán: tìm lượt khám theo bệnh nhân,
    xử lý thanh toán, xuất viện và dọn dẹp hàng đợi.
    """

    def get_visit_by_patient(self, patient_id: str) -> Optional[models.Visit]:
        """
        Tìm lượt khám đang diễn ra (chưa xuất viện) của một bệnh nhân.

        Lặp qua global_visits.values(), tìm visit có patientID khớp
        và status != STATUS_DISCHARGED.

        Trả về Visit hoặc None.
        """
        for visit in global_state.global_visits.values():
            if (
                visit.patientID == patient_id
                and visit.status != config.STATUS_DISCHARGED
            ):
                return visit
        return None

    def process_payment(
        self, visit_id: str, insurance_discount_percent: float = 80.0
    ) -> Tuple[bool, str, Optional[models.Bill]]:
        """
        Xử lý thanh toán cho lượt khám.

        - Nếu có đơn thuốc: chạy two_pass_validation để kiểm tra và trừ kho.
        - Tính hóa đơn bằng calculate_bill.
        - Đánh dấu đã thanh toán, cập nhật status = STATUS_COMPLETED (giữ nguyên DB).
        - Dọn dẹp: xóa visit khỏi mọi room queue (nếu còn sót)
          và giải phóng currentVisitID của phòng.

        Trả về:
            (True, "Thanh toán thành công", bill_obj) nếu thành công.
            (False, message, None) nếu có lỗi (ví dụ kho thuốc không đủ).
        """
        try:
            visit = global_state.global_visits[visit_id]

            # --- Xác thực đơn thuốc (Two-Pass Validation) ---
            if visit.prescriptionID:
                prescription = global_state.global_prescriptions[visit.prescriptionID]
                ok, msg = algorithms.two_pass_validation(
                    prescription, global_state.global_inventory
                )
                if not ok:
                    return False, msg, None

            # --- Tính toán hóa đơn ---
            bill = algorithms.calculate_bill(
                visit,
                global_state.global_services,
                global_state.global_inventory,
                insurance_discount_percent,
            )

            # --- Thanh toán ---
            bill.markPaid()

            # --- Hoàn tất: giữ nguyên trong DB, chỉ đổi trạng thái ---
            visit.status = config.STATUS_COMPLETED

            # --- Dọn dẹp phòng và hàng đợi ---
            for room in global_state.global_rooms.values():
                if room.currentVisitID == visit_id:
                    room.currentVisitID = None

                try:
                    room.queues.remove(visit, visit.queuePriority)
                except ValueError:
                    # Visit không còn trong hàng đợi này (đã bị pop trước đó)
                    pass

            return True, "Thanh toán thành công", bill

        except KeyError as e:
            return False, f"Không tìm thấy dữ liệu: {str(e)}", None
        except Exception as e:
            return False, f"Lỗi thanh toán: {str(e)}", None
