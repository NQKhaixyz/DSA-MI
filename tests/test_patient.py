import pytest
from datetime import datetime
from triage_system import Patient
from hospital_triage import Patient as HTPatient


class TestPatientCreation:
    def test_patient_creation_basic(self):
        patient = Patient("P001", "John Doe")
        assert patient.patient_id == "P001"
        assert patient.name == "John Doe"
        assert patient.age == 0
        assert patient.symptoms == ""
        assert patient.danger_level == 2
        assert patient.is_booked is False

    def test_patient_creation_full(self):
        patient = Patient(
            "P002",
            "Jane Smith",
            age=25,
            symptoms="Fever",
            danger_level=1,
            is_booked=True,
        )
        assert patient.patient_id == "P002"
        assert patient.name == "Jane Smith"
        assert patient.age == 25
        assert patient.symptoms == "Fever"
        assert patient.danger_level == 1
        assert patient.is_booked is True

    def test_patient_default_values(self):
        patient = Patient("P003", "Test Patient")
        assert patient.ticket_number == ""
        assert patient.appointment_time is None
        assert patient.doctor_id is None
        assert patient.doctor_ids == set()
        assert patient.priority == 2

    def test_patient_repr(self):
        patient = Patient("P001", "John Doe")
        patient.ticket_number = "W-001"
        repr_str = repr(patient)
        assert "P001" in repr_str
        assert "John Doe" in repr_str
        assert "W-001" in repr_str


class TestPatientPriorityLevels:
    def test_priority_emergency(self):
        patient = Patient("P001", "Emergency", danger_level=1)
        assert patient.priority == 1
        assert patient.danger_level == 1

    def test_priority_urgent(self):
        patient = Patient("P001", "Urgent", danger_level=2)
        assert patient.priority == 2
        assert patient.danger_level == 2

    def test_priority_normal(self):
        patient = Patient("P001", "Normal", danger_level=3)
        assert patient.priority == 3
        assert patient.danger_level == 3

    def test_priority_low(self):
        patient = Patient("P001", "Low", danger_level=4)
        assert patient.priority == 4
        assert patient.danger_level == 4

    def test_priority_change(self):
        patient = Patient("P001", "Test", danger_level=3)
        patient.priority = 1
        assert patient.priority == 1
        assert patient.danger_level == 3

    @pytest.mark.parametrize("level", [1, 2, 3, 4, 5])
    def test_priority_levels_parametrized(self, level):
        patient = Patient("P001", "Test", danger_level=level)
        assert patient.priority == level


class TestTicketNumberGeneration:
    def test_default_ticket_empty(self):
        patient = Patient("P001", "Test")
        assert patient.ticket_number == ""

    def test_ticket_assignment(self):
        patient = Patient("P001", "Test")
        patient.ticket_number = "W-001"
        assert patient.ticket_number == "W-001"

    def test_ticket_walk_in_format(self):
        patient = Patient("P001", "Test")
        patient.ticket_number = "W-005"
        assert patient.ticket_number.startswith("W-")

    def test_ticket_booked_format(self):
        patient = Patient("P001", "Test")
        patient.ticket_number = "B-001"
        assert patient.ticket_number.startswith("B-")

    def test_ticket_emergency_format(self):
        patient = Patient("P001", "Test")
        patient.ticket_number = "EMERGENCY"
        assert patient.ticket_number == "EMERGENCY"


class TestHTPatient:
    def test_ht_patient_creation(self):
        patient = HTPatient(id="P001", name="John", priority=3)
        assert patient.id == "P001"
        assert patient.name == "John"
        assert patient.priority == 3
        assert patient.status == "waiting"
        assert patient.is_walk_in is False

    def test_ht_patient_comparison(self):
        p1 = HTPatient(id="P001", name="A", priority=1)
        p2 = HTPatient(id="P002", name="B", priority=2)
        assert p1 < p2

    def test_ht_patient_properties(self):
        patient = HTPatient(id="P001", name="John", priority=2)
        assert patient.checked_in_at is None
        assert patient.department is None
        assert patient.doctor_id is None
        assert patient.appointment_time is None
