import pytest
from collections import deque
from datetime import datetime, timedelta
from triage_system import Doctor
from hospital_triage import Doctor as HTDoctor, Patient as HTPatient


class TestDoctorCreation:
    def test_doctor_creation_basic(self):
        doctor = Doctor("D001", "Dr. Smith", "DEPT01")
        assert doctor.doctor_id == "D001"
        assert doctor.name == "Dr. Smith"
        assert doctor.department_id == "DEPT01"
        assert doctor.is_idle is True
        assert doctor.current_patient_id is None

    def test_doctor_creation_defaults(self):
        doctor = Doctor("D001", "Dr. Smith", "DEPT01")
        assert isinstance(doctor.booked_queue, deque)
        assert len(doctor.booked_queue) == 0

    def test_doctor_repr(self):
        doctor = Doctor("D001", "Dr. Smith", "DEPT01")
        repr_str = repr(doctor)
        assert "D001" in repr_str
        assert "Dr. Smith" in repr_str


class TestBookedQueueOperations:
    def test_empty_booked_queue(self, sample_doctor):
        assert len(sample_doctor.booked_queue) == 0

    def test_add_to_booked_queue(self, sample_doctor):
        from triage_system import Patient

        patient = Patient("P001", "Test Patient")
        sample_doctor.booked_queue.append(patient)
        assert len(sample_doctor.booked_queue) == 1

    def test_add_multiple_to_booked_queue(self, sample_doctor):
        from triage_system import Patient

        for i in range(5):
            patient = Patient(f"P00{i}", f"Patient {i}")
            sample_doctor.booked_queue.append(patient)
        assert len(sample_doctor.booked_queue) == 5

    def test_pop_from_booked_queue(self, sample_doctor):
        from triage_system import Patient

        patient1 = Patient("P001", "Patient 1")
        patient2 = Patient("P002", "Patient 2")
        sample_doctor.booked_queue.append(patient1)
        sample_doctor.booked_queue.append(patient2)
        popped = sample_doctor.booked_queue.popleft()
        assert popped.patient_id == "P001"
        assert len(sample_doctor.booked_queue) == 1

    def test_booked_queue_order(self, sample_doctor):
        from triage_system import Patient

        patients = [Patient(f"P00{i}", f"Patient {i}") for i in range(3)]
        for p in patients:
            sample_doctor.booked_queue.append(p)
        assert sample_doctor.booked_queue[0].patient_id == "P000"
        assert sample_doctor.booked_queue[2].patient_id == "P002"


class TestMaxSlotLimit:
    def test_max_slot_limit_four(self, setup_triage_system):
        ts = setup_triage_system
        patient_data = {"patient_id": "P001", "name": "Patient 1", "age": 30}
        for i in range(4):
            data = patient_data.copy()
            data["patient_id"] = f"P00{i + 1}"
            result = ts.book_appointment(data, "2024-01-15", "09:00-10:00", "D001")
            assert result["status"] == "success"

    def test_max_slot_limit_exceeded(self, setup_triage_system):
        ts = setup_triage_system
        patient_data = {"patient_id": "P001", "name": "Patient 1", "age": 30}
        for i in range(4):
            data = patient_data.copy()
            data["patient_id"] = f"P00{i + 1}"
            ts.book_appointment(data, "2024-01-15", "10:00-11:00", "D001")

        result = ts.book_appointment(
            {"patient_id": "P005", "name": "Patient 5"},
            "2024-01-15",
            "10:00-11:00",
            "D001",
        )
        assert result["status"] == "failure"
        assert "Slot is full" in result["message"]

    def test_different_doctors_same_slot(self, setup_triage_system):
        ts = setup_triage_system
        result1 = ts.book_appointment(
            {"patient_id": "P001", "name": "Patient 1"},
            "2024-01-15",
            "09:00-10:00",
            "D001",
        )
        result2 = ts.book_appointment(
            {"patient_id": "P002", "name": "Patient 2"},
            "2024-01-15",
            "09:00-10:00",
            "D002",
        )
        assert result1["status"] == "success"
        assert result2["status"] == "success"

    def test_different_time_slots_same_doctor(self, setup_triage_system):
        ts = setup_triage_system
        result1 = ts.book_appointment(
            {"patient_id": "P001", "name": "Patient 1"},
            "2024-01-15",
            "09:00-10:00",
            "D001",
        )
        result2 = ts.book_appointment(
            {"patient_id": "P002", "name": "Patient 2"},
            "2024-01-15",
            "10:00-11:00",
            "D001",
        )
        assert result1["status"] == "success"
        assert result2["status"] == "success"


class TestAppointmentBooking:
    def test_book_appointment_creates_patient(self, setup_triage_system):
        ts = setup_triage_system
        result = ts.book_appointment(
            {"patient_id": "P001", "name": "John", "age": 30},
            "2024-01-15",
            "09:00-10:00",
            "D001",
        )
        assert result["status"] == "success"
        assert "P001" in ts.patients
        assert ts.patients["P001"].is_booked is True

    def test_book_appointment_ticket_generation(self, setup_triage_system):
        ts = setup_triage_system
        result = ts.book_appointment(
            {"patient_id": "P001", "name": "John"}, "2024-01-15", "09:00-10:00", "D001"
        )
        assert "ticket_number" in result
        assert result["ticket_number"].startswith("B-")

    def test_book_appointment_sets_patient_ticket(self, setup_triage_system):
        ts = setup_triage_system
        ts.book_appointment(
            {"patient_id": "P001", "name": "John"}, "2024-01-15", "09:00-10:00", "D001"
        )
        assert ts.patients["P001"].ticket_number.startswith("B-")

    def test_book_appointment_with_existing_patient(self, setup_triage_system):
        ts = setup_triage_system
        ts.patients["P001"] = type(
            "Patient",
            (),
            {
                "patient_id": "P001",
                "name": "John",
                "is_booked": False,
                "ticket_number": "",
            },
        )()
        result = ts.book_appointment(
            {"patient_id": "P001", "name": "John"}, "2024-01-15", "09:00-10:00", "D001"
        )
        assert result["status"] == "success"


class TestHTDoctor:
    def test_ht_doctor_creation(self):
        doctor = HTDoctor(id="D001", name="Dr. Smith", department="Emergency")
        assert doctor.id == "D001"
        assert doctor.name == "Dr. Smith"
        assert doctor.department == "Emergency"
        assert doctor.max_slots_per_hour == 4

    def test_ht_doctor_availability(self):
        doctor = HTDoctor(id="D001", name="Dr. Smith", department="Emergency")
        time_slot = datetime(2024, 1, 15, 9, 0)
        assert doctor.is_available(time_slot) is True

    def test_ht_doctor_appointments(self):
        doctor = HTDoctor(id="D001", name="Dr. Smith", department="Emergency")
        patient = HTPatient(id="P001", name="John", priority=3)
        time_slot = datetime(2024, 1, 15, 9, 0)
        result = doctor.book_appointment(patient, time_slot)
        assert result is True
        assert len(doctor.appointments) == 1

    def test_ht_doctor_slot_limit(self):
        doctor = HTDoctor(id="D001", name="Dr. Smith", department="Emergency")
        time_slot = datetime(2024, 1, 15, 10, 0)
        for i in range(4):
            patient = HTPatient(id=f"P00{i}", name=f"Patient {i}", priority=3)
            doctor.book_appointment(patient, time_slot)

        fifth_patient = HTPatient(id="P004", name="Patient 4", priority=3)
        result = doctor.book_appointment(fifth_patient, time_slot)
        assert result is False
