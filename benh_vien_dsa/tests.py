"""
Module test tổng hợp cho hệ thống quản lý bệnh viện.
Chạy: python -m unittest benh_vien_dsa.tests
"""

import os
import unittest

from benh_vien_dsa import global_state
from benh_vien_dsa.global_state import reset_globals
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
    Appointment,
)
from benh_vien_dsa.data_structures import MultiLevelQueue
from benh_vien_dsa.algorithms import (
    cycle_detection,
    shortest_queue_first,
    two_pass_validation,
    calculate_bill,
    strict_priority_call_next,
    generate_id,
)
from benh_vien_dsa.services import ReceptionService, DoctorService, PharmacyService
from benh_vien_dsa.persistence import saveData, loadData
from benh_vien_dsa import config


class TestHospitalSystem(unittest.TestCase):
    """Test tổng hợp hệ thống quản lý bệnh viện."""

    def setUp(self):
        """Reset toàn bộ trạng thái toàn cục trước mỗi test."""
        reset_globals()

    # ---------------------------------------------------------
    # 1. Test hàng đợi đa mức ưu tiên (MultiLevelQueue)
    # ---------------------------------------------------------
    def test_priority_queue_operations(self):
        """Enqueue 3 visit (priority 1,2,3), verify dequeue order 3->2->1, và appendleft_emergency."""
        mlq = MultiLevelQueue()
        v1 = Visit("V1", "P1", "01/01/2024", "08:00")
        v2 = Visit("V2", "P2", "01/01/2024", "08:00")
        v3 = Visit("V3", "P3", "01/01/2024", "08:00")

        mlq.enqueue(v1, 1)
        mlq.enqueue(v2, 2)
        mlq.enqueue(v3, 3)

        self.assertEqual(mlq.dequeue(), v3)
        self.assertEqual(mlq.dequeue(), v2)
        self.assertEqual(mlq.dequeue(), v1)
        self.assertIsNone(mlq.dequeue())

        # appendleft_emergency đẩy lên đầu hàng đợi cấp cứu
        v4 = Visit("V4", "P4", "01/01/2024", "08:00")
        mlq.enqueue(v3, 3)
        mlq.appendleft_emergency(v4)
        self.assertEqual(mlq.dequeue(), v4)
        self.assertEqual(mlq.dequeue(), v3)

    # ---------------------------------------------------------
    # 2. Strict priority gọi số khi phòng rỗng
    # ---------------------------------------------------------
    def test_strict_priority_call_next_empty_room(self):
        """Gọi strict_priority_call_next trên phòng rỗng phải trả về None."""
        room = Room("R1", "DEPT1", "DOC1")
        result = strict_priority_call_next(room)
        self.assertIsNone(result)

    # ---------------------------------------------------------
    # 3. Shortest Queue First chọn phòng có hàng đợi ngắn nhất
    # ---------------------------------------------------------
    def test_sqf_assign_shortest_queue(self):
        """SQF phải xếp visit vào phòng có hàng đợi ngắn nhất."""
        dept = Department("DEPT1", "Khoa Test")

        room1 = Room("R1", "DEPT1", "DOC1")
        room2 = Room("R2", "DEPT1", "DOC2")

        global_state.global_rooms["R1"] = room1
        global_state.global_rooms["R2"] = room2
        dept.addRoom("R1")
        dept.addRoom("R2")

        # Room1 có 2 visit
        v_old1 = Visit("V_OLD1", "P1", "01/01/2024", "08:00")
        v_old2 = Visit("V_OLD2", "P2", "01/01/2024", "08:00")
        room1.addToQueue(v_old1, 1)
        room1.addToQueue(v_old2, 1)

        visit_new = Visit("V_NEW", "P3", "01/01/2024", "09:00")
        visit_new.queuePriority = 1

        chosen_room = shortest_queue_first(dept, visit_new)

        self.assertEqual(chosen_room.roomID, "R2")
        self.assertEqual(visit_new.assignedRoomID, "R2")

    # ---------------------------------------------------------
    # 4. Cycle detection chặn trùng khoa
    # ---------------------------------------------------------
    def test_cycle_detection_blocks_duplicate(self):
        """Thêm cùng một khoa 2 lần phải bị cycle_detection chặn."""
        visit = Visit("V1", "P1", "01/01/2024", "08:00")

        # Thêm khoa lần đầu thành công
        ok1, msg1 = visit.addDepartment("NoiTongQuat")
        self.assertTrue(ok1)

        # Thêm khoa đã khám (visited_departments chưa có vì chưa moveToNextDepartment)
        # Nhưng cycle_detection dựa trên visited_departments, ta giả lập đã khám
        visit.moveToNextDepartment()  # -> NoiTongQuat vào visited_departments

        ok2, msg2 = cycle_detection(visit, "NoiTongQuat")
        self.assertFalse(ok2)
        self.assertIn("đã khám", msg2)

    # ---------------------------------------------------------
    # 5. Cycle detection giới hạn tối đa 3 khoa/ngày
    # ---------------------------------------------------------
    def test_cycle_detection_max_3_departments(self):
        """Thêm khoa thứ 4 trong ngày phải bị từ chối."""
        visit = Visit("V1", "P1", "01/01/2024", "08:00")

        # Thêm 3 khoa khác nhau
        for dept in ["NoiTongQuat", "NgoaiKhoa", "NhiKhoa"]:
            ok, _ = visit.addDepartment(dept)
            self.assertTrue(ok)

        # Khi đã có 3 khoa trong departmentSequence, cycle_detection kiểm tra
        # visited_departments nhưng ta chưa move, nên ta giả lập visited_departments đủ 3
        visit.visited_departments = {"NoiTongQuat", "NgoaiKhoa", "NhiKhoa"}

        ok, msg = cycle_detection(visit, "DaLieu")
        self.assertFalse(ok)
        self.assertIn("vượt quá", msg)

    # ---------------------------------------------------------
    # 6. Two-Pass Validation thành công
    # ---------------------------------------------------------
    def test_two_pass_validation_success(self):
        """Thuốc đủ tồn kho, sau xuất kho stock giảm đúng."""
        med = Medicine("M1", "Paracetamol", 5000, 100)
        global_state.global_inventory["M1"] = med

        pres = Prescription("PRE1", "V1", "DOC1")
        pres.addMedicine("M1", 10)

        ok, msg = two_pass_validation(pres, global_state.global_inventory)
        self.assertTrue(ok)
        self.assertEqual(med.stockQuantity, 90)

    # ---------------------------------------------------------
    # 7. Two-Pass Validation thất bại, không trừ kho
    # ---------------------------------------------------------
    def test_two_pass_validation_failure(self):
        """Thuốc không đủ tồn kho, stock phải giữ nguyên."""
        med = Medicine("M1", "Paracetamol", 5000, 5)
        global_state.global_inventory["M1"] = med

        pres = Prescription("PRE1", "V1", "DOC1")
        pres.addMedicine("M1", 10)

        ok, msg = two_pass_validation(pres, global_state.global_inventory)
        self.assertFalse(ok)
        self.assertEqual(med.stockQuantity, 5)

    # ---------------------------------------------------------
    # 8. Emergency Preempt ưu tiên tuyệt đối
    # ---------------------------------------------------------
    def test_emergency_preempt(self):
        """emergencyPreempt phải đẩy visit lên đầu hàng đợi cấp cứu."""
        room = Room("R1", "DEPT1", "DOC1")
        v1 = Visit("V1", "P1", "01/01/2024", "08:00")
        v1.queuePriority = 1
        room.addToQueue(v1, 1)

        room.emergencyPreempt(v1)

        self.assertEqual(v1.queuePriority, config.PRIORITY_EMERGENCY)
        self.assertEqual(room.callNextPatient(), v1)

    # ---------------------------------------------------------
    # 9. Tính hóa đơn có bảo hiểm
    # ---------------------------------------------------------
    def test_bill_calculation_with_insurance(self):
        """Có BHYT: thanh toán 20% tổng chi phí."""
        patient = Patient(
            "P1",
            "Nguyen Van A",
            "Nam",
            "01/01/1990",
            "123456789",
            "0909123456",
            "a@email.com",
            "HN",
            "O+",
            hasInsurance=True,
        )
        global_state.global_patients["P1"] = patient

        visit = Visit("V1", "P1", "01/01/2024", "08:00")
        visit.usedServiceIDs = ["S1"]

        svc = Service("S1", "Kham", "DEPT1", 100000)
        global_state.global_services["S1"] = svc

        pres = Prescription("PRE1", "V1", "DOC1")
        pres.addMedicine("M1", 2)
        global_state.global_prescriptions["PRE1"] = pres
        visit.prescriptionID = "PRE1"

        med = Medicine("M1", "ThuocX", 50000, 100)
        global_state.global_inventory["M1"] = med

        bill = calculate_bill(
            visit, global_state.global_services, global_state.global_inventory
        )

        expected = (100000 + 100000) * 0.2
        self.assertEqual(bill.finalTotal, expected)

    # ---------------------------------------------------------
    # 10. Tính hóa đơn không có bảo hiểm
    # ---------------------------------------------------------
    def test_bill_calculation_without_insurance(self):
        """Không BHYT: thanh toán 100% tổng chi phí."""
        patient = Patient(
            "P1",
            "Nguyen Van A",
            "Nam",
            "01/01/1990",
            "123456789",
            "0909123456",
            "a@email.com",
            "HN",
            "O+",
            hasInsurance=False,
        )
        global_state.global_patients["P1"] = patient

        visit = Visit("V1", "P1", "01/01/2024", "08:00")
        visit.usedServiceIDs = ["S1"]

        svc = Service("S1", "Kham", "DEPT1", 100000)
        global_state.global_services["S1"] = svc

        pres = Prescription("PRE1", "V1", "DOC1")
        pres.addMedicine("M1", 2)
        global_state.global_prescriptions["PRE1"] = pres
        visit.prescriptionID = "PRE1"

        med = Medicine("M1", "ThuocX", 50000, 100)
        global_state.global_inventory["M1"] = med

        bill = calculate_bill(
            visit, global_state.global_services, global_state.global_inventory
        )

        expected = 100000 + 100000
        self.assertEqual(bill.finalTotal, expected)

    # ---------------------------------------------------------
    # 11. Giới hạn tối đa 4 bệnh nhân/slot
    # ---------------------------------------------------------
    def test_slot_limit_blocks_fifth_patient(self):
        """Đăng ký lịch hẹn slot thứ 5 phải bị từ chối."""
        reception = ReceptionService()
        doctor = Doctor(
            "DOC1",
            "Bac Si A",
            "Nam",
            "01/01/1980",
            "0909123456",
            "doc@email.com",
            "HN",
            "DEPT1",
            "BS",
            "LIC1",
            10,
        )
        global_state.global_doctors["DOC1"] = doctor

        for i in range(4):
            ok, _ = reception.register_online(
                f"P{i}", ["DEPT1"], "DOC1", "01/01/2024", "08:00-09:00"
            )
            self.assertTrue(ok)

        ok5, msg5 = reception.register_online(
            "P4", ["DEPT1"], "DOC1", "01/01/2024", "08:00-09:00"
        )
        self.assertFalse(ok5)
        self.assertIn("đã đầy", msg5)

    # ---------------------------------------------------------
    # 12. Reception check-in walk-in
    # ---------------------------------------------------------
    def test_reception_checkin_walkin(self):
        """Check-in trực tiếp phải có queuePriority = 1 (WALKIN)."""
        reception = ReceptionService()
        dept = Department("DEPT1", "Khoa Test")
        room = Room("R1", "DEPT1", "DOC1")
        global_state.global_departments["DEPT1"] = dept
        global_state.global_rooms["R1"] = room
        dept.addRoom("R1")

        visit, msg = reception.checkin_patient(
            "P1", full_name="Test", is_appointment=False, department_sequence=["DEPT1"]
        )
        self.assertIsNotNone(visit)
        self.assertEqual(visit.queuePriority, config.PRIORITY_WALKIN)

    # ---------------------------------------------------------
    # 13. Reception check-in appointment
    # ---------------------------------------------------------
    def test_reception_checkin_appointment(self):
        """Check-in có đặt hẹn trước phải có queuePriority = 2 (APPOINTMENT)."""
        reception = ReceptionService()
        dept = Department("DEPT1", "Khoa Test")
        room = Room("R1", "DEPT1", "DOC1")
        global_state.global_departments["DEPT1"] = dept
        global_state.global_rooms["R1"] = room
        dept.addRoom("R1")

        # Đăng ký lịch trước
        doctor = Doctor(
            "DOC1",
            "Bac Si A",
            "Nam",
            "01/01/1980",
            "0909123456",
            "doc@email.com",
            "HN",
            "DEPT1",
            "BS",
            "LIC1",
            10,
        )
        global_state.global_doctors["DOC1"] = doctor

        ok, _ = reception.register_online(
            "P1", ["DEPT1"], "DOC1", "01/01/2026", "08:00-09:00"
        )
        self.assertTrue(ok)

        # Check-in với is_appointment=True
        visit, msg = reception.checkin_patient(
            "P1", is_appointment=True, department_sequence=["DEPT1"]
        )
        self.assertIsNotNone(visit)
        self.assertEqual(visit.queuePriority, config.PRIORITY_APPOINTMENT)

    # ---------------------------------------------------------
    # 14. Hoàn tất khám tự động gọi bệnh nhân tiếp theo
    # ---------------------------------------------------------
    def test_doctor_complete_examination_calls_next(self):
        """complete_examination giải phóng phòng, call_next_patient lấy visit tiếp theo."""
        doctor_svc = DoctorService()
        room = Room("R1", "DEPT1", "DOC1")
        global_state.global_rooms["R1"] = room

        v1 = Visit("V1", "P1", "01/01/2024", "08:00")
        v2 = Visit("V2", "P2", "01/01/2024", "08:00")
        room.addToQueue(v1, 1)
        room.addToQueue(v2, 1)
        global_state.global_visits["V1"] = v1
        global_state.global_visits["V2"] = v2

        # Gọi bệnh nhân đầu tiên
        visit_called, _ = doctor_svc.call_next_patient("R1")
        self.assertEqual(visit_called, v1)
        self.assertEqual(room.currentVisitID, "V1")
        v1.assignedRoomID = "R1"  # Đảm bảo complete_examination biết phòng đang khám

        # Hoàn tất khám v1
        doctor_svc.complete_examination("V1")
        self.assertIsNone(room.currentVisitID)

        # Gọi bệnh nhân tiếp theo
        visit_next, _ = doctor_svc.call_next_patient("R1")
        self.assertEqual(visit_next, v2)

    # ---------------------------------------------------------
    # 15. Persistence save/load
    # ---------------------------------------------------------
    def test_persistence_save_and_load(self):
        """Lưu dữ liệu ra file, reset, load lại, verify đúng dữ liệu."""
        p1 = Patient("P1", "A", "Nam", "01/01/1990", "123", "0909", "a@b.c", "HN", "O+")
        p2 = Patient("P2", "B", "Nu", "01/01/1991", "456", "0910", "b@c.d", "HCM", "A+")
        global_state.global_patients["P1"] = p1
        global_state.global_patients["P2"] = p2

        doc = Doctor(
            "DOC1",
            "Dr.X",
            "Nam",
            "01/01/1980",
            "0909",
            "doc@b.c",
            "HN",
            "DEPT1",
            "BS",
            "LIC1",
            10,
        )
        global_state.global_doctors["DOC1"] = doc

        dept = Department("DEPT1", "Khoa Noi")
        global_state.global_departments["DEPT1"] = dept

        room = Room("R1", "DEPT1", "DOC1")
        global_state.global_rooms["R1"] = room

        ok, _ = saveData("test_data.json")
        self.assertTrue(ok)

        reset_globals()
        self.assertEqual(len(global_state.global_patients), 0)

        ok2, _ = loadData("test_data.json")
        self.assertTrue(ok2)

        self.assertEqual(len(global_state.global_patients), 2)
        self.assertIn("P1", global_state.global_patients)
        self.assertIn("P2", global_state.global_patients)
        self.assertEqual(global_state.global_patients["P1"].patientID, "P1")

        # Dọn dẹp file test
        if os.path.exists("test_data.json"):
            os.remove("test_data.json")

    # ---------------------------------------------------------
    # 16. Chuyển khoa hợp lệ
    # ---------------------------------------------------------
    def test_transfer_department_valid(self):
        """Chuyển khoa hợp lệ, visit phải cập nhật visited_departments có khoa mới."""
        doctor_svc = DoctorService()

        dept_a = Department("DEPT_A", "Khoa A")
        dept_b = Department("DEPT_B", "Khoa B")
        room_a = Room("RA", "DEPT_A", "DOC_A")
        room_b = Room("RB", "DEPT_B", "DOC_B")

        global_state.global_departments["DEPT_A"] = dept_a
        global_state.global_departments["DEPT_B"] = dept_b
        global_state.global_rooms["RA"] = room_a
        global_state.global_rooms["RB"] = room_b
        dept_a.addRoom("RA")
        dept_b.addRoom("RB")

        visit = Visit("V1", "P1", "01/01/2024", "08:00")
        visit.departmentSequence = ["DEPT_A"]
        visit.currentDepartmentIndex = 0
        visit.visited_departments = {"DEPT_A"}
        global_state.global_visits["V1"] = visit

        # Gán vào room A để có assignedRoomID
        room_a.addToQueue(visit, 1)
        visit.assignedRoomID = "RA"

        ok, msg = doctor_svc.transfer_department("V1", "DEPT_B")
        self.assertTrue(ok)
        self.assertIn("DEPT_B", visit.visited_departments)


if __name__ == "__main__":
    unittest.main()
