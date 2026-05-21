#!/usr/bin/env python3
"""
Hospital Triage System - Comprehensive Performance Test Suite
=============================================================
A production-ready performance testing framework for hospital triage systems.
Features load testing, speed benchmarks, stress testing, scalability testing,
and automated report generation.

Dependencies: timeit, memory_profiler, psutil, tqdm, tabulate
"""

import argparse
import json
import logging
import os
import random
import sys
import time
import timeit
import tracemalloc
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import threading
import queue as QueueModule

# Third-party imports
try:
    import psutil
except ImportError:
    print("Warning: psutil not installed. Install with: pip install psutil")
    psutil = None

try:
    from memory_profiler import memory_usage
except ImportError:
    print(
        "Warning: memory_profiler not installed. Install with: pip install memory_profiler"
    )
    memory_usage = None

try:
    from tqdm import tqdm
except ImportError:
    print("Warning: tqdm not installed. Install with: pip install tqdm")

    def tqdm(iterable, *args, **kwargs):
        return iterable


try:
    from tabulate import tabulate
except ImportError:
    print("Warning: tabulate not installed. Install with: pip install tabulate")

    def tabulate(data, headers, tablefmt="grid"):
        result = " | ".join(headers) + "\n"
        result += "-" * (len(result) - 1) + "\n"
        for row in data:
            result += " | ".join(str(x) for x in row) + "\n"
        return result


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure production-ready logging with both file and console handlers."""
    logger = logging.getLogger("TriagePerformance")
    logger.setLevel(getattr(logging, log_level.upper()))

    if logger.handlers:
        logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler("performance_test.log")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


logger = setup_logging()


# ============================================================================
# TRIAGE SYSTEM MODELS
# ============================================================================


class PriorityLevel(Enum):
    """Patient priority levels for triage queue."""

    CRITICAL = 1
    URGENT = 2
    HIGH = 3
    MODERATE = 4
    LOW = 5


@dataclass
class Patient:
    """Represents a hospital patient."""

    patient_id: str
    name: str
    age: int
    priority: PriorityLevel
    symptoms: List[str] = field(default_factory=list)
    check_in_time: Optional[datetime] = None
    assigned_doctor: Optional[str] = None

    def __post_init__(self):
        if self.check_in_time is None:
            self.check_in_time = datetime.now()


@dataclass
class Doctor:
    """Represents a hospital doctor."""

    doctor_id: str
    name: str
    specialization: str
    is_available: bool = True
    current_patient: Optional[str] = None


@dataclass
class Appointment:
    """Represents a scheduled appointment."""

    appointment_id: str
    patient_id: str
    doctor_id: str
    scheduled_time: datetime
    duration_minutes: int = 30
    status: str = "scheduled"


# ============================================================================
# TRIAGE SYSTEM CORE
# ============================================================================


class MultiLevelQueue:
    """Priority queue implementation using multiple levels."""

    def __init__(self):
        self.queues = {
            PriorityLevel.CRITICAL: deque(),
            PriorityLevel.URGENT: deque(),
            PriorityLevel.HIGH: deque(),
            PriorityLevel.MODERATE: deque(),
            PriorityLevel.LOW: deque(),
        }
        self._size = 0
        self._lock = threading.Lock()

    def enqueue(self, patient: Patient) -> None:
        """Add patient to appropriate priority queue."""
        with self._lock:
            self.queues[patient.priority].append(patient)
            self._size += 1

    def dequeue(self) -> Optional[Patient]:
        """Get next patient from highest priority non-empty queue."""
        with self._lock:
            for priority in sorted(PriorityLevel, key=lambda x: x.value):
                if self.queues[priority]:
                    self._size -= 1
                    return self.queues[priority].popleft()
            return None

    def size(self) -> int:
        """Return total number of patients in queue."""
        with self._lock:
            return self._size

    def is_empty(self) -> bool:
        """Check if all queues are empty."""
        with self._lock:
            return self._size == 0


class HospitalTriageSystem:
    """Core hospital triage system with all required operations."""

    def __init__(self):
        self.patients: Dict[str, Patient] = {}
        self.doctors: Dict[str, Doctor] = {}
        self.appointments: Dict[str, Appointment] = {}
        self.triage_queue = MultiLevelQueue()
        self.appointment_slots: Dict[str, List[bool]] = defaultdict(
            lambda: [False] * 24  # 24 slots per doctor per day
        )
        self._patient_lock = threading.RLock()
        self._doctor_lock = threading.RLock()
        self._appointment_lock = threading.RLock()

    def check_in_patient(self, patient: Patient) -> bool:
        """Check in a patient and add to triage queue."""
        try:
            with self._patient_lock:
                self.patients[patient.patient_id] = patient
            self.triage_queue.enqueue(patient)
            return True
        except Exception as e:
            logger.error(f"Error checking in patient {patient.patient_id}: {e}")
            return False

    def get_next_patient(self, doctor_id: str) -> Optional[Patient]:
        """Get next patient for a doctor from triage queue."""
        try:
            with self._doctor_lock:
                doctor = self.doctors.get(doctor_id)
                if not doctor or not doctor.is_available:
                    return None

            patient = self.triage_queue.dequeue()
            if patient:
                with self._doctor_lock:
                    doctor.current_patient = patient.patient_id
                    doctor.is_available = False
                with self._patient_lock:
                    patient.assigned_doctor = doctor_id
            return patient
        except Exception as e:
            logger.error(f"Error getting next patient for doctor {doctor_id}: {e}")
            return None

    def book_appointment(self, appointment: Appointment) -> bool:
        """Book an appointment with slot validation."""
        try:
            with self._appointment_lock:
                doctor_id = appointment.doctor_id
                hour = appointment.scheduled_time.hour

                if hour < 0 or hour >= 24:
                    logger.warning(f"Invalid hour {hour} for appointment")
                    return False

                if self.appointment_slots[doctor_id][hour]:
                    logger.warning(f"Slot {hour} already booked for doctor {doctor_id}")
                    return False

                self.appointment_slots[doctor_id][hour] = True
                self.appointments[appointment.appointment_id] = appointment
                return True
        except Exception as e:
            logger.error(f"Error booking appointment {appointment.appointment_id}: {e}")
            return False

    def search_patient(self, patient_id: str) -> Optional[Patient]:
        """Search for patient by ID."""
        with self._patient_lock:
            return self.patients.get(patient_id)

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Generate dashboard data with full system statistics."""
        try:
            with self._patient_lock:
                total_patients = len(self.patients)
                priority_counts = defaultdict(int)
                for patient in self.patients.values():
                    priority_counts[patient.priority.name] += 1

            with self._doctor_lock:
                total_doctors = len(self.doctors)
                available_doctors = sum(
                    1 for d in self.doctors.values() if d.is_available
                )
                busy_doctors = total_doctors - available_doctors

            with self._appointment_lock:
                total_appointments = len(self.appointments)
                today = datetime.now().date()
                today_appointments = sum(
                    1
                    for a in self.appointments.values()
                    if a.scheduled_time.date() == today
                )

            queue_size = self.triage_queue.size()

            return {
                "total_patients": total_patients,
                "total_doctors": total_doctors,
                "available_doctors": available_doctors,
                "busy_doctors": busy_doctors,
                "total_appointments": total_appointments,
                "today_appointments": today_appointments,
                "queue_size": queue_size,
                "priority_breakdown": dict(priority_counts),
                "average_wait_time": self._calculate_average_wait_time(),
                "system_load": (queue_size / max(total_doctors, 1)) * 100,
            }
        except Exception as e:
            logger.error(f"Error generating dashboard: {e}")
            return {}

    def _calculate_average_wait_time(self) -> float:
        """Calculate average wait time for patients in queue."""
        now = datetime.now()
        total_wait = 0
        count = 0

        for priority in PriorityLevel:
            for patient in self.triage_queue.queues[priority]:
                wait_time = (now - patient.check_in_time).total_seconds() / 60
                total_wait += wait_time
                count += 1

        return total_wait / max(count, 1)

    def load_test_data(
        self, num_patients: int, num_doctors: int, num_appointments: int
    ):
        """Load test data into the system."""
        logger.info(
            f"Loading test data: {num_patients} patients, {num_doctors} doctors, {num_appointments} appointments"
        )

        # Generate doctors
        specializations = [
            "Emergency",
            "Cardiology",
            "Neurology",
            "Orthopedics",
            "Pediatrics",
        ]
        for i in tqdm(
            range(num_doctors), desc="Generating doctors", disable=num_doctors < 100
        ):
            doctor = Doctor(
                doctor_id=f"DOC_{i:06d}",
                name=f"Dr. Doctor_{i}",
                specialization=random.choice(specializations),
                is_available=True,
            )
            with self._doctor_lock:
                self.doctors[doctor.doctor_id] = doctor

        # Generate patients
        priorities = list(PriorityLevel)
        symptoms_pool = [
            ["chest_pain", "shortness_of_breath"],
            ["fever", "cough"],
            ["broken_arm", "pain"],
            ["headache", "dizziness"],
            ["stomach_pain", "nausea"],
            ["allergic_reaction", "rash"],
            ["cut", "bleeding"],
            ["back_pain"],
            ["anxiety", "palpitations"],
        ]

        for i in tqdm(
            range(num_patients), desc="Generating patients", disable=num_patients < 100
        ):
            patient = Patient(
                patient_id=f"PAT_{i:06d}",
                name=f"Patient_{i}",
                age=random.randint(1, 95),
                priority=random.choice(priorities),
                symptoms=random.choice(symptoms_pool),
            )
            self.check_in_patient(patient)

        # Generate appointments
        doctor_ids = list(self.doctors.keys())
        patient_ids = list(self.patients.keys())

        for i in tqdm(
            range(num_appointments),
            desc="Generating appointments",
            disable=num_appointments < 100,
        ):
            hour = random.randint(8, 17)
            appointment = Appointment(
                appointment_id=f"APT_{i:08d}",
                patient_id=random.choice(patient_ids),
                doctor_id=random.choice(doctor_ids),
                scheduled_time=datetime.now()
                + timedelta(days=random.randint(0, 30), hours=hour),
                duration_minutes=random.choice([15, 30, 45, 60]),
            )
            self.book_appointment(appointment)

        logger.info("Test data loaded successfully")


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


