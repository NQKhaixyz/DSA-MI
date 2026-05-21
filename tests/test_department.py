import pytest
from triage_system import Department, Patient
from hospital_triage import (
    Department as HTDepartment,
    Patient as HTPatient,
    Doctor as HTDoctor,
)


class TestDepartmentCreation:
    def test_department_creation_basic(self):
        dept = Department("DEPT01", "Emergency")
        assert dept.department_id == "DEPT01"
        assert dept.name == "Emergency"
        assert len(dept.emergency_queue) == 0
        assert len(dept.walk_in_queue) == 0
        assert len(dept.priority_queue) == 0

    def test_department_creation_defaults(self):
        dept = Department("DEPT02", "Cardiology")
        assert len(dept.doctor_ids) == 0

    def test_department_repr(self):
        dept = Department("DEPT01", "Emergency")
        repr_str = repr(dept)
        assert "DEPT01" in repr_str
        assert "Emergency" in repr_str


class TestEmergencyQueue:
    def test_add_to_emergency_queue(self, setup_triage_system):
        ts = setup_triage_system
        patient = Patient("P001", "Emergency Patient", danger_level=1)
        ts.add_to_emergency_queue("DEPT01", patient)
        assert len(ts.departments["DEPT01"].emergency_queue) == 1

    def test_emergency_queue_priority(self, setup_triage_system):
        ts = setup_triage_system
        patient = Patient("P001", "Emergency", danger_level=3)
        ts.add_to_emergency_queue("DEPT01", patient)
        assert patient.priority == 1

    def test_emergency_queue_patient_tracking(self, setup_triage_system):
        ts = setup_triage_system
        patient = Patient("P001", "Emergency", danger_level=3)
        ts.add_to_emergency_queue("DEPT01", patient)
        assert "P001" in ts.patients

    def test_multiple_emergency_patients(self, setup_triage_system):
        ts = setup_triage_system
        for i in range(3):
            patient = Patient(f"P00{i + 1}", f"Emergency {i + 1}", danger_level=1)
            ts.add_to_emergency_queue("DEPT01", patient)
        assert len(ts.departments["DEPT01"].emergency_queue) == 3

    def test_add_to_invalid_department(self):
        ts = type("TriageSystem", (), {"departments": {}})()
        patient = Patient("P001", "Test", danger_level=1)
        from triage_system import TriageSystem

        ts = TriageSystem()
        result = ts.add_to_emergency_queue("INVALID", patient)
        assert result is False


class TestWalkInQueue:
    def test_add_to_walk_in_queue(self, setup_triage_system):
        ts = setup_triage_system
        patient = Patient("P001", "Walk-in Patient", danger_level=3)
        ts.add_to_walk_in_queue("DEPT01", patient)
        assert len(ts.departments["DEPT01"].walk_in_queue) == 1

    def test_walk_in_queue_order(self, setup_triage_system):
        ts = setup_triage_system
        patients = [
            Patient(f"P00{i}", f"Walk-in {i}", danger_level=3) for i in range(3)
        ]
        for p in patients:
            ts.add_to_walk_in_queue("DEPT01", p)
        assert ts.departments["DEPT01"].walk_in_queue[0].patient_id == "P000"

    def test_walk_in_sets_wait_time(self, setup_triage_system):
        ts = setup_triage_system
        patient = Patient("P001", "Walk-in", danger_level=3)
        ts.add_to_walk_in_queue("DEPT01", patient)
        assert patient.wait_start_time is not None

    def test_add_multiple_walk_ins(self, setup_triage_system):
        ts = setup_triage_system
        for i in range(5):
            patient = Patient(f"P00{i}", f"Walk-in {i}", danger_level=3)
            ts.add_to_walk_in_queue("DEPT01", patient)
        assert len(ts.departments["DEPT01"].walk_in_queue) == 5


class TestQueueSortingByPriority:
    def test_ht_department_queue_sorting(self):
        dept = HTDepartment(name="Emergency")
        p1 = HTPatient(id="P001", name="Low", priority=4)
        p2 = HTPatient(id="P002", name="Normal", priority=3)
        p3 = HTPatient(id="P003", name="Urgent", priority=2)
        p4 = HTPatient(id="P004", name="Emergency", priority=1)

        dept.add_to_queue(p1)
        dept.add_to_queue(p2)
        dept.add_to_queue(p3)
        dept.add_to_queue(p4)

        priorities = [p.priority for p in dept.queue]
        assert priorities == [1, 2, 3, 4]

    def test_ht_department_get_next_patient(self):
        dept = HTDepartment(name="Emergency")
        p1 = HTPatient(id="P001", name="Low", priority=4)
        p2 = HTPatient(id="P002", name="Emergency", priority=1)
        dept.add_to_queue(p1)
        dept.add_to_queue(p2)

        next_p = dept.get_next_patient()
        assert next_p.priority == 1
        assert next_p.name == "Emergency"

    def test_ht_department_queue_length(self):
        dept = HTDepartment(name="Test")
        assert dept.get_queue_length() == 0
        dept.add_to_queue(HTPatient(id="P001", name="Test", priority=3))
        assert dept.get_queue_length() == 1

    def test_ht_department_available_doctors(self):
        dept = HTDepartment(name="Test")
        doctor = HTDoctor(id="D001", name="Dr. Smith", department="Test")
        dept.add_doctor(doctor)
        available = dept.get_available_doctors()
        assert len(available) == 1

        patient = HTPatient(id="P001", name="Patient", priority=3)
        doctor.start_examination(patient)
        available = dept.get_available_doctors()
        assert len(available) == 0

    def test_ht_department_queue_with_same_priority(self):
        dept = HTDepartment(name="Test")
        p1 = HTPatient(id="P001", name="First", priority=3)
        p2 = HTPatient(id="P002", name="Second", priority=3)
        p3 = HTPatient(id="P003", name="Third", priority=2)

        dept.add_to_queue(p1)
        dept.add_to_queue(p2)
        dept.add_to_queue(p3)

        priorities = [p.priority for p in dept.queue]
        assert priorities == [2, 3, 3]
        assert dept.queue[1].id == "P001"
        assert dept.queue[2].id == "P002"

    def test_ht_department_add_doctor(self):
        dept = HTDepartment(name="Test")
        doctor = HTDoctor(id="D001", name="Dr. Smith", department="Test")
        dept.add_doctor(doctor)
        assert len(dept.doctors) == 1
        assert dept.doctors[0].id == "D001"
