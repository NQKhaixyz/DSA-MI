#!/usr/bin/env python3
"""
Comprehensive Mock Data Generator for Hospital Triage System.

Generates realistic Vietnamese hospital data including patients, doctors,
appointments, check-ins, and queue data. Exports to JSON and CSV formats.
Compatible with TriageSystem from triage_system.py.
"""

import csv
import json
import logging
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from faker import Faker
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEPARTMENTS = [
    {"id": "DEPT01", "name": "Noi tong quat"},
    {"id": "DEPT02", "name": "Ngoai khoa"},
    {"id": "DEPT03", "name": "Nhi khoa"},
    {"id": "DEPT04", "name": "San khoa"},
    {"id": "DEPT05", "name": "Tai mui hong"},
]

VIETNAMESE_SYMPTOMS = [
    "Dau dau",
    "Sot",
    "Ho",
    "Dau bung",
    "Dau nguc",
    "Kho tho",
    "Buon non",
    "Tieu chay",
    "Tao bon",
    "Dau lung",
    "Dau co",
    "Chay mau mui",
    "Dau hong",
    "Mat tieng",
    "Nghe kem",
    "Chong mat",
    "Xuat huyet",
    "Phat ban",
    "Ngua",
    "Dau khop",
    "Suy nhuoc",
    "Mat ngu",
    "Lo au",
    "Dau mat",
    "Mo mat",
    "Chan an",
    "Khat nuoc",
    "Tieu nhieu",
    "Dau rang",
    "Dau co tim",
    "Hen suyen",
    "Huyet ap cao",
    "Huyet ap thap",
    "Dau dau man tinh",
    "Dot quy nhe",
    "Dau bao tu",
    "Viem da day",
    "Soi than",
    "Dau than",
    "Viem phoi",
    "Dau vai",
    "Te tay",
    "Te chan",
    "Chan thuong",
    "Gay xuong",
    "Bong",
    "Tram cam",
    "Roi loan tieu hoa",
    "Viem gan",
    "Viem tuy",
]

TIME_SLOTS = [
    "08:00-08:30",
    "08:30-09:00",
    "09:00-09:30",
    "09:30-10:00",
    "10:00-10:30",
    "10:30-11:00",
    "11:00-11:30",
    "11:30-12:00",
    "13:00-13:30",
    "13:30-14:00",
    "14:00-14:30",
    "14:30-15:00",
    "15:00-15:30",
    "15:30-16:00",
    "16:00-16:30",
    "16:30-17:00",
]

DANGER_LEVELS = [1, 2, 3, 3, 3, 3, 3]  # Weighted: fewer emergencies

MAX_PATIENTS_PER_SLOT = 4

# ---------------------------------------------------------------------------
# Faker Setup
# ---------------------------------------------------------------------------

fake = Faker("vi_VN")
Faker.seed(42)
random.seed(42)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def generate_vn_phone() -> str:
    """Generate a realistic Vietnamese phone number."""
    prefixes = [
        "090",
        "091",
        "092",
        "093",
        "094",
        "095",
        "096",
        "097",
        "098",
        "099",
        "032",
        "033",
        "034",
        "035",
        "036",
        "037",
        "038",
        "039",
        "081",
        "082",
        "083",
        "084",
        "085",
        "086",
        "087",
        "088",
        "089",
        "070",
        "076",
        "077",
        "078",
        "079",
        "052",
        "056",
        "058",
        "059",
        "0162",
        "0163",
        "0164",
        "0165",
        "0166",
        "0167",
        "0168",
        "0169",
    ]
    prefix = random.choice(prefixes)
    suffix_length = 11 - len(prefix)
    suffix = "".join(str(random.randint(0, 9)) for _ in range(suffix_length))
    return f"{prefix}{suffix}"


def random_date_of_birth(min_age: int = 0, max_age: int = 100) -> str:
    """Generate a random date of birth within an age range."""
    today = datetime.today()
    age = random.randint(min_age, max_age)
    birth_year = today.year - age
    try:
        dob = datetime(birth_year, random.randint(1, 12), random.randint(1, 28))
    except ValueError:
        dob = datetime(birth_year, 1, 1)
    return dob.strftime("%Y-%m-%d")


def random_admission_date(days_back: int = 365, days_forward: int = 30) -> str:
    """Generate a random admission date (mix of past and future)."""
    today = datetime.today()
    delta = random.randint(-days_back, days_forward)
    adm = today + timedelta(days=delta)
    return adm.strftime("%Y-%m-%d")