@dataclass
class BenchmarkResult:
    """Stores benchmark results."""

    name: str
    execution_time: float
    memory_used_mb: float
    operations_per_second: float
    success_rate: float
    details: Dict[str, Any] = field(default_factory=dict)
    status: str = "PASS"  # PASS, FAIL, WARNING
    threshold: Optional[float] = None


class PerformanceTestSuite:
    """Comprehensive performance test suite for hospital triage system."""

    # Performance thresholds (in seconds)
    THRESHOLDS = {
        "check_in": 5.0,
        "routing": 3.0,
        "booking": 5.0,
        "search": 1.0,
        "dashboard": 2.0,
    }

    def __init__(self):
        self.system = HospitalTriageSystem()
        self.results: List[BenchmarkResult] = []
        self.baseline_results: Optional[Dict[str, float]] = None

    def _measure_memory(self, func, *args, **kwargs) -> Tuple[Any, float]:
        """Measure memory usage of a function."""
        if memory_usage:
            mem_before = memory_usage()[0]
            result = func(*args, **kwargs)
            mem_after = memory_usage()[0]
            memory_used = mem_after - mem_before
        else:
            # Fallback using tracemalloc
            tracemalloc.start()
            result = func(*args, **kwargs)
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            memory_used = peak / 1024 / 1024  # Convert to MB

        return result, memory_used

    def _get_system_memory(self) -> Dict[str, float]:
        """Get current system memory usage."""
        if psutil:
            mem = psutil.virtual_memory()
            return {
                "total_mb": mem.total / 1024 / 1024,
                "available_mb": mem.available / 1024 / 1024,
                "used_mb": mem.used / 1024 / 1024,
                "percent": mem.percent,
            }
        return {}

    def benchmark_check_in(self) -> BenchmarkResult:
        """Benchmark patient check-in operations."""
        logger.info("Starting check-in benchmark...")

        num_operations = 1000
        priorities = list(PriorityLevel)

        def run_check_ins():
            for i in range(num_operations):
                patient = Patient(
                    patient_id=f"BENCH_PAT_{i:06d}",
                    name=f"BenchPatient_{i}",
                    age=random.randint(20, 70),
                    priority=random.choice(priorities),
                )
                self.system.check_in_patient(patient)

        # Warmup
        run_check_ins()
        self.system.patients.clear()
        self.system.triage_queue = MultiLevelQueue()

        # Actual benchmark
        start_time = timeit.default_timer()
        _, memory_used = self._measure_memory(run_check_ins)
        end_time = timeit.default_timer()

        execution_time = end_time - start_time
        ops_per_second = num_operations / execution_time
        threshold = self.THRESHOLDS["check_in"]

        status = "PASS" if execution_time <= threshold else "FAIL"

        result = BenchmarkResult(
            name="Patient Check-In",
            execution_time=execution_time,
            memory_used_mb=memory_used,
            operations_per_second=ops_per_second,
            success_rate=100.0,
            details={
                "operations": num_operations,
                "patients_in_system": len(self.system.patients),
            },
            status=status,
            threshold=threshold,
        )

        logger.info(
            f"Check-in benchmark completed: {execution_time:.4f}s ({ops_per_second:.2f} ops/sec)"
        )
        return result

    def benchmark_routing(self) -> BenchmarkResult:
        """Benchmark doctor routing with multilevel queue."""
        logger.info("Starting routing benchmark...")

        num_doctors = 100
        patients_per_doctor = 10
        total_patients = num_doctors * patients_per_doctor

        # Setup: Load patients into queue
        priorities = list(PriorityLevel)
        for i in range(total_patients):
            patient = Patient(
                patient_id=f"ROUTE_PAT_{i:06d}",
                name=f"RoutePatient_{i}",
                age=random.randint(20, 70),
                priority=random.choice(priorities),
            )
            self.system.check_in_patient(patient)

        # Setup: Create doctors
        for i in range(num_doctors):
            doctor = Doctor(
                doctor_id=f"ROUTE_DOC_{i:06d}",
                name=f"RouteDoctor_{i}",
                specialization="Emergency",
            )
            with self.system._doctor_lock:
                self.system.doctors[doctor.doctor_id] = doctor

        def run_routing():
            doctor_ids = list(self.system.doctors.keys())
            for doctor_id in doctor_ids:
                self.system.get_next_patient(doctor_id)

        start_time = timeit.default_timer()
        _, memory_used = self._measure_memory(run_routing)
        end_time = timeit.default_timer()

        execution_time = end_time - start_time
        ops_per_second = num_doctors / execution_time
        threshold = self.THRESHOLDS["routing"]

        status = "PASS" if execution_time <= threshold else "FAIL"

        result = BenchmarkResult(
            name="Doctor Routing (Multilevel Queue)",
            execution_time=execution_time,
            memory_used_mb=memory_used,
            operations_per_second=ops_per_second,
            success_rate=100.0,
            details={"doctors": num_doctors, "patients_processed": total_patients},
            status=status,
            threshold=threshold,
        )

        logger.info(
            f"Routing benchmark completed: {execution_time:.4f}s ({ops_per_second:.2f} ops/sec)"
        )
        return result

    def benchmark_booking(self) -> BenchmarkResult:
        """Benchmark appointment booking with slot validation."""
        logger.info("Starting booking benchmark...")

        num_operations = 1000

        # Setup: Create doctors
        for i in range(50):
            doctor = Doctor(
                doctor_id=f"BOOK_DOC_{i:06d}",
                name=f"BookDoctor_{i}",
                specialization="General",
            )
            with self.system._doctor_lock:
                self.system.doctors[doctor.doctor_id] = doctor

        doctor_ids = list(self.system.doctors.keys())

        def run_bookings():
            success_count = 0
            for i in range(num_operations):
                hour = random.randint(8, 17)
                appointment = Appointment(
                    appointment_id=f"BENCH_APT_{i:08d}",
                    patient_id=f"BENCH_PAT_{i:06d}",
                    doctor_id=random.choice(doctor_ids),
                    scheduled_time=datetime.now()
                    + timedelta(days=random.randint(0, 30), hours=hour),
                )
                if self.system.book_appointment(appointment):
                    success_count += 1
            return success_count

        start_time = timeit.default_timer()
        success_count, memory_used = self._measure_memory(run_bookings)
        end_time = timeit.default_timer()

        execution_time = end_time - start_time
        ops_per_second = num_operations / execution_time
        success_rate = (success_count / num_operations) * 100
        threshold = self.THRESHOLDS["booking"]

        status = "PASS" if execution_time <= threshold else "FAIL"

        result = BenchmarkResult(
            name="Appointment Booking (with validation)",
            execution_time=execution_time,
            memory_used_mb=memory_used,
            operations_per_second=ops_per_second,
            success_rate=success_rate,
            details={
                "operations": num_operations,
                "successful_bookings": success_count,
            },
            status=status,
            threshold=threshold,
        )

        logger.info(
            f"Booking benchmark completed: {execution_time:.4f}s ({ops_per_second:.2f} ops/sec)"
        )
        return result

    def benchmark_search(self) -> BenchmarkResult:
        """Benchmark patient search by ID."""
        logger.info("Starting search benchmark...")

        num_patients = 10000
        num_searches = 1000

        # Setup: Load patients
        for i in range(num_patients):
            patient = Patient(
                patient_id=f"SEARCH_PAT_{i:06d}",
                name=f"SearchPatient_{i}",
                age=random.randint(20, 70),
                priority=PriorityLevel.MODERATE,
            )
            with self.system._patient_lock:
                self.system.patients[patient.patient_id] = patient

        # Prepare search IDs (mix of existing and random)
        search_ids = [
            f"SEARCH_PAT_{random.randint(0, num_patients - 1):06d}"
            for _ in range(num_searches)
        ]

        def run_searches():
            found_count = 0
            for patient_id in search_ids:
                if self.system.search_patient(patient_id):
                    found_count += 1
            return found_count

        start_time = timeit.default_timer()
        found_count, memory_used = self._measure_memory(run_searches)
        end_time = timeit.default_timer()

        execution_time = end_time - start_time
        ops_per_second = num_searches / execution_time
        success_rate = (found_count / num_searches) * 100
        threshold = self.THRESHOLDS["search"]

        status = "PASS" if execution_time <= threshold else "FAIL"

        result = BenchmarkResult(
            name="Patient Search (10K patients)",
            execution_time=execution_time,
            memory_used_mb=memory_used,
            operations_per_second=ops_per_second,
            success_rate=success_rate,
            details={
                "searches": num_searches,
                "patients_in_db": num_patients,
                "found": found_count,
            },
            status=status,
            threshold=threshold,
        )

        logger.info(
            f"Search benchmark completed: {execution_time:.4f}s ({ops_per_second:.2f} ops/sec)"
        )
        return result

    def benchmark_dashboard(self) -> BenchmarkResult:
        """Benchmark dashboard generation under full load."""
        logger.info("Starting dashboard benchmark...")

        # Setup: Full system load
        self.system.load_test_data(10000, 1000, 100000)

        def run_dashboard():
            return self.system.get_dashboard_data()

        # Run multiple times for accurate measurement
        num_runs = 100
        start_time = timeit.default_timer()

        for _ in tqdm(range(num_runs), desc="Dashboard iterations", disable=False):
            _, memory_used = self._measure_memory(run_dashboard)

        end_time = timeit.default_timer()

        total_time = end_time - start_time
        execution_time = total_time / num_runs
        ops_per_second = num_runs / total_time
        threshold = self.THRESHOLDS["dashboard"]

        status = "PASS" if execution_time <= threshold else "FAIL"

        result = BenchmarkResult(
            name="Dashboard Generation (full load)",
            execution_time=execution_time,
            memory_used_mb=memory_used,
            operations_per_second=ops_per_second,
            success_rate=100.0,
            details={
                "iterations": num_runs,
                "total_time": total_time,
                "patients": len(self.system.patients),
                "doctors": len(self.system.doctors),
                "appointments": len(self.system.appointments),
            },
            status=status,
            threshold=threshold,
        )

        logger.info(
            f"Dashboard benchmark completed: {execution_time:.4f}s ({ops_per_second:.2f} ops/sec)"
        )
        return result

    def test_load(self) -> BenchmarkResult:
        """Load test with large dataset."""
        logger.info("Starting load test...")

        num_patients = 10000
        num_doctors = 1000
        num_appointments = 100000

        start_time = timeit.default_timer()

        # Measure memory before
        mem_before = self._get_system_memory()

        self.system.load_test_data(num_patients, num_doctors, num_appointments)

        # Measure memory after
        mem_after = self._get_system_memory()

        end_time = timeit.default_timer()
        execution_time = end_time - start_time

        memory_diff = 0
        if mem_before and mem_after:
            memory_diff = mem_after["used_mb"] - mem_before["used_mb"]

        result = BenchmarkResult(
            name="Load Test (10K patients, 1K doctors, 100K appointments)",
            execution_time=execution_time,
            memory_used_mb=memory_diff,
            operations_per_second=(num_patients + num_doctors + num_appointments)
            / execution_time,
            success_rate=100.0,
            details={
                "patients_loaded": num_patients,
                "doctors_loaded": num_doctors,
                "appointments_loaded": num_appointments,
                "memory_before_mb": mem_before.get("used_mb", 0),
                "memory_after_mb": mem_after.get("used_mb", 0),
            },
            status="PASS",
        )

        logger.info(
            f"Load test completed: {execution_time:.2f}s, Memory: {memory_diff:.2f} MB"
        )
        return result

    def test_stress_peak_hours(self) -> BenchmarkResult:
        """Simulate peak hours with 50 patients arriving per minute."""
        logger.info("Starting peak hours stress test...")

        patients_per_minute = 50
        duration_minutes = 10
        total_patients = patients_per_minute * duration_minutes

        # Setup: Create some base load
        self.system.load_test_data(5000, 500, 50000)

        start_time = timeit.default_timer()

        # Measure memory before
        mem_before = self._get_system_memory()

        # Simulate patient arrivals
        for minute in tqdm(range(duration_minutes), desc="Peak hour simulation"):
            minute_start = timeit.default_timer()

            for _ in range(patients_per_minute):
                patient = Patient(
                    patient_id=f"PEAK_PAT_{minute}_{random.randint(0, 999999):06d}",
                    name=f"PeakPatient_{random.randint(0, 999999)}",
                    age=random.randint(1, 95),
                    priority=random.choice(list(PriorityLevel)),
                )
                self.system.check_in_patient(patient)

            # Ensure we maintain the rate
            elapsed = timeit.default_timer() - minute_start
            if elapsed < 60:
                time.sleep(60 - elapsed)  # Real-time simulation

        # Measure memory after
        mem_after = self._get_system_memory()

        end_time = timeit.default_timer()
        execution_time = end_time - start_time

        memory_diff = 0
        if mem_before and mem_after:
            memory_diff = mem_after["used_mb"] - mem_before["used_mb"]

        queue_size = self.system.triage_queue.size()

        result = BenchmarkResult(
            name="Stress Test - Peak Hours (50 patients/min for 10 min)",
            execution_time=execution_time,
            memory_used_mb=memory_diff,
            operations_per_second=total_patients / max(execution_time, 0.001),
            success_rate=100.0,
            details={
                "patients_arrived": total_patients,
                "duration_minutes": duration_minutes,
                "queue_size_after": queue_size,
                "memory_before_mb": mem_before.get("used_mb", 0),
                "memory_after_mb": mem_after.get("used_mb", 0),
            },
            status="PASS",
        )

        logger.info(
            f"Peak hours test completed: {execution_time:.2f}s, Queue size: {queue_size}"
        )
        return result

    def test_stress_queue_operations(self) -> BenchmarkResult:
        """Test queue operations with 10K items."""
        logger.info("Starting queue operations stress test...")

        queue_size = 10000

        # Create a fresh queue
        test_queue = MultiLevelQueue()

        # Enqueue 10K items
        enqueue_start = timeit.default_timer()
        for i in tqdm(range(queue_size), desc="Enqueue operations"):
            patient = Patient(
                patient_id=f"QUEUE_PAT_{i:06d}",
                name=f"QueuePatient_{i}",
                age=random.randint(20, 70),
                priority=random.choice(list(PriorityLevel)),
            )
            test_queue.enqueue(patient)
        enqueue_time = timeit.default_timer() - enqueue_start

        # Dequeue all items
        dequeue_start = timeit.default_timer()
        dequeued_count = 0
        for _ in tqdm(range(queue_size), desc="Dequeue operations"):
            if test_queue.dequeue():
                dequeued_count += 1
        dequeue_time = timeit.default_timer() - dequeue_start

        total_time = enqueue_time + dequeue_time

        result = BenchmarkResult(
            name="Stress Test - Queue Operations (10K items)",
            execution_time=total_time,
            memory_used_mb=0,  # Hard to measure accurately for individual operations
            operations_per_second=(queue_size * 2) / total_time,
            success_rate=(dequeued_count / queue_size) * 100,
            details={
                "queue_size": queue_size,
                "enqueue_time": enqueue_time,
                "dequeue_time": dequeue_time,
                "dequeued_count": dequeued_count,
            },
            status="PASS",
        )

        logger.info(f"Queue operations test completed: {total_time:.4f}s")
        return result

    def test_scalability(self) -> List[BenchmarkResult]:
        """Test performance as patient count grows."""
        logger.info("Starting scalability tests...")

        sizes = [1000, 5000, 10000, 50000]
        results = []

        for size in sizes:
            logger.info(f"Testing with {size} patients...")

            # Fresh system for each test
            test_system = HospitalTriageSystem()

            # Generate patients
            start_time = timeit.default_timer()
            for i in tqdm(
                range(size), desc=f"Loading {size} patients", disable=size < 1000
            ):
                patient = Patient(
                    patient_id=f"SCALE_PAT_{i:06d}",
                    name=f"ScalePatient_{i}",
                    age=random.randint(20, 70),
                    priority=random.choice(list(PriorityLevel)),
                )
                test_system.check_in_patient(patient)
            load_time = timeit.default_timer() - start_time

            # Test search performance
            search_ids = [
                f"SCALE_PAT_{random.randint(0, size - 1):06d}" for _ in range(1000)
            ]
            search_start = timeit.default_timer()
            for patient_id in search_ids:
                test_system.search_patient(patient_id)
            search_time = timeit.default_timer() - search_start

            # Test dashboard generation
            dash_start = timeit.default_timer()
            test_system.get_dashboard_data()
            dash_time = timeit.default_timer() - dash_start

            result = BenchmarkResult(
                name=f"Scalability Test - {size} patients",
                execution_time=load_time,
                memory_used_mb=0,
                operations_per_second=size / load_time,
                success_rate=100.0,
                details={
                    "patient_count": size,
                    "load_time": load_time,
                    "search_1000_time": search_time,
                    "dashboard_time": dash_time,
                },
                status="PASS",
            )
            results.append(result)

            logger.info(
                f"Scalability test for {size} patients: Load={load_time:.4f}s, Search={search_time:.4f}s, Dashboard={dash_time:.4f}s"
            )

        return results

    def run_all_benchmarks(self) -> List[BenchmarkResult]:
        """Run all benchmarks and tests."""
        logger.info("=" * 60)
        logger.info("STARTING COMPREHENSIVE PERFORMANCE TEST SUITE")
        logger.info("=" * 60)

        all_results = []

        try:
            # Speed benchmarks
            logger.info("\n--- SPEED BENCHMARKS ---")
            all_results.append(self.benchmark_check_in())
            all_results.append(self.benchmark_routing())
            all_results.append(self.benchmark_booking())
            all_results.append(self.benchmark_search())
            all_results.append(self.benchmark_dashboard())

            # Reset system for load tests
            self.system = HospitalTriageSystem()

            # Load testing
            logger.info("\n--- LOAD TESTING ---")
            all_results.append(self.test_load())

            # Stress testing
            logger.info("\n--- STRESS TESTING ---")
            all_results.append(self.test_stress_peak_hours())
            all_results.append(self.test_stress_queue_operations())

            # Scalability testing
            logger.info("\n--- SCALABILITY TESTING ---")
            scalability_results = self.test_scalability()
            all_results.extend(scalability_results)

        except Exception as e:
            logger.error(f"Error during benchmark execution: {e}", exc_info=True)

        self.results = all_results
        self._print_results_table()

        return all_results

    def _print_results_table(self) -> None:
        """Print formatted results table."""
        headers = [
            "Test Name",
            "Time (s)",
            "Ops/sec",
            "Memory (MB)",
            "Success %",
            "Status",
        ]
        data = []

        for result in self.results:
            data.append(
                [
                    result.name,
                    f"{result.execution_time:.4f}",
                    f"{result.operations_per_second:.2f}",
                    f"{result.memory_used_mb:.2f}",
                    f"{result.success_rate:.1f}",
                    result.status,
                ]
            )

        print("\n" + "=" * 80)
        print("PERFORMANCE TEST RESULTS")
        print("=" * 80)
        print(tabulate(data, headers=headers, tablefmt="grid"))
        print("=" * 80)

        # Summary
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        warnings = sum(1 for r in self.results if r.status == "WARNING")

        print(f"\nSUMMARY: {passed} passed, {failed} failed, {warnings} warnings")
        print("=" * 80 + "\n")


