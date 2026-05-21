#!/usr/bin/env python3
"""Seed database with sample patients using direct SQL."""

import sqlite3
from datetime import datetime, timedelta
import random

DB_PATH = "instance/hospital.db"


def seed_patients():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if patients table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='patients'"
    )
    if not cursor.fetchone():
        print(
            "Patients table not found. Please run the Flask app first to create tables."
        )
        return

    # Check schema
    cursor.execute("PRAGMA table_info(patients)")
    columns = cursor.fetchall()
    print("Patients table columns:", [c[1] for c in columns])

    # Clear existing data
    cursor.execute("DELETE FROM patients")

    # Sample Vietnamese patients
    patients = [
        (
            "Nguyen",
            "Van A",
            "0901234567",
            "nguyenvana@email.com",
            45,
            "male",
            "Dau dau, sot cao",
            "Waiting",
            1,
        ),
        (
            "Tran",
            "Thi B",
            "0912345678",
            "tranthib@email.com",
            32,
            "female",
            "Dau bung",
            "Waiting",
            2,
        ),
        (
            "Le",
            "Van C",
            "0923456789",
            "levanc@email.com",
            28,
            "male",
            "Ho, kho tho",
            "Waiting",
            3,
        ),
        (
            "Pham",
            "Thi D",
            "0934567890",
            "phamthid@email.com",
            55,
            "female",
            "Dau nguc",
            "Waiting",
            2,
        ),
        (
            "Hoang",
            "Van E",
            "0945678901",
            "hoangvane@email.com",
            8,
            "male",
            "Sot, phat ban",
            "Waiting",
            1,
        ),
        (
            "Vu",
            "Thi F",
            "0956789012",
            "vuthif@email.com",
            67,
            "female",
            "Tieu duong",
            "Waiting",
            3,
        ),
        (
            "Do",
            "Van G",
            "0967890123",
            "dovang@email.com",
            19,
            "male",
            "Gay xuong",
            "Waiting",
            3,
        ),
        (
            "Ngo",
            "Thi H",
            "0978901234",
            "ngothih@email.com",
            41,
            "female",
            "Dau dau man tinh",
            "Waiting",
            2,
        ),
    ]

    # Get actual columns
    cursor.execute("PRAGMA table_info(patients)")
    col_names = [c[1] for c in cursor.fetchall()]

    for p in patients:
        try:
            cursor.execute(
                """
                INSERT INTO patients (first_name, last_name, phone, email, gender, status, priority, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (p[0], p[1], p[2], p[3], p[5], p[7], p[8], datetime.now()),
            )
            print(f"Added patient: {p[0]} {p[1]}")
        except sqlite3.Error as e:
            print(f"Error inserting patient {p[0]} {p[1]}: {e}")

    conn.commit()

    # Verify
    cursor.execute("SELECT COUNT(*) FROM patients")
    count = cursor.fetchone()[0]
    print(f"\nAdded {count} patients to database")

    conn.close()
    print("Database seeded successfully!")
    print("Visit http://127.0.0.1:5000 to view the dashboard.")


if __name__ == "__main__":
    seed_patients()