def slot_to_datetime(date_str: str, slot_str: str) -> datetime:
    """Convert a date + time-slot string to a datetime object."""
    start_time = slot_str.split("-")[0]
    return datetime.strptime(f"{date_str} {start_time}", "%Y-%m-%d %H:%M")


def ensure_dir(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------


def generate_patients(count: int = 1000) -> List[Dict[str, Any]]:
    """
    Generate a list of realistic Vietnamese patient dictionaries.

    Args:
        count: Number of patients to generate (default 1000).

    Returns:
        List of patient dicts with keys: patient_id, name, dob, age, phone,
        address, symptoms, danger_level, is_booked, admission_date.
    """
    patients = []
    logger.info(f"Generating {count} patients...")

    for i in tqdm(range(1, count + 1), desc="Patients", unit="patient", ncols=80):
        try:
            age = random.randint(0, 95)
            dob = random_date_of_birth(age, age)
            danger_level = random.choice(DANGER_LEVELS)
            symptoms = ", ".join(
                random.sample(VIETNAMESE_SYMPTOMS, k=random.randint(1, 3))
            )

            patient = {
                "patient_id": f"P{i:04d}",
                "name": fake.name(),
                "dob": dob,
                "age": age,
                "phone": generate_vn_phone(),
                "address": fake.address().replace("\n", ", "),
                "symptoms": symptoms,
                "danger_level": danger_level,
                "is_booked": False,
                "admission_date": random_admission_date(),
            }
            patients.append(patient)
        except Exception as exc:
            logger.warning(f"Error generating patient {i}: {exc}")

    logger.info(f"Generated {len(patients)} patients successfully.")
    return patients


def generate_doctors(count: int = 20) -> List[Dict[str, Any]]:
    """
    Generate a list of Vietnamese doctor dictionaries across 5 departments.

    Args:
        count: Number of doctors to generate (default 20, minimum 5).

    Returns:
        List of doctor dicts with keys: doctor_id, name, department_id,
        department_name, experience_years, phone.
    """
    if count < len(DEPARTMENTS):
        count = len(DEPARTMENTS)
        logger.warning(
            f"Doctor count raised to minimum {count} to cover all departments."
        )

    doctors = []
    logger.info(f"Generating {count} doctors...")

    # Ensure at least one doctor per department
    for dept in DEPARTMENTS:
        doctor = {
            "doctor_id": f"D{len(doctors) + 1:03d}",
            "name": fake.name(),
            "department_id": dept["id"],
            "department_name": dept["name"],
            "experience_years": random.randint(1, 30),
            "phone": generate_vn_phone(),
        }
        doctors.append(doctor)

    # Remaining doctors distributed randomly
    remaining = count - len(doctors)
    for i in tqdm(range(remaining), desc="Doctors", unit="doctor", ncols=80):
        try:
            dept = random.choice(DEPARTMENTS)
            doctor = {
                "doctor_id": f"D{len(doctors) + 1:03d}",
                "name": fake.name(),
                "department_id": dept["id"],
                "department_name": dept["name"],
                "experience_years": random.randint(1, 30),
                "phone": generate_vn_phone(),
            }
            doctors.append(doctor)
        except Exception as exc:
            logger.warning(f"Error generating doctor: {exc}")

    logger.info(f"Generated {len(doctors)} doctors successfully.")
    return doctors


def generate_appointments(
    patients: List[Dict[str, Any]],
    doctors: List[Dict[str, Any]],
    count: int = 500,
) -> List[Dict[str, Any]]:
    """
    Generate realistic appointments respecting the 4-patients-per-slot limit.

    Args:
        patients: List of patient dicts.
        doctors: List of doctor dicts.
        count: Number of appointments to generate (default 500).

    Returns:
        List of appointment dicts with keys: appointment_id, patient_id,
        doctor_id, date, time_slot, status, created_at.
    """
    appointments: List[Dict[str, Any]] = []
    slot_tracker: Dict[Tuple[str, str, str], int] = {}
    used_patient_ids: Set[str] = set()

    # Build a pool of patients who are not already used
    patient_pool = [p for p in patients if not p.get("is_booked", False)]
    if len(patient_pool) < count:
        logger.warning(
            f"Only {len(patient_pool)} unbooked patients available; "
            f"some patients will be reused."
        )

    logger.info(f"Generating {count} appointments...")

    attempts = 0
    max_attempts = count * 10
    pbar = tqdm(total=count, desc="Appointments", unit="appt", ncols=80)

    while len(appointments) < count and attempts < max_attempts:
        attempts += 1
        try:
            doctor = random.choice(doctors)
            date = random_admission_date(days_back=30, days_forward=60)
            slot = random.choice(TIME_SLOTS)
            slot_key = (date, slot, doctor["doctor_id"])

            current_count = slot_tracker.get(slot_key, 0)
            if current_count >= MAX_PATIENTS_PER_SLOT:
                continue

            # Pick a patient
            if patient_pool:
                patient = random.choice(patient_pool)
            else:
                patient = random.choice(patients)

            patient_id = patient["patient_id"]

            # Mark patient as booked (first time only)
            if patient_id not in used_patient_ids:
                patient["is_booked"] = True
                used_patient_ids.add(patient_id)
                if patient in patient_pool:
                    patient_pool.remove(patient)

            appointment = {
                "appointment_id": f"A{len(appointments) + 1:04d}",
                "patient_id": patient_id,
                "doctor_id": doctor["doctor_id"],
                "date": date,
                "time_slot": slot,
                "status": random.choice(
                    ["confirmed", "completed", "cancelled", "no_show"]
                ),
                "created_at": (
                    datetime.strptime(date, "%Y-%m-%d")
                    - timedelta(days=random.randint(1, 14))
                ).strftime("%Y-%m-%d %H:%M:%S"),
            }
            appointments.append(appointment)
            slot_tracker[slot_key] = current_count + 1
            pbar.update(1)
        except Exception as exc:
            logger.warning(f"Error generating appointment: {exc}")

    pbar.close()
    logger.info(f"Generated {len(appointments)} appointments successfully.")
    return appointments


def generate_checkins(
    patients: List[Dict[str, Any]],
    doctors: List[Dict[str, Any]],
    appointments: List[Dict[str, Any]],
    count: int = 300,
) -> List[Dict[str, Any]]:
    """
    Generate check-in records for patients.

    Creates a mix of emergency, booked, and walk-in check-ins.

    Args:
        patients: List of patient dicts.
        doctors: List of doctor dicts.
        appointments: List of appointment dicts.
        count: Number of check-ins to generate.

    Returns:
        List of check-in dicts with keys: checkin_id, patient_id, doctor_id,
        department_id, checkin_type, priority, checked_in_at, ticket_number.
    """
    checkins = []
    doctors_by_id = {d["doctor_id"]: d for d in doctors}

    # Map appointments by patient_id for quick lookup
    patient_appointments: Dict[str, List[Dict[str, Any]]] = {}
    for appt in appointments:
        pid = appt["patient_id"]
        patient_appointments.setdefault(pid, []).append(appt)

    # Select a subset of patients for check-ins
    checkin_patients = random.sample(patients, min(count, len(patients)))
    if len(checkin_patients) < count:
        # Allow repeats if we need more
        extras = random.choices(patients, k=count - len(checkin_patients))
        checkin_patients.extend(extras)

    logger.info(f"Generating {count} check-ins...")

    for i, patient in enumerate(
        tqdm(checkin_patients, desc="Check-ins", unit="chk", ncols=80)
    ):
        try:
            danger_level = patient.get("danger_level", 3)
            # Override checkin type distribution: 10% emergency, 30% booked, 60% walk-in
            roll = random.random()
            if roll < 0.10:
                checkin_type = "emergency"
                danger_level = 1
            elif roll < 0.40 and patient.get("is_booked", False):
                checkin_type = "booked"
                danger_level = 2
            else:
                checkin_type = "walk_in"
                danger_level = 3

            # Determine doctor / department
            appts = patient_appointments.get(patient["patient_id"], [])
            if checkin_type == "booked" and appts:
                appt = random.choice(appts)
                doctor_id = appt["doctor_id"]
                dept_id = doctors_by_id.get(doctor_id, {}).get(
                    "department_id", random.choice(DEPARTMENTS)["id"]
                )
            else:
                doctor_id = None
                dept_id = random.choice(DEPARTMENTS)["id"]

            now = datetime.now()
            checked_in_at = (
                now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 12))
            ).strftime("%Y-%m-%d %H:%M:%S")

            ticket_prefix = {"emergency": "E", "booked": "B", "walk_in": "W"}.get(
                checkin_type, "W"
            )
            ticket_number = f"{ticket_prefix}-{i + 1:03d}"

            checkin = {
                "checkin_id": f"C{i + 1:04d}",
                "patient_id": patient["patient_id"],
                "doctor_id": doctor_id,
                "department_id": dept_id,
                "checkin_type": checkin_type,
                "priority": danger_level,
                "checked_in_at": checked_in_at,
                "ticket_number": ticket_number,
            }
            checkins.append(checkin)
        except Exception as exc:
            logger.warning(f"Error generating check-in: {exc}")

    logger.info(f"Generated {len(checkins)} check-ins successfully.")
    return checkins


