import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from triage_system import TriageSystem, Patient, Doctor, Department


class TestAddDepartmentDoctorPatient:
    def test_add_department(self):
        ts = TriageSystem()
        ts.departments["DEPT01"] = Department("DEPT01", "Emergency")
        assert "DEPT01" in ts.departments
        assert ts.departments["DEPT01"].name == "Emergency"

    def test_add_doctor(self):
        ts = TriageSystem()
        ts.departments["DEPT01"] = Department("DEPT01", "Emergency")
        ts.doctors["D001"] = Doctor("D001", "Dr. Smith", "DEPT01")
        ts.departments["DEPT01"].doctor_ids.add("D001")
        assert "D001" in ts.doctors
        assert ts.doctors["D001"].name == "Dr. Smith"

    def test_add_patient(self):
        ts = TriageSystem()
        ts.patients["P001"] = Patient("P001", "John Doe", danger_level=3)
        assert "P001" in ts.patients
        assert ts.patients["P001"].name == "John Doe"

    def test_add_multiple_departments(self):
        ts = TriageSystem()
        for i in range(3):
            ts.departments[f"DEPT0{i + 1}"] = Department(
                f"DEPT0{i + 1}", f"Dept {i + 1}"
            )
        assert len(ts.departments) == 3


class TestBookAppointment:
    def test_book_appointment_success(self, setup_triage_system):
        result = setup_triage_system.book_appointment(
            {"patient_id": "P001", "name": "John"}, "2024-01-15", "09:00-10:00", "D001"
        )
        assert result["status"] == "success"

    def test_book_appointment_slot_limit(self, setup_triage_system):
        ts = setup_triage_system
        for i in range(4):
            ts.book_appointment(
                {"patient_id": f"P00{i + 1}", "name": f"Patient {i + 1}"},
                "2024-01-15",
                "09:00-10:00",
                "D001",
            )
        result = ts.book_appointment(
            {"patient_id": "P005", "name": "Patient 5"},
            "2024-01-15",
            "09:00-10:00",
            "D001",
        )
        assert result["status"] == "failure"
        assert "max 4" in result["message"]

    def test_book_appointment_different_dates(self, setup_triage_system):
        ts = setup_triage_system
        result1 = ts.book_appointment(
            {"patient_id": "P001", "name": "John"}, "2024-01-15", "09:00-10:00", "D001"
        )
        result2 = ts.book_appointment(
            {"patient_id": "P002", "name": "Jane"}, "2024-01-16", "09:00-10:00", "D001"
        )
        assert result1["status"] == "success"
        assert result2["status"] == "success"


class TestCheckInPatient:
    def test_check_in_emergency(self, setup_triage_system):
        ts = setup_triage_system
        result = ts.check_in_patient("P001", "DEPT01", danger_level=1)
        assert result["status"] == "checked_in"
        assert result["priority"] == 1
        assert result["queue"] == "emergency"

    def test_check_in_booked_on_time(self, setup_triage_system):
        ts = setup_triage_system
        ts.patients["P001"] = Patient("P001", "John", is_booked=True, danger_level=2)
        ts.patients["P001"].doctor_id = "D001"
        ts.patients["P001"].appointment_time = datetime(2024, 1, 15, 9, 0)

        result = ts.check_in_patient(
            "P001",
            "DEPT01",
            danger_level=2,
            doctor_id="D001",
            current_time=datetime(2024, 1, 15, 9, 10),
        )
        assert result["status"] == "checked_in"
        assert result["priority"] == 2

    def test_check_in_walk_in(self, setup_triage_system):
        ts = setup_triage_system
        result = ts.check_in_patient("P001", "DEPT01", danger_level=3)
        assert result["status"] == "checked_in"
        assert result["priority"] == 3
        assert result["queue"] == "walk_in"
        assert result["ticket"].startswith("W-")

    def test_check_in_late_patient(self, setup_triage_system):
        ts = setup_triage_system
        ts.patients["P001"] = Patient("P001", "John", is_booked=True, danger_level=2)
        ts.patients["P001"].doctor_id = "D001"
        ts.patients["P001"].appointment_time = datetime(2024, 1, 15, 9, 0)

        result = ts.check_in_patient(
            "P001",
            "DEPT01",
            danger_level=2,
            doctor_id="D001",
            current_time=datetime(2024, 1, 15, 9, 30),
        )
        assert result["priority"] == 3
        assert result["queue"] == "walk_in"
        assert ts.patients["P001"].danger_level == 3

    def test_check_in_auto_creates_patient(self, setup_triage_system):
        ts = setup_triage_system
        result = ts.check_in_patient("P999", "DEPT01", danger_level=3)
        assert result["status"] == "checked_in"
        assert "P999" in ts.patients

    def test_check_in_invalid_danger_level(self, setup_triage_system):
        ts = setup_triage_system
        result = ts.check_in_patient("P001", "DEPT01", danger_level=5)
        assert result["status"] == "error"

    def test_check_in_booked_no_doctor(self, setup_triage_system):
        ts = setup_triage_system
        result = ts.check_in_patient("P001", "DEPT01", danger_level=2)
        assert result["status"] == "error"
        assert "doctor_id required" in result["message"]

    def test_check_in_missing_appointment(self, setup_triage_system):
        ts = setup_triage_system
        ts.patients["P001"] = Patient("P001", "John", is_booked=False, danger_level=2)
        result = ts.check_in_patient("P001", "DEPT01", danger_level=2, doctor_id="D001")
        assert result["priority"] == 3


