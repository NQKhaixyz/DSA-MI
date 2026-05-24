"""
Module CLI (Command Line Interface) cho hệ thống quản lý bệnh viện.
Cung cấp menu tương tác trên console với 3 phân hệ chính.
"""

import os
import sys
import unittest

# --- Import các dict toàn cục ---
try:
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
    from . import config
    from .models import Patient, Visit, Doctor, Department, Room, Service, Medicine
    from .algorithms import generate_id
    from .services import ReceptionService, DoctorService, PharmacyService
    from .persistence import saveData, loadData
    from .performance_test import run_all_benchmarks
except ImportError:
    from global_state import (
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
    import config
    from models import Patient, Visit, Doctor, Department, Room, Service, Medicine
    from algorithms import generate_id
    from services import ReceptionService, DoctorService, PharmacyService
    from persistence import saveData, loadData
    from performance_test import run_all_benchmarks


class HospitalCLI:
    """
    Lớp giao diện dòng lệnh (CLI) cho hệ thống quản lý bệnh viện.
    """

    def __init__(self):
        """Khởi tạo các dịch vụ nghiệp vụ."""
        self.reception = ReceptionService()
        self.doctor_svc = DoctorService()
        self.pharmacy = PharmacyService()

    # =====================================================================
    # Tiện ích
    # =====================================================================

    def _clear_screen(self):
        """Làm mới màn hình console (Windows: cls, Unix: clear)."""
        os.system("cls" if os.name == "nt" else "clear")

    def _pause(self):
        """Dừng chờ người dùng nhấn Enter."""
        input("\nNhấn Enter để tiếp tục...")

    def _print_header(self, title: str):
        """In tiêu đề có viền."""
        print("=" * 50)
        print(title.center(50))
        print("=" * 50)

    def _choose_from_list(self, items: list, title: str) -> int:
        """
        Hiển thị danh sách có đánh số và yêu cầu người dùng chọn.
        Trả về chỉ số (0-based) hoặc -1 nếu hủy.
        """
        print(f"\n{title}")
        for idx, item in enumerate(items, start=1):
            print(f"  [{idx}] {item}")
        print("  [0] Hủy")
        try:
            choice = int(input("Chọn số: ").strip())
            if choice == 0:
                return -1
            if 1 <= choice <= len(items):
                return choice - 1
            print("Lựa chọn không hợp lệ.")
            return -1
        except ValueError:
            print("Vui lòng nhập số.")
            return -1

    # =====================================================================
    # Vòng lặp chính
    # =====================================================================

    def run(self):
        """Vòng lặp chính hiển thị menu tổng."""
        while True:
            self._clear_screen()
            self._print_header("HỆ THỐNG QUẢN LÝ BỆNH VIỆN - DSA")
            print("[1] PHÂN HỆ LỄ TÂN (Tiếp đón & Đặt lịch)")
            print("[2] PHÂN HỆ BÁC SĨ (Tại phòng khám)")
            print("[3] PHÂN HỆ THU NGÂN & KHO DƯỢC")
            print("[4] LƯU DỮ LIỆU RA FILE (JSON)")
            print("[5] TẢI DỮ LIỆU TỪ FILE (JSON)")
            print("[6] CHẠY PERFORMANCE TEST")
            print("[7] CHẠY UNIT TESTS")
            print("[0] THOÁT")
            print("=" * 50)

            choice = input("Chọn chức năng: ").strip()

            if choice == "1":
                self.menu_le_tan()
            elif choice == "2":
                self.menu_bac_si()
            elif choice == "3":
                self.menu_thu_ngan()
            elif choice == "4":
                self._run_save_data()
            elif choice == "5":
                self._run_load_data()
            elif choice == "6":
                self._run_performance_test()
            elif choice == "7":
                self._run_unit_tests()
            elif choice == "0":
                print("Cảm ơn đã sử dụng hệ thống. Tạm biệt!")
                sys.exit(0)
            else:
                print("Lựa chọn không hợp lệ.")
                self._pause()

    # =====================================================================
    # Menu con: Phân hệ Lễ tân
    # =====================================================================

    def menu_le_tan(self):
        """Menu phân hệ Lễ tân: tiếp đón, đặt lịch, cấp cứu, danh sách chờ."""
        while True:
            self._clear_screen()
            self._print_header("PHÂN HỆ LỄ TÂN")
            print("[1.1] Đăng ký đặt lịch Online")
            print("[1.2] Tiếp đón bệnh nhân trực tiếp (Vãng lai)")
            print("[1.3] Kích hoạt trạng thái Cấp cứu khẩn cấp")
            print("[1.4] Hiển thị danh sách chờ của phòng khám")
            print("[1.0] Quay lại")
            print("=" * 50)

            choice = input("Chọn chức năng: ").strip()

            if choice == "1.1":
                self._register_online()
            elif choice == "1.2":
                self._checkin_walkin()
            elif choice == "1.3":
                self._activate_emergency()
            elif choice == "1.4":
                self._display_waiting_list()
            elif choice == "1.0":
                break
            else:
                print("Lựa chọn không hợp lệ.")
                self._pause()

    def _register_online(self):
        """
        [1.1] Đăng ký đặt lịch Online.
        Nhận patientID, chọn khoa, chọn bác sĩ, ngày khám, khung giờ.
        """
        try:
            patient_id = input("Nhập mã bệnh nhân (patientID): ").strip()
            if not patient_id:
                print("Mã bệnh nhân không được để trống.")
                self._pause()
                return

            # --- Chọn khoa ---
            depts = config.DEPARTMENTS
            idx = self._choose_from_list(depts, "DANH SÁCH KHOA")
            if idx == -1:
                print("Đã hủy.")
                self._pause()
                return
            chosen_dept = depts[idx]
            department_sequence = [chosen_dept]

            # --- Chọn bác sĩ thuộc khoa ---
            dept_obj = global_departments.get(chosen_dept)
            if not dept_obj or not dept_obj.doctorIDs:
                print(f"Khoa '{chosen_dept}' chưa có bác sĩ.")
                self._pause()
                return

            doctor_items = []
            for doc_id in dept_obj.doctorIDs:
                doc = global_doctors.get(doc_id)
                if doc:
                    doctor_items.append(f"{doc.doctorID} - {doc.fullName}")
                else:
                    doctor_items.append(doc_id)

            doc_idx = self._choose_from_list(doctor_items, "DANH SÁCH BÁC SĨ")
            if doc_idx == -1:
                print("Đã hủy.")
                self._pause()
                return
            selected_doctor_id = dept_obj.doctorIDs[doc_idx]

            # --- Ngày khám & khung giờ ---
            appointment_date = input("Nhập ngày khám (dd/mm/yyyy): ").strip()
            time_slot = input("Nhập khung giờ (ví dụ 08:00-09:00): ").strip()

            ok, msg = self.reception.register_online(
                patient_id,
                department_sequence,
                selected_doctor_id,
                appointment_date,
                time_slot,
            )
            print(f"\nKết quả: {'Thành công' if ok else 'Thất bại'} - {msg}")

        except Exception as e:
            print(f"Lỗi: {e}")
        self._pause()

    def _checkin_walkin(self):
        """
        [1.2] Tiếp đón bệnh nhân trực tiếp (Vãng lai).
        Nhập thông tin bệnh nhân (hoặc ID nếu đã có), chọn khoa, mức độ Bình thường.
        """
        try:
            patient_id = input("Nhập mã bệnh nhân (patientID): ").strip()
            if not patient_id:
                print("Mã bệnh nhân không được để trống.")
                self._pause()
                return

            # Nếu bệnh nhân chưa tồn tại, yêu cầu nhập thêm thông tin
            is_new = patient_id not in global_patients
            full_name = gender = dob = citizen_id = phone = address = blood_type = None
            if is_new:
                print("Bệnh nhân chưa có trong hệ thống. Vui lòng nhập thông tin:")
                full_name = input("Họ tên: ").strip() or None
                gender = input("Giới tính (Nam/Nữ): ").strip() or None
                dob = input("Ngày sinh (dd/mm/yyyy): ").strip() or None
                citizen_id = input("CCCD/CMND: ").strip() or None
                phone = input("Số điện thoại: ").strip() or None
                address = input("Địa chỉ: ").strip() or None
                blood_type = input("Nhóm máu (ví dụ O+): ").strip() or None

            # --- Chọn khoa ---
            depts = config.DEPARTMENTS
            idx = self._choose_from_list(depts, "DANH SÁCH KHOA")
            if idx == -1:
                print("Đã hủy.")
                self._pause()
                return
            department_sequence = [depts[idx]]

            visit, msg = self.reception.checkin_patient(
                patient_id,
                full_name=full_name,
                gender=gender,
                dob=dob,
                citizen_id=citizen_id,
                phone=phone,
                address=address,
                blood_type=blood_type,
                severity="BinhThuong",
                department_sequence=department_sequence,
                is_appointment=False,
            )
            if visit:
                print(f"\nCheck-in thành công!")
                print(f"  Visit ID : {visit.visitID}")
                print(f"  Priority : {visit.queuePriority}")
                print(f"  Room ID  : {visit.assignedRoomID}")
            else:
                print(f"\nCheck-in thất bại: {msg}")

        except Exception as e:
            print(f"Lỗi: {e}")
        self._pause()

    def _activate_emergency(self):
        """
        [1.3] Kích hoạt trạng thái Cấp cứu khẩn cấp.
        Nhập visitID và gọi activate_emergency.
        """
        try:
            visit_id = input("Nhập mã lượt khám (visitID): ").strip()
            ok, msg = self.reception.activate_emergency(visit_id)
            print(f"\nKết quả: {'Thành công' if ok else 'Thất bại'} - {msg}")
        except Exception as e:
            print(f"Lỗi: {e}")
        self._pause()

    def _display_waiting_list(self):
        """
        [1.4] Hiển thị danh sách chờ của phòng khám.
        Nhập roomID và hiển thị room.queues.display().
        """
        try:
            room_id = input("Nhập mã phòng (roomID): ").strip()
            result = self.reception.display_waiting_list(room_id)
            print(f"\n{result}")
        except Exception as e:
            print(f"Lỗi: {e}")
        self._pause()

    # =====================================================================
    # Menu con: Phân hệ Bác sĩ
    # =====================================================================

    def menu_bac_si(self):
        """Menu phân hệ Bác sĩ: xem hàng đợi, gọi bệnh nhân, chỉ định, hoàn tất."""
        while True:
            self._clear_screen()
            self._print_header("PHÂN HỆ BÁC SĨ")
            print("[2.1] Bảng điện tử: Xem danh sách chờ của Phòng khám")
            print("[2.2] Gọi bệnh nhân tiếp theo (Chạy Strict Priority)")
            print("[2.3] Chỉ định dịch vụ / Kê đơn thuốc")
            print("[2.4] Hoàn tất khám / Chuyển khoa chuyên môn")
            print("[2.0] Quay lại")
            print("=" * 50)

            choice = input("Chọn chức năng: ").strip()

            if choice == "2.1":
                self._view_room_queues()
            elif choice == "2.2":
                self._call_next_patient()
            elif choice == "2.3":
                self._add_service_or_prescription()
            elif choice == "2.4":
                self._complete_or_transfer()
            elif choice == "2.0":
                break
            else:
                print("Lựa chọn không hợp lệ.")
                self._pause()

    def _view_room_queues(self):
        """
        [2.1] Xem danh sách chờ đầy đủ 3 Queue của phòng.
        Nhập roomID và hiển thị queues.display().
        """
        try:
            room_id = input("Nhập mã phòng (roomID): ").strip()
            room = global_rooms.get(room_id)
            if not room:
                print("Không tìm thấy phòng.")
            else:
                print(f"\n--- Danh sách chờ phòng {room_id} ---")
                print(room.queues.display())
        except Exception as e:
            print(f"Lỗi: {e}")
        self._pause()

    def _call_next_patient(self):
        """
        [2.2] Gọi bệnh nhân tiếp theo theo Strict Priority.
        Nhập roomID, gọi call_next_patient và hiển thị thông tin.
        """
        try:
            room_id = input("Nhập mã phòng (roomID): ").strip()
            visit, msg = self.doctor_svc.call_next_patient(room_id)
            if visit:
                print(f"\n{msg}")
                print(f"  Visit ID   : {visit.visitID}")
                print(f"  Patient ID : {visit.patientID}")
                patient = global_patients.get(visit.patientID)
                if patient:
                    print(f"  Họ tên     : {patient.fullName}")
                print(f"  Priority   : {visit.queuePriority}")
                print(f"  Trạng thái : {visit.status}")
            else:
                print(f"\n{msg}")
        except Exception as e:
            print(f"Lỗi: {e}")
        self._pause()

    def _add_service_or_prescription(self):
        """
        [2.3] Chỉ định dịch vụ / Kê đơn thuốc.
        Hỏi người dùng muốn thêm dịch vụ (S) hay kê đơn (P).
        """
        try:
            action = (
                input("Thêm Dịch vụ (S) hay Kê đơn thuốc (P)? [S/P]: ").strip().upper()
            )

            if action == "S":
                visit_id = input("Nhập mã lượt khám (visitID): ").strip()
                svc_input = input(
                    "Nhập mã dịch vụ (có thể nhiều, cách nhau dấu phẩy): "
                ).strip()
                if not svc_input:
                    print("Không có dịch vụ nào được nhập.")
                    self._pause()
                    return

                service_ids = [s.strip() for s in svc_input.split(",") if s.strip()]
                for svc_id in service_ids:
                    ok, msg = self.doctor_svc.add_service(visit_id, svc_id)
                    print(f"  [{svc_id}] {'OK' if ok else 'LỖI'} - {msg}")

            elif action == "P":
                visit_id = input("Nhập mã lượt khám (visitID): ").strip()
                med_input = input("Nhập đơn thuốc (medID:qty,medID:qty...): ").strip()
                if not med_input:
                    print("Không có thuốc nào được nhập.")
                    self._pause()
                    return

                # Lấy doctorID tự động từ visit nếu có
                visit = global_visits.get(visit_id)
                doctor_id = None
                if visit and visit.assignedDoctorIDs:
                    doctor_id = visit.assignedDoctorIDs[-1]
                if not doctor_id:
                    doctor_id = input("Nhập mã bác sĩ (doctorID): ").strip()

                medicine_list = {}
                for pair in med_input.split(","):
                    if ":" in pair:
                        med_id, qty_str = pair.split(":", 1)
                        medicine_list[med_id.strip()] = int(qty_str.strip())

                ok, msg = self.doctor_svc.add_prescription(
                    visit_id, doctor_id, medicine_list
                )
                print(f"\nKết quả kê đơn: {'Thành công' if ok else 'Thất bại'} - {msg}")

            else:
                print("Lựa chọn không hợp lệ.")

        except Exception as e:
            print(f"Lỗi: {e}")
        self._pause()

    def _complete_or_transfer(self):
        """
        [2.4] Hoàn tất khám hoặc Chuyển khoa chuyên môn.
        Nhập visitID, hỏi Hoàn tất (H) hay Chuyển khoa (C).
        """
        try:
            visit_id = input("Nhập mã lượt khám (visitID): ").strip()
            sub = input("Hoàn tất (H) hay Chuyển khoa (C)? [H/C]: ").strip().upper()

            if sub == "H":
                ok, msg = self.doctor_svc.complete_examination(visit_id)
                print(f"\nKết quả: {'Thành công' if ok else 'Thất bại'} - {msg}")
            elif sub == "C":
                new_dept_id = input("Nhập mã khoa mới (new_dept_id): ").strip()
                ok, msg = self.doctor_svc.transfer_department(visit_id, new_dept_id)
                print(f"\nKết quả: {'Thành công' if ok else 'Thất bại'} - {msg}")
            else:
                print("Lựa chọn không hợp lệ.")

        except Exception as e:
            print(f"Lỗi: {e}")
        self._pause()

    # =====================================================================
    # Menu con: Phân hệ Thu ngân & Kho dược
    # =====================================================================

    def menu_thu_ngan(self):
        """Menu phân hệ Thu ngân: tìm visit chưa thanh toán, xử lý thanh toán."""
        while True:
            self._clear_screen()
            self._print_header("PHÂN HỆ THU NGÂN & KHO DƯỢC")
            print("[3.1] Nhập mã bệnh nhân để thanh toán")
            print("[3.2] Trích xuất hóa đơn viện phí & Trừ kho thuốc")
            print("[3.0] Quay lại")
            print("=" * 50)

            choice = input("Chọn chức năng: ").strip()

            if choice == "3.1":
                self._find_visit_by_patient()
            elif choice == "3.2":
                self._process_payment()
            elif choice == "3.0":
                break
            else:
                print("Lựa chọn không hợp lệ.")
                self._pause()

    def _find_visit_by_patient(self):
        """
        [3.1] Nhập mã bệnh nhân để tìm lượt khám chưa thanh toán.
        Hiển thị usedServiceIDs và thông tin đơn thuốc (nếu có).
        """
        try:
            patient_id = input("Nhập mã bệnh nhân (patientID): ").strip()
            visit = self.pharmacy.get_visit_by_patient(patient_id)
            if not visit:
                print(
                    f"\nKhông tìm thấy lượt khám chưa thanh toán của bệnh nhân {patient_id}."
                )
                self._pause()
                return

            print(f"\n--- Lượt khám tìm thấy ---")
            print(f"  Visit ID       : {visit.visitID}")
            print(f"  Patient ID     : {visit.patientID}")
            print(
                f"  Dịch vụ đã dùng: {visit.usedServiceIDs if visit.usedServiceIDs else 'Không có'}"
            )

            if visit.prescriptionID:
                pres = global_prescriptions.get(visit.prescriptionID)
                if pres:
                    print(f"  Đơn thuốc ID   : {pres.prescriptionID}")
                    print(f"  Thuốc          : {pres.medicineList}")
                else:
                    print(
                        f"  Đơn thuốc ID   : {visit.prescriptionID} (không tìm thấy chi tiết)"
                    )
            else:
                print("  Đơn thuốc      : Không có")

        except Exception as e:
            print(f"Lỗi: {e}")
        self._pause()

    def _process_payment(self):
        """
        [3.2] Trích xuất hóa đơn viện phí & Trừ kho thuốc.
        Nhập visitID, gọi process_payment, hiển thị hóa đơn.
        """
        try:
            visit_id = input("Nhập mã lượt khám (visitID): ").strip()
            ok, msg, bill = self.pharmacy.process_payment(visit_id)
            if ok and bill:
                print(f"\n{msg}")
                print(bill.generateInvoice())
            else:
                print(f"\nThanh toán thất bại: {msg}")
        except Exception as e:
            print(f"Lỗi: {e}")
        self._pause()

    # =====================================================================
    # Các chức năng chính khác
    # =====================================================================

    def _run_save_data(self):
        """[4] Lưu toàn bộ dữ liệu hệ thống ra file JSON."""
        try:
            filepath = input("Nhập tên file (mặc định hospital_data.json): ").strip()
            if not filepath:
                filepath = "hospital_data.json"
            ok, msg = saveData(filepath)
            print(f"\n{'Thành công' if ok else 'Thất bại'}: {msg}")
        except Exception as e:
            print(f"Lỗi: {e}")
        self._pause()

    def _run_load_data(self):
        """[5] Tải toàn bộ dữ liệu hệ thống từ file JSON."""
        try:
            filepath = input("Nhập tên file (mặc định hospital_data.json): ").strip()
            if not filepath:
                filepath = "hospital_data.json"
            ok, msg = loadData(filepath)
            print(f"\n{'Thành công' if ok else 'Thất bại'}: {msg}")
        except Exception as e:
            print(f"Lỗi: {e}")
        self._pause()

    def _run_performance_test(self):
        """[6] Chạy bộ benchmark hiệu năng hệ thống."""
        print("\nĐang chạy Performance Test (có thể mất vài phút)...")
        try:
            run_all_benchmarks()
        except Exception as e:
            print(f"Lỗi khi chạy benchmark: {e}")
        self._pause()

    def _run_unit_tests(self):
        """[7] Chạy toàn bộ unit tests của hệ thống."""
        print("\nĐang chạy Unit Tests...")
        try:
            # Load test suite từ module tests
            loader = unittest.TestLoader()
            # Thử import theo cách tương đối/tuyệt đối
            try:
                suite = loader.loadTestsFromName("benh_vien_dsa.tests")
            except Exception:
                suite = loader.loadTestsFromName("tests")
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            print(
                f"\nKết quả: {result.testsRun} test, "
                f"lỗi={len(result.errors)}, fail={len(result.failures)}"
            )
        except Exception as e:
            print(f"Lỗi khi chạy unit test: {e}")
        self._pause()