# ---------------------------------------------------------------------------
# Dataset Assembly & Persistence
# ---------------------------------------------------------------------------


def generate_full_dataset(
    data_dir: str = "data",
    patient_count: int = 1000,
    doctor_count: int = 20,
    appointment_count: int = 500,
    checkin_count: int = 300,
) -> Dict[str, Any]:
    """
    Generate the complete mock dataset and persist to JSON and CSV.

    Args:
        data_dir: Directory to save output files.
        patient_count: Number of patients.
        doctor_count: Number of doctors.
        appointment_count: Number of appointments.
        checkin_count: Number of check-ins.

    Returns:
        Dictionary with keys: patients, doctors, appointments, checkins, departments.
    """
    base_path = Path(data_dir)
    ensure_dir(base_path)

    logger.info("=" * 60)
    logger.info("Starting full dataset generation")
    logger.info("=" * 60)

    patients = generate_patients(count=patient_count)
    doctors = generate_doctors(count=doctor_count)
    appointments = generate_appointments(patients, doctors, count=appointment_count)
    checkins = generate_checkins(patients, doctors, appointments, count=checkin_count)

    dataset = {
        "departments": DEPARTMENTS,
        "patients": patients,
        "doctors": doctors,
        "appointments": appointments,
        "checkins": checkins,
    }

    # Save JSON
    json_path = base_path / "mock_data.json"
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved JSON dataset to {json_path}")
    except Exception as exc:
        logger.error(f"Failed to save JSON: {exc}")
        raise

    # Save individual CSVs
    try:
        _save_csv(base_path / "patients.csv", patients)
        _save_csv(base_path / "doctors.csv", doctors)
        _save_csv(base_path / "appointments.csv", appointments)
        _save_csv(base_path / "checkins.csv", checkins)
        _save_csv(base_path / "departments.csv", DEPARTMENTS)
        logger.info(f"Saved CSV datasets to {base_path}")
    except Exception as exc:
        logger.error(f"Failed to save CSV: {exc}")
        raise

    logger.info("=" * 60)
    logger.info("Dataset generation complete!")
    logger.info("=" * 60)

    return dataset