class TestNextPatientForDoctor:
    def test_next_patient_emergency_first(self, setup_triage_system):
        ts = setup_triage_system
        patient = Patient("P001", "Emergency", danger_level=1)
        ts.add_to_emergency_queue("DEPT01", patient)

        next_p = ts.next_patient_for_doctor("D001")
        assert next_p is not None
        assert next_p.patient_id == "P001"
        assert next_p.priority == 1

    def test_next_patient_booked_within_window(self, setup_triage_system):
        ts = setup_triage_system
        patient = Patient("P001", "Booked", danger_level=2, is_booked=True)
        appt_time = datetime(2024, 1, 15, 10, 0)
        ts.add_to_booked_queue("D001", patient, appt_time)

        next_p = ts.next_patient_for_doctor(
            "D001", current_time=datetime(2024, 1, 15, 10, 10)
        )
        assert next_p is not None
        assert next_p.patient_id == "P001"

    def test_next_patient_walk_in(self, setup_triage_system):
        ts = setup_triage_system
        patient = Patient("P001", "Walk-in", danger_level=3)
        ts.add_to_walk_in_queue("DEPT01", patient)

        next_p = ts.next_patient_for_doctor("D001")
        assert next_p is not None
        assert next_p.patient_id == "P001"

    def test_next_patient_booked_early_arrival(self, setup_triage_system):
        ts = setup_triage_system
        patient = Patient("P001", "Booked", danger_level=2, is_booked=True)
        appt_time = datetime(2024, 1, 15, 10, 0)
        ts.add_to_booked_queue("D001", patient, appt_time)

        next_p = ts.next_patient_for_doctor(
            "D001", current_time=datetime(2024, 1, 15, 9, 50)
        )
        assert next_p is not None
        assert next_p.patient_id == "P001"

    def test_next_patient_no_patients(self, setup_triage_system):
        ts = setup_triage_system
        next_p = ts.next_patient_for_doctor("D001")
        assert next_p is None
        assert ts.doctors["D001"].is_idle is True

    def test_next_patient_sets_doctor_busy(self, setup_triage_system):
        ts = setup_triage_system
        patient = Patient("P001", "Emergency", danger_level=1)
        ts.add_to_emergency_queue("DEPT01", patient)

        ts.next_patient_for_doctor("D001")
        assert ts.doctors["D001"].is_idle is False
        assert ts.doctors["D001"].current_patient_id == "P001"


class TestCompleteExamination:
    def test_complete_examination_assigns_next(self, setup_triage_system):
        ts = setup_triage_system
        patient = Patient("P001", "Emergency", danger_level=1)
        ts.add_to_emergency_queue("DEPT01", patient)

        next_p = ts.complete_examination("D001")
        assert next_p is not None
        assert next_p.patient_id == "P001"

    def test_complete_examination_no_patients(self, setup_triage_system):
        ts = setup_triage_system
        next_p = ts.complete_examination("D001")
        assert next_p is None

    def test_complete_examination_invalid_doctor(self, setup_triage_system):
        ts = setup_triage_system
        next_p = ts.complete_examination("INVALID")
        assert next_p is None


