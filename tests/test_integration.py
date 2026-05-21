import pytest
from pathlib import Path
from datetime import datetime, timedelta
from triage_system import TriageSystem, Patient, Doctor, Department
from billing_system import BillingSystem
from data_manager import save_to_json, load_from_json, export_to_csv


@pytest.fixture
def full_system():
    ts = TriageSystem()
    ts.departments["DEPT01"] = Department("DEPT01", "Emergency")
    ts.departments["DEPT02"] = Department("DEPT02", "Cardiology")
    ts.departments["DEPT03"] = Department("DEPT03", "Radiology")

    ts.doctors["D001"] = Doctor("D001", "Dr. Smith", "DEPT01")
    ts.doctors["D002"] = Doctor("D002", "Dr. Jones", "DEPT02")
    ts.doctors["D003"] = Doctor("D003", "Dr. Brown", "DEPT03")

    ts.departments["DEPT01"].doctor_ids.add("D001")
    ts.departments["DEPT02"].doctor_ids.add("D002")
    ts.departments["DEPT03"].doctor_ids.add("D003")

    return ts


@pytest.fixture
def billing_with_services():
    bs = BillingSystem()
    return bs


class TestEndToEndWorkflow:
    def test_book_appointment_check_in_examine_bill(
        self, full_system, billing_with_services
    ):
        # Book appointment
        result = full_system.book_appointment(
            {"patient_id": "P001", "name": "John", "age": 35},
            "2024-01-15",
            "09:00-10:00",
            "D001",
        )
        assert result["status"] == "success"

        # Check in
        patient = full_system.patients["P001"]
        patient.is_booked = True
        patient.doctor_id = "D001"
        patient.appointment_time = datetime(2024, 1, 15, 9, 0)

        checkin = full_system.check_in_patient(
            "P001",
            "DEPT01",
            danger_level=2,
            doctor_id="D001",
            current_time=datetime(2024, 1, 15, 9, 5),
        )
        assert checkin["status"] == "checked_in"

        # Examine
        next_p = full_system.complete_examination("D001")
        assert next_p is not None
        assert next_p.patient_id == "P001"

        # Bill
        bill = billing_with_services.create_bill(
            "P001", "D001", "DEPT01", ["consultation", "blood_test"]
        )
        assert bill.total_amount == 350000
        billing_with_services.mark_bill_paid(bill.bill_id)
        assert billing_with_services.get_total_revenue() == 350000

    def test_walk_in_patient_full_flow(self, full_system, billing_with_services):
        # Walk-in patient
        result = full_system.check_in_patient("P002", "DEPT01", danger_level=3)
        assert result["status"] == "checked_in"
        assert result["priority"] == 3

        # Assign to doctor
        next_p = full_system.complete_examination("D001")
        assert next_p is not None
        assert next_p.patient_id == "P002"

        # Generate bill
        bill = billing_with_services.create_bill(
            "P002", "D001", "DEPT01", ["emergency_care", "xray"]
        )
        assert bill.total_amount == 800000

    def test_emergency_patient_bypasses_all(self, full_system, billing_with_services):
        # Booked patient
        full_system.book_appointment(
            {"patient_id": "P001", "name": "Booked"},
            "2024-01-15",
            "09:00-10:00",
            "D001",
        )
        full_system.patients["P001"].is_booked = True
        full_system.patients["P001"].doctor_id = "D001"
        full_system.patients["P001"].appointment_time = datetime(2024, 1, 15, 9, 0)
        full_system.check_in_patient(
            "P001",
            "DEPT01",
            danger_level=2,
            doctor_id="D001",
            current_time=datetime(2024, 1, 15, 9, 0),
        )

        # Walk-in patient
        full_system.check_in_patient("P002", "DEPT01", danger_level=3)

        # Emergency patient arrives
        emergency = Patient("P003", "Emergency", danger_level=1)
        full_system.add_to_emergency_queue("DEPT01", emergency)

        # Should get emergency first
        next_p = full_system.complete_examination("D001")
        assert next_p.patient_id == "P003"
        assert next_p.priority == 1

    def test_cancelled_appointment_flow(self, full_system):
        # Book appointment
        full_system.book_appointment(
            {"patient_id": "P001", "name": "John"}, "2024-01-15", "09:00-10:00", "D001"
        )

        # Cancel
        result = full_system.cancel_appointment(
            "P001", "2024-01-15", "09:00-10:00", "D001"
        )
        assert result["status"] == "success"

        # Should be able to book again in same slot
        result2 = full_system.book_appointment(
            {"patient_id": "P002", "name": "Jane"}, "2024-01-15", "09:00-10:00", "D001"
        )
        assert result2["status"] == "success"


