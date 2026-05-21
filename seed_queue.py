#!/usr/bin/env python3
"""Seed queue entries for patients."""

import sqlite3
from datetime import datetime

DB_PATH = "instance/hospital.db"


def seed_queue():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if queue_entries table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='queue_entries'"
    )
    if not cursor.fetchone():
        print("Queue entries table not found.")
        return

    # Clear existing queue
    cursor.execute("DELETE FROM queue_entries")

    # Add queue entries for patients
    queue_data = [
        (1, 1, 1, "waiting", datetime.now()),
        (2, 2, 2, "waiting", datetime.now()),
        (3, 2, 3, "waiting", datetime.now()),
        (4, 4, 2, "waiting", datetime.now()),
        (5, 3, 1, "waiting", datetime.now()),
        (6, 2, 3, "waiting", datetime.now()),
        (7, 5, 3, "waiting", datetime.now()),
        (8, 2, 2, "waiting", datetime.now()),
    ]

    for q in queue_data:
        try:
            cursor.execute(
                """
                INSERT INTO queue_entries (patient_id, department_id, priority, status, checked_in_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                q,
            )
            print(f"Added queue entry for patient {q[0]} in department {q[1]}")
        except sqlite3.Error as e:
            print(f"Error: {e}")

    conn.commit()
    conn.close()
    print("\nQueue seeded successfully!")


if __name__ == "__main__":
    seed_queue()
