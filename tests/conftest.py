import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime, timedelta
from triage_system import Patient, Doctor, Department, TriageSystem
from hospital_triage import (
    Patient as HTPatient,
    Doctor as HTDoctor,
    Department as HTDepartment,
)
from billing_system import Bill, BillingSystem


@pytest.fixture
def triage_system():
    return TriageSystem()


@pytest.fixture
def billing_system():
    return BillingSystem()


@pytest.fixture
def sample_patient():
    return Patient("P001", "John Doe", age=30, symptoms="Headache", danger_level=3)


@pytest.fixture
def sample_doctor():
    return Doctor("D001", "Dr. Smith", "DEPT01")


@pytest.fixture
def sample_department():
    return Department("DEPT01", "Emergency")


@pytest.fixture
def sample_patient_ht():
    return HTPatient(id="P001", name="John Doe", priority=3)


@pytest.fixture
def sample_doctor_ht():
    return HTDoctor(id="D001", name="Dr. Smith", department="Emergency")


@pytest.fixture
def sample_department_ht():
    return HTDepartment(name="Emergency")


@pytest.fixture
def setup_triage_system():
    ts = TriageSystem()
    ts.departments["DEPT01"] = Department("DEPT01", "Emergency")
    ts.departments["DEPT02"] = Department("DEPT02", "Cardiology")
    ts.doctors["D001"] = Doctor("D001", "Dr. Smith", "DEPT01")
    ts.doctors["D002"] = Doctor("D002", "Dr. Jones", "DEPT02")
    ts.departments["DEPT01"].doctor_ids = {"D001"}
    ts.departments["DEPT02"].doctor_ids = {"D002"}
    return ts


@pytest.fixture
def mock_datetime_now(monkeypatch):
    fixed_time = datetime(2024, 1, 15, 10, 0, 0)

    class MockDatetime:
        @classmethod
        def now(cls):
            return fixed_time

        @classmethod
        def __call__(cls, *args, **kwargs):
            return datetime(*args, **kwargs)

    monkeypatch.setattr("triage_system.datetime", MockDatetime)
    return fixed_time


@pytest.fixture
def sample_services():
    return ["consultation", "blood_test", "prescription"]