class TestLatePatientDemotion:
    def test_late_patient_demotion(self, setup_triage_system):
        ts = setup_triage_system
        ts.patients["P001"] = Patient("P001", "John", is_booked=True, danger_level=2)
        ts.patients["P001"].doctor_id = "D001"
        ts.patients["P001"].appointment_time = datetime(2024, 1, 15, 9, 0)

        result = ts.check_in_patient(
            "P001",
            "DEPT01",
            danger_level=2,
            doctor_id="D001",
            current_time=datetime(2024, 1, 15, 9, 20),
        )
        assert result["priority"] == 3
        assert result["queue"] == "walk_in"

    def test_late_patient_exactly_15_min(self, setup_triage_system):
        ts = setup_triage_system
        ts.patients["P001"] = Patient("P001", "John", is_booked=True, danger_level=2)
        ts.patients["P001"].doctor_id = "D001"
        ts.patients["P001"].appointment_time = datetime(2024, 1, 15, 9, 0)

        result = ts.check_in_patient(
            "P001",
            "DEPT01",
            danger_level=2,
            doctor_id="D001",
            current_time=datetime(2024, 1, 15, 9, 15),
        )
        assert result["priority"] == 2

    def test_on_time_patient_not_demoted(self, setup_triage_system):
        ts = setup_triage_system
        ts.patients["P001"] = Patient("P001", "John", is_booked=True, danger_level=2)
        ts.patients["P001"].doctor_id = "D001"
        ts.patients["P001"].appointment_time = datetime(2024, 1, 15, 9, 0)

        result = ts.check_in_patient(
            "P001",
            "DEPT01",
            danger_level=2,
            doctor_id="D001",
            current_time=datetime(2024, 1, 15, 9, 14),
        )
        assert result["priority"] == 2


class TestPromoteWaitedPatients:
    def test_promote_waited_patients_120_min(
        self, setup_triage_system, mock_datetime_now
    ):
        ts = setup_triage_system
        patient = Patient("P001", "Long Wait", danger_level=3)
        ts.add_to_walk_in_queue("DEPT01", patient)
        patient.wait_start_time = mock_datetime_now - timedelta(minutes=130)

        promoted = ts.promote_waited_patients("DEPT01", max_wait_minutes=120)
        assert len(promoted) == 1
        assert promoted[0].patient_id == "P001"
        assert promoted[0].priority == 2

    def test_no_promote_under_120_min(self, setup_triage_system, mock_datetime_now):
        ts = setup_triage_system
        patient = Patient("P001", "Short Wait", danger_level=3)
        ts.add_to_walk_in_queue("DEPT01", patient)
        patient.wait_start_time = mock_datetime_now - timedelta(minutes=60)

        promoted = ts.promote_waited_patients("DEPT01", max_wait_minutes=120)
        assert len(promoted) == 0
        assert patient.priority == 3

    def test_promote_to_emergency_180_min(self, setup_triage_system, mock_datetime_now):
        ts = setup_triage_system
        patient = Patient("P001", "Very Long Wait", danger_level=3)
        ts.add_to_walk_in_queue("DEPT01", patient)
        patient.wait_start_time = mock_datetime_now - timedelta(minutes=130)
        ts.promote_waited_patients("DEPT01", max_wait_minutes=120)

        patient.wait_start_time = mock_datetime_now - timedelta(minutes=200)
        ts.departments["DEPT01"].priority_queue.append(patient)
        promoted = ts.promote_waited_patients("DEPT01", max_wait_minutes=120)
        assert any(p.patient_id == "P001" and p.priority == 1 for p in promoted)

    def test_promote_invalid_department(self, setup_triage_system):
        ts = setup_triage_system
        promoted = ts.promote_waited_patients("INVALID")
        assert promoted == []


class TestEmergencyPriority:
    def test_emergency_always_first(self, setup_triage_system):
        ts = setup_triage_system
        walk_in = Patient("P001", "Walk-in", danger_level=3)
        emergency = Patient("P002", "Emergency", danger_level=1)
        booked = Patient("P003", "Booked", danger_level=2, is_booked=True)

        ts.add_to_walk_in_queue("DEPT01", walk_in)
        ts.add_to_emergency_queue("DEPT01", emergency)
        ts.add_to_booked_queue("D001", booked, datetime(2024, 1, 15, 10, 0))

        next_p = ts.next_patient_for_doctor(
            "D001", current_time=datetime(2024, 1, 15, 10, 0)
        )
        assert next_p.patient_id == "P002"
        assert next_p.priority == 1

    def test_emergency_after_normal_booked(self, setup_triage_system):
        ts = setup_triage_system
        booked = Patient("P001", "Booked", danger_level=2, is_booked=True)
        emergency = Patient("P002", "Emergency", danger_level=1)

        ts.add_to_booked_queue("D001", booked, datetime(2024, 1, 15, 10, 0))
        ts.add_to_emergency_queue("DEPT01", emergency)

        next_p = ts.next_patient_for_doctor(
            "D001", current_time=datetime(2024, 1, 15, 10, 0)
        )
        assert next_p.patient_id == "P002"