def _save_csv(path: Path, records: List[Dict[str, Any]]) -> None:
    """Helper to write a list of dicts to a CSV file."""
    if not records:
        logger.warning(f"No records to write to {path}")
        return
    keys = list(records[0].keys())
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(records)


# ---------------------------------------------------------------------------
# Loader for TriageSystem
# ---------------------------------------------------------------------------


def load_mock_data(triage_system: Any) -> None:
    """
    Load generated mock data into a TriageSystem instance.

    This function reads the JSON dataset from data/mock_data.json and injects
    patients, doctors, departments, appointments, and check-ins into the provided
    TriageSystem object (from triage_system.py).

    Args:
        triage_system: An instance of TriageSystem.

    Raises:
        FileNotFoundError: If data/mock_data.json does not exist.
        AttributeError: If triage_system lacks expected attributes.
    """
    json_path = Path("data") / "mock_data.json"
    if not json_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {json_path}. Run generate_full_dataset() first."
        )

    logger.info(f"Loading mock data from {json_path}...")

    with open(json_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    # Inject departments
    for dept in tqdm(
        dataset.get("departments", []), desc="Departments", unit="dept", ncols=80
    ):
        dept_id = dept["id"]
        dept_name = dept["name"]
        if dept_id not in triage_system.departments:
            # Lazy import to avoid hard dependency
            try:
                from triage_system import Department
            except ImportError:
                logger.error("Cannot import Department from triage_system")
                raise
            triage_system.departments[dept_id] = Department(dept_id, dept_name)

    # Inject doctors
    for doc in tqdm(dataset.get("doctors", []), desc="Doctors", unit="doc", ncols=80):
        doc_id = doc["doctor_id"]
        if doc_id not in triage_system.doctors:
            try:
                from triage_system import Doctor
            except ImportError:
                logger.error("Cannot import Doctor from triage_system")
                raise
            triage_system.doctors[doc_id] = Doctor(
                doctor_id=doc_id,
                name=doc["name"],
                department_id=doc["department_id"],
            )
            triage_system.departments[doc["department_id"]].doctor_ids.add(doc_id)

    # Inject patients
    for pat in tqdm(dataset.get("patients", []), desc="Patients", unit="pat", ncols=80):
        pat_id = pat["patient_id"]
        if pat_id not in triage_system.patients:
            try:
                from triage_system import Patient
            except ImportError:
                logger.error("Cannot import Patient from triage_system")
                raise
            triage_system.patients[pat_id] = Patient(
                patient_id=pat_id,
                name=pat["name"],
                age=pat.get("age", 0),
                symptoms=pat.get("symptoms", ""),
                danger_level=pat.get("danger_level", 3),
                is_booked=pat.get("is_booked", False),
            )

    # Book appointments into the system
    for appt in tqdm(
        dataset.get("appointments", []), desc="Appointments", unit="appt", ncols=80
    ):
        try:
            patient_id = appt["patient_id"]
            doctor_id = appt["doctor_id"]
            date = appt["date"]
            time_slot = appt["time_slot"]

            patient_data = {
                "patient_id": patient_id,
                "name": triage_system.patients.get(patient_id, {}).name
                if hasattr(triage_system.patients.get(patient_id), "name")
                else "Unknown",
                "age": triage_system.patients.get(patient_id, {}).age
                if hasattr(triage_system.patients.get(patient_id), "age")
                else 0,
                "symptoms": triage_system.patients.get(patient_id, {}).symptoms
                if hasattr(triage_system.patients.get(patient_id), "symptoms")
                else "",
            }

            result = triage_system.book_appointment(
                patient_data, date, time_slot, doctor_id
            )
            if result.get("status") == "success":
                # Mark patient as booked and link doctor
                patient = triage_system.patients.get(patient_id)
                if patient:
                    patient.is_booked = True
                    patient.doctor_id = doctor_id
                    patient.appointment_time = slot_to_datetime(date, time_slot)
        except Exception as exc:
            logger.warning(
                f"Failed to book appointment {appt.get('appointment_id')}: {exc}"
            )

    # Check-ins -> populate queues
    for chk in tqdm(
        dataset.get("checkins", []), desc="Check-ins", unit="chk", ncols=80
    ):
        try:
            patient_id = chk["patient_id"]
            dept_id = chk["department_id"]
            doctor_id = chk.get("doctor_id")
            priority = chk.get("priority", 3)
            checkin_type = chk.get("checkin_type", "walk_in")

            patient = triage_system.patients.get(patient_id)
            if not patient:
                continue

            patient.danger_level = priority
            patient.priority = priority

            if checkin_type == "emergency":
                triage_system.add_to_emergency_queue(dept_id, patient)
            elif checkin_type == "booked" and doctor_id:
                appt_time = patient.appointment_time or datetime.now()
                triage_system.add_to_booked_queue(doctor_id, patient, appt_time)
            else:
                triage_system.add_to_walk_in_queue(dept_id, patient)
        except Exception as exc:
            logger.warning(f"Failed to check in patient {chk.get('patient_id')}: {exc}")

    logger.info("Mock data loaded into TriageSystem successfully.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Hospital Mock Data Generator")
    parser.add_argument("--patients", type=int, default=1000, help="Number of patients")
    parser.add_argument("--doctors", type=int, default=20, help="Number of doctors")
    parser.add_argument(
        "--appointments", type=int, default=500, help="Number of appointments"
    )
    parser.add_argument("--checkins", type=int, default=300, help="Number of check-ins")
    parser.add_argument("--output", type=str, default="data", help="Output directory")
    args = parser.parse_args()

    try:
        generate_full_dataset(
            data_dir=args.output,
            patient_count=args.patients,
            doctor_count=args.doctors,
            appointment_count=args.appointments,
            checkin_count=args.checkins,
        )
        return 0
    except Exception as exc:
        logger.error(f"Generation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