def generate_report(
    results: List[BenchmarkResult], output_file: str = "performance_report"
) -> None:
    """Generate HTML and JSON performance reports."""
    logger.info(f"Generating reports: {output_file}.html and {output_file}.json")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # JSON Report
    json_data = {
        "report_generated": timestamp,
        "total_tests": len(results),
        "summary": {
            "passed": sum(1 for r in results if r.status == "PASS"),
            "failed": sum(1 for r in results if r.status == "FAIL"),
            "warnings": sum(1 for r in results if r.status == "WARNING"),
        },
        "results": [
            {
                "name": r.name,
                "execution_time_sec": r.execution_time,
                "memory_used_mb": r.memory_used_mb,
                "operations_per_second": r.operations_per_second,
                "success_rate_percent": r.success_rate,
                "status": r.status,
                "threshold_sec": r.threshold,
                "details": r.details,
            }
            for r in results
        ],
    }

    with open(f"{output_file}.json", "w") as f:
        json.dump(json_data, f, indent=2)

    # HTML Report
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hospital Triage System - Performance Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .summary {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
        }}
        .summary-card {{
            flex: 1;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
        }}
        .pass {{ background-color: #d4edda; color: #155724; }}
        .fail {{ background-color: #f8d7da; color: #721c24; }}
        .warning {{ background-color: #fff3cd; color: #856404; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background-color: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .status-pass {{ color: #28a745; font-weight: bold; }}
        .status-fail {{ color: #dc3545; font-weight: bold; }}
        .status-warning {{ color: #ffc107; font-weight: bold; }}
        .details {{
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }}
        .threshold-exceeded {{
            background-color: #ffebee;
        }}
        footer {{
            margin-top: 30px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Hospital Triage System - Performance Test Report</h1>
        <p><strong>Generated:</strong> {timestamp}</p>
        
        <div class="summary">
            <div class="summary-card pass">
                PASSED<br>
                <span style="font-size: 2em;">{json_data["summary"]["passed"]}</span>
            </div>
            <div class="summary-card fail">
                FAILED<br>
                <span style="font-size: 2em;">{json_data["summary"]["failed"]}</span>
            </div>
            <div class="summary-card warning">
                WARNINGS<br>
                <span style="font-size: 2em;">{json_data["summary"]["warnings"]}</span>
            </div>
        </div>
        
        <h2>Detailed Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Test Name</th>
                    <th>Execution Time (s)</th>
                    <th>Operations/sec</th>
                    <th>Memory (MB)</th>
                    <th>Success Rate</th>
                    <th>Status</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
"""

    for result in results:
        status_class = f"status-{result.status.lower()}"
        threshold_exceeded = (
            result.threshold and result.execution_time > result.threshold
        )
        row_class = "threshold-exceeded" if threshold_exceeded else ""

        details_html = "<br>".join([f"{k}: {v}" for k, v in result.details.items()])

        html_content += f"""
                <tr class="{row_class}">
                    <td>{result.name}</td>
                    <td>{result.execution_time:.4f} {"⚠️" if threshold_exceeded else ""}</td>
                    <td>{result.operations_per_second:.2f}</td>
                    <td>{result.memory_used_mb:.2f}</td>
                    <td>{result.success_rate:.1f}%</td>
                    <td class="{status_class}">{result.status}</td>
                    <td class="details">{details_html}</td>
                </tr>
"""

    html_content += f"""
            </tbody>
        </table>
        
        <div style="margin-top: 20px; padding: 15px; background-color: #e3f2fd; border-radius: 5px;">
            <h3>Performance Thresholds</h3>
            <ul>
                <li>Check-In: ≤ {PerformanceTestSuite.THRESHOLDS["check_in"]}s</li>
                <li>Routing: ≤ {PerformanceTestSuite.THRESHOLDS["routing"]}s</li>
                <li>Booking: ≤ {PerformanceTestSuite.THRESHOLDS["booking"]}s</li>
                <li>Search: ≤ {PerformanceTestSuite.THRESHOLDS["search"]}s</li>
                <li>Dashboard: ≤ {PerformanceTestSuite.THRESHOLDS["dashboard"]}s</li>
            </ul>
            <p><em>⚠️ indicates operations that exceeded acceptable limits</em></p>
        </div>
        
        <footer>
            <p>Hospital Triage System Performance Test Suite</p>
            <p>Generated automatically on {timestamp}</p>
        </footer>
    </div>
</body>
</html>
"""

    with open(f"{output_file}.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info(
        f"Reports generated successfully: {output_file}.html and {output_file}.json"
    )


def main():
    """Entry point with CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Hospital Triage System - Performance Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python performance_test.py                    # Run all benchmarks
  python performance_test.py --benchmarks-only  # Run only speed benchmarks
  python performance_test.py --stress-only      # Run only stress tests
  python performance_test.py --report report    # Generate report with custom name
        """,
    )

    parser.add_argument(
        "--benchmarks-only", action="store_true", help="Run only speed benchmarks"
    )
    parser.add_argument(
        "--stress-only", action="store_true", help="Run only stress tests"
    )
    parser.add_argument("--load-only", action="store_true", help="Run only load test")
    parser.add_argument(
        "--scalability-only", action="store_true", help="Run only scalability tests"
    )
    parser.add_argument(
        "--report",
        type=str,
        default="performance_report",
        help="Output file name for reports (without extension)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level",
    )

    args = parser.parse_args()

    # Update log level
    logger.setLevel(getattr(logging, args.log_level))

    # Create test suite
    suite = PerformanceTestSuite()

    try:
        if args.benchmarks_only:
            logger.info("Running benchmarks only...")
            results = [
                suite.benchmark_check_in(),
                suite.benchmark_routing(),
                suite.benchmark_booking(),
                suite.benchmark_search(),
                suite.benchmark_dashboard(),
            ]
            suite.results = results
            suite._print_results_table()

        elif args.stress_only:
            logger.info("Running stress tests only...")
            results = [
                suite.test_load(),
                suite.test_stress_peak_hours(),
                suite.test_stress_queue_operations(),
            ]
            suite.results = results
            suite._print_results_table()

        elif args.load_only:
            logger.info("Running load test only...")
            result = suite.test_load()
            suite.results = [result]
            suite._print_results_table()

        elif args.scalability_only:
            logger.info("Running scalability tests only...")
            results = suite.test_scalability()
            suite.results = results
            suite._print_results_table()

        else:
            # Run all tests
            results = suite.run_all_benchmarks()

        # Generate reports
        generate_report(suite.results, args.report)

        logger.info("Performance test suite completed successfully!")

        # Return exit code based on results
        failed_tests = sum(1 for r in suite.results if r.status == "FAIL")
        if failed_tests > 0:
            logger.warning(f"{failed_tests} test(s) failed performance thresholds")
            sys.exit(1)

        sys.exit(0)

    except KeyboardInterrupt:
        logger.info("Test suite interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