class TestManyToManyRelationships:
    def test_doctor_patient_graph(self, setup_triage_system):
        ts = setup_triage_system
        patient = Patient("P001", "Test", danger_level=1)
        ts.add_to_emergency_queue("DEPT01", patient)
        ts.next_patient_for_doctor("D001")

        assert "D001" in ts.doctor_patient_graph
        assert "P001" in ts.doctor_patient_graph["D001"]

    def test_patient_doctor_graph(self, setup_triage_system):
        ts = setup_triage_system
        patient = Patient("P001", "Test", danger_level=1)
        ts.add_to_emergency_queue("DEPT01", patient)
        ts.next_patient_for_doctor("D001")

        assert "P001" in ts.patient_doctor_graph
        assert "D001" in ts.patient_doctor_graph["P001"]

    def test_multiple_doctors_one_patient(self, setup_triage_system):
        ts = setup_triage_system
        patient = Patient("P001", "Test", danger_level=1)
        ts.add_to_emergency_queue("DEPT01", patient)
        ts.next_patient_for_doctor("D001")

        patient2 = Patient("P002", "Test2", danger_level=1)
        ts.add_to_emergency_queue("DEPT02", patient2)
        ts.next_patient_for_doctor("D002")

        assert len(ts.doctor_patient_graph) == 2

    def test_patient_doctor_ids_set(self, setup_triage_system):
        ts = setup_triage_system
        patient = Patient("P001", "Test", danger_level=1)
        ts.add_to_emergency_queue("DEPT01", patient)
        ts.next_patient_for_doctor("D001")

        assert "D001" in patient.doctor_ids


class TestCancelAppointment:
    def test_cancel_appointment_success(self, setup_triage_system):
        ts = setup_triage_system
        ts.book_appointment(
            {"patient_id": "P001", "name": "John"}, "2024-01-15", "09:00-10:00", "D001"
        )
        result = ts.cancel_appointment("P001", "2024-01-15", "09:00-10:00", "D001")
        assert result["status"] == "success"
        assert "cancelled" in result["message"]

    def test_cancel_appointment_not_found(self, setup_triage_system):
        ts = setup_triage_system
        result = ts.cancel_appointment("P001", "2024-01-15", "09:00-10:00", "D001")
        assert result["status"] == "failure"
        assert "not found" in result["message"]

    def test_cancel_appointment_removes_slot(self, setup_triage_system):
        ts = setup_triage_system
        ts.book_appointment(
            {"patient_id": "P001", "name": "John"}, "2024-01-15", "09:00-10:00", "D001"
        )
        ts.cancel_appointment("P001", "2024-01-15", "09:00-10:00", "D001")
        slot_key = ("2024-01-15", "09:00-10:00", "D001")
        assert (
            slot_key not in ts.appointment_slots or ts.appointment_slots[slot_key] == 0
        )

    def test_cancel_appointment_unsets_booked(self, setup_triage_system):
        ts = setup_triage_system
        ts.book_appointment(
            {"patient_id": "P001", "name": "John"}, "2024-01-15", "09:00-10:00", "D001"
        )
        ts.cancel_appointment("P001", "2024-01-15", "09:00-10:00", "D001")
        assert ts.patients["P001"].is_booked is False


class TestSystemStatus:
    def test_get_queue_status(self, setup_triage_system):
        ts = setup_triage_system
        ts.check_in_patient("P001", "DEPT01", danger_level=1)
        status = ts.get_queue_status("DEPT01")
        assert status["status"] == "success"
        assert status["emergency"]["queue_length"] == 1

    def test_get_patient_ticket(self, setup_triage_system):
        ts = setup_triage_system
        ts.check_in_patient("P001", "DEPT01", danger_level=3)
        ticket = ts.get_patient_ticket("P001")
        assert ticket["status"] == "success"
        assert ticket["ticket_number"].startswith("W-")
        assert ticket["priority_level"] == 3

    def test_get_available_slots(self, setup_triage_system):
        ts = setup_triage_system
        result = ts.get_available_slots("2024-01-15", "D001")
        assert result["status"] == "success"
        assert isinstance(result["available_slots"], list)

    def test_get_doctor_appointments(self, setup_triage_system):
        ts = setup_triage_system
        ts.book_appointment(
            {"patient_id": "P001", "name": "John"}, "2024-01-15", "09:00-10:00", "D001"
        )
        result = ts.get_doctor_appointments("D001", "2024-01-15")
        assert result["status"] == "success"
        assert result["count"] == 1

    def test_get_all_departments_status(self, setup_triage_system):
        ts = setup_triage_system
        status = ts.get_all_departments_status()
        assert "departments" in status
        assert status["summary"]["total_departments"] == 2
        assert status["summary"]["total_doctors"] == 2

    def test_get_doctor_status(self, setup_triage_system):
        ts = setup_triage_system
        patient = Patient("P001", "Test", danger_level=1)
        ts.add_to_emergency_queue("DEPT01", patient)
        ts.next_patient_for_doctor("D001")

        status = ts.get_doctor_status("D001")
        assert status["doctor_id"] == "D001"
        assert status["is_idle"] is False
        assert status["current_patient"]["patient_id"] == "P001"
