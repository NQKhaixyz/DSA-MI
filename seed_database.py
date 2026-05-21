#!/usr/bin/env python3
"""Seed database with sample patients, appointments, and queue entries."""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:5000"


def add_patient(name, age, gender, phone, address, symptoms, priority=3):
    data = {
        "name": name,
        "age": age,
        "gender": gender,
        "phone": phone,
        "address": address,
        "symptoms": symptoms,
        "priority": priority,
    }
    r = requests.post(f"{BASE_URL}/api/patients", json=data)
    return r.json() if r.status_code == 201 else None


def book_appointment(patient_id, doctor_id, date, time_slot):
    data = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "date": date,
        "time_slot": time_slot,
    }
    r = requests.post(f"{BASE_URL}/api/appointments", json=data)
    return r.json() if r.status_code == 201 else None


def checkin_patient(patient_id, department_id, priority=3):
    data = {
        "patient_id": patient_id,
        "department_id": department_id,
        "priority": priority,
    }
    r = requests.post(f"{BASE_URL}/api/checkin", json=data)
    return r.json() if r.status_code == 200 else None


if __name__ == "__main__":
    print("Seeding database with sample data...")

    # Add patients
    patients = [
        (
            "Nguyen Van A",
            45,
            "male",
            "0901234567",
            "123 Le Loi, Q1",
            "Dau dau, sot cao",
            1,
        ),
        (
            "Tran Thi B",
            32,
            "female",
            "0912345678",
            "456 Nguyen Trai, Q5",
            "Dau bung",
            2,
        ),
        (
            "Le Van C",
            28,
            "male",
            "0923456789",
            "789 Tran Hung Dao, Q3",
            "Ho, kho tho",
            3,
        ),
        (
            "Pham Thi D",
            55,
            "female",
            "0934567890",
            "321 Hai Ba Trung, Q1",
            "Dau nguc",
            2,
        ),
        (
            "Hoang Van E",
            8,
            "male",
            "0945678901",
            "654 Ly Tu Trong, Q10",
            "Sot, phat ban",
            1,
        ),
        (
            "Vu Thi F",
            67,
            "female",
            "0956789012",
            "987 Cach Mang Thang 8, Q3",
            "Tieu duong",
            3,
        ),
        ("Do Van G", 19, "male", "0967890123", "147 Vo Thi Sau, Q1", "Gay xuong", 3),
        (
            "Ngo Thi H",
            41,
            "female",
            "0978901234",
            "258 Phan Xich Long, Q5",
            "Dau dau man tinh",
            2,
        ),
    ]

    patient_ids = []
    for p in patients:
        result = add_patient(*p)
        if result:
            patient_ids.append(result["id"])
            print(f"Added patient: {p[0]} (ID: {result['id']})")

    # Book appointments
    today = datetime.now().strftime("%Y-%m-%d")
    appointments = [
        (patient_ids[1], 2, today, "09:00"),
        (patient_ids[3], 4, today, "10:00"),
        (patient_ids[7], 2, today, "14:00"),
    ]

    for app in appointments:
        result = book_appointment(*app)
        if result:
            print(f"Booked appointment for patient {app[0]}")

    # Check-in patients
    checkins = [
        (patient_ids[0], 1, 1),  # Emergency
        (patient_ids[2], 2, 3),  # Walk-in
        (patient_ids[4], 3, 1),  # Emergency
        (patient_ids[5], 2, 3),  # Walk-in
        (patient_ids[6], 5, 3),  # Walk-in
    ]

    for c in checkins:
        result = checkin_patient(*c)
        if result:
            print(f"Checked in patient {c[0]} to department {c[1]}")

    print("\nDatabase seeded successfully!")
    print(f"Total patients added: {len(patient_ids)}")
    print("Visit http://127.0.0.1:5000 to view the dashboard.")