class TestMultipleDepartments:
    def test_simultaneous_operations(self, full_system):
        # Patients in different departments
        full_system.check_in_patient("P001", "DEPT01", danger_level=1)
        full_system.check_in_patient("P002", "DEPT02", danger_level=3)
        full_system.check_in_patient("P003", "DEPT03", danger_level=3)

        # Assign to doctors
        p1 = full_system.complete_examination("D001")
        p2 = full_system.complete_examination("D002")
        p3 = full_system.complete_examination("D003")

        assert p1 is not None
        assert p2 is not None
        assert p3 is not None

        # Verify correct department routing
        assert p1.patient_id == "P001"
        assert p2.patient_id == "P002"
        assert p3.patient_id == "P003"

    def test_cross_department_patient_movement(self, full_system):
        # Patient checked into emergency
        full_system.check_in_patient("P001", "DEPT01", danger_level=3)

        # Then referred to cardiology
        patient = full_system.patients["P001"]
        full_system.add_to_walk_in_queue("DEPT02", patient)

        assert len(full_system.departments["DEPT02"].walk_in_queue) == 1

    def test_department_isolation(self, full_system):
        # Emergency queue in DEPT01 should not affect DEPT02
        emergency = Patient("P001", "Emergency", danger_level=1)
        full_system.add_to_emergency_queue("DEPT01", emergency)

        # D002 in DEPT02 should not see DEPT01 emergency
        next_p = full_system.complete_examination("D002")
        assert next_p is None

    def test_system_wide_status(self, full_system):
        full_system.check_in_patient("P001", "DEPT01", danger_level=1)
        full_system.check_in_patient("P002", "DEPT02", danger_level=3)

        status = full_system.get_all_departments_status()
        assert status["summary"]["total_departments"] == 3
        assert status["summary"]["total_doctors"] == 3
        assert status["summary"]["total_patients"] == 2
        assert status["departments"]["DEPT01"]["queue_lengths"]["emergency_queue"] == 1
        assert status["departments"]["DEPT02"]["queue_lengths"]["walk_in_queue"] == 1


class TestConcurrentOperations:
    def test_multiple_bookings_same_slot(self, full_system):
        # Try to book 5 patients in same slot (max 4)
        results = []
        for i in range(5):
            result = full_system.book_appointment(
                {"patient_id": f"P00{i + 1}", "name": f"Patient {i + 1}"},
                "2024-01-15",
                "09:00-10:00",
                "D001",
            )
            results.append(result["status"])

        assert results.count("success") == 4
        assert results.count("failure") == 1

    def test_multiple_check_ins_same_department(self, full_system):
        # 10 patients check in to same department
        for i in range(10):
            full_system.check_in_patient(f"P00{i + 1}", "DEPT01", danger_level=3)

        assert len(full_system.departments["DEPT01"].walk_in_queue) == 10

    def test_patient_priority_in_mixed_queue(self, full_system):
        # Mix of priorities
        priorities = [3, 1, 3, 2, 1, 3, 2, 3, 1, 3]
        for i, p in enumerate(priorities):
            if p == 1:
                patient = Patient(f"P00{i + 1}", f"Patient {i + 1}", danger_level=1)
                full_system.add_to_emergency_queue("DEPT01", patient)
            else:
                full_system.check_in_patient(f"P00{i + 1}", "DEPT01", danger_level=p)

        # Emergency should always be seen first
        first = full_system.complete_examination("D001")
        assert first.priority == 1

    def test_doctor_capacity_limits(self, full_system):
        # Book 4 appointments with D001
        for i in range(4):
            full_system.book_appointment(
                {"patient_id": f"P00{i + 1}", "name": f"Patient {i + 1}"},
                "2024-01-15",
                "10:00-11:00",
                "D001",
            )

        # Try 5th
        result = full_system.book_appointment(
            {"patient_id": "P005", "name": "Patient 5"},
            "2024-01-15",
            "10:00-11:00",
            "D001",
        )
        assert result["status"] == "failure"

        # But can book same slot with D002
        result2 = full_system.book_appointment(
            {"patient_id": "P005", "name": "Patient 5"},
            "2024-01-15",
            "10:00-11:00",
            "D002",
        )
        assert result2["status"] == "success"


class TestDataPersistenceIntegration:
    def test_save_and_load_integration(self, full_system, tmp_path):
        # Setup data
        full_system.check_in_patient("P001", "DEPT01", danger_level=3)
        full_system.book_appointment(
            {"patient_id": "P002", "name": "Jane"}, "2024-01-15", "09:00-10:00", "D001"
        )

        filepath = tmp_path / "integration.json"
        save_to_json(full_system, filepath)

        new_system = TriageSystem()
        load_from_json(new_system, filepath)

        assert len(new_system.patients) == 2
        assert len(new_system.departments) == 3
        assert len(new_system.doctors) == 3
        assert len(new_system.scheduled_appointments) == 1

    def test_csv_export_integration(self, full_system, tmp_path):
        full_system.check_in_patient("P001", "DEPT01", danger_level=3)
        full_system.check_in_patient("P002", "DEPT02", danger_level=1)

        exported = export_to_csv(full_system, tmp_path / "export")
        assert len(exported) == 3

        # Verify files exist
        for f in exported:
            assert Path(f).exists()


class TestBillingIntegration:
    def test_full_billing_workflow(self, full_system, billing_with_services):
        # Multiple patients, multiple bills
        bill1 = billing_with_services.create_bill(
            "P001", "D001", "DEPT01", ["consultation", "blood_test", "xray"]
        )
        bill2 = billing_with_services.create_bill(
            "P002", "D002", "DEPT02", ["emergency_care", "surgery"]
        )
        bill3 = billing_with_services.create_bill(
            "P001", "D003", "DEPT03", ["ultrasound"]
        )

        # Mark some as paid
        billing_with_services.mark_bill_paid(bill1.bill_id)
        billing_with_services.mark_bill_paid(bill2.bill_id)

        # Verify totals
        assert billing_with_services.get_total_revenue() == 3150000
        assert billing_with_services.get_department_revenue("DEPT01") == 650000
        assert billing_with_services.get_department_revenue("DEPT02") == 2500000

        # Verify patient bills
        p1_bills = billing_with_services.get_patient_bills("P001")
        assert len(p1_bills) == 2

    def test_add_service_after_bill_creation(self, full_system, billing_with_services):
        bill = billing_with_services.create_bill("P001", "D001", "DEPT01")
        assert bill.total_amount == 0

        billing_with_services.add_service_to_bill(bill.bill_id, "consultation")
        billing_with_services.add_service_to_bill(bill.bill_id, "prescription")

        assert bill.total_amount == 250000
        billing_with_services.mark_bill_paid(bill.bill_id)
        assert billing_with_services.get_total_revenue() == 250000

    def test_billing_with_custom_service(self, full_system, billing_with_services):
        billing_with_services.add_service_to_catalog("mri_scan", 1000000)
        bill = billing_with_services.create_bill("P001", "D001", "DEPT01", ["mri_scan"])

        assert bill.total_amount == 1000000
        billing_with_services.mark_bill_paid(bill.bill_id)
        assert billing_with_services.get_total_revenue() == 1000000


class TestEdgeCases:
    def test_late_patient_demoted_then_seen(self, full_system):
        # Book and check in late
        full_system.patients["P001"] = Patient(
            "P001", "Late", is_booked=True, danger_level=2
        )
        full_system.patients["P001"].doctor_id = "D001"
        full_system.patients["P001"].appointment_time = datetime(2024, 1, 15, 9, 0)

        result = full_system.check_in_patient(
            "P001",
            "DEPT01",
            danger_level=2,
            doctor_id="D001",
            current_time=datetime(2024, 1, 15, 9, 20),
        )
        assert result["priority"] == 3

        # Should be in walk-in queue
        assert len(full_system.departments["DEPT01"].walk_in_queue) == 1

    def test_promote_then_examine(self, full_system, mock_datetime_now):
        # Patient waits long time
        patient = Patient("P001", "Waiter", danger_level=3)
        full_system.add_to_walk_in_queue("DEPT01", patient)
        patient.wait_start_time = mock_datetime_now - timedelta(minutes=130)

        # Promote
        promoted = full_system.promote_waited_patients("DEPT01", max_wait_minutes=120)
        assert len(promoted) == 1

        # Now in priority queue
        assert len(full_system.departments["DEPT01"].priority_queue) == 1

    def test_empty_system_operations(self):
        ts = TriageSystem()

        result = ts.complete_examination("D001")
        assert result is None

        result = ts.next_patient_for_doctor("D001")
        assert result is None

        result = ts.get_queue_status("DEPT01")
        assert result["status"] == "error"

    def test_many_patients_single_doctor(self, full_system):
        # 20 patients, 1 doctor
        for i in range(20):
            if i % 5 == 0:
                patient = Patient(f"P00{i}", f"Emergency {i}", danger_level=1)
                full_system.add_to_emergency_queue("DEPT01", patient)
            else:
                full_system.check_in_patient(f"P00{i}", "DEPT01", danger_level=3)

        # Should always get emergency first
        for i in range(4):
            next_p = full_system.complete_examination("D001")
            if next_p:
                if i == 0:
                    assert next_p.priority == 1

    def test_patient_doctor_many_to_many(self, full_system):
        # One patient seen by multiple doctors
        patient = Patient("P001", "Multi", danger_level=1)
        full_system.add_to_emergency_queue("DEPT01", patient)
        full_system.next_patient_for_doctor("D001")

        patient2 = Patient("P002", "Multi2", danger_level=1)
        full_system.add_to_emergency_queue("DEPT02", patient2)
        full_system.next_patient_for_doctor("D002")

        # Add P001 to D002 as well
        full_system.doctor_patient_graph["D002"] = {"P001"}
        full_system.patient_doctor_graph["P001"] = {"D001", "D002"}

        assert "P001" in full_system.doctor_patient_graph["D001"]
        assert "P001" in full_system.doctor_patient_graph["D002"]
        assert full_system.patient_doctor_graph["P001"] == {"D001", "D002"}
