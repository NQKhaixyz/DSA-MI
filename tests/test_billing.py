import pytest
from datetime import datetime
from billing_system import Bill, BillingSystem


class TestBillCreation:
    def test_bill_creation(self):
        bill = Bill("BILL000001", "P001", "D001", "DEPT01")
        assert bill.bill_id == "BILL000001"
        assert bill.patient_id == "P001"
        assert bill.doctor_id == "D001"
        assert bill.department_id == "DEPT01"
        assert bill.total_amount == 0.0
        assert bill.is_paid is False
        assert len(bill.items) == 0

    def test_bill_add_item(self):
        bill = Bill("BILL000001", "P001", "D001", "DEPT01")
        bill.add_item("consultation", 200000)
        assert len(bill.items) == 1
        assert bill.items[0] == ("consultation", 200000)
        assert bill.total_amount == 200000

    def test_bill_add_multiple_items(self):
        bill = Bill("BILL000001", "P001", "D001", "DEPT01")
        bill.add_item("consultation", 200000)
        bill.add_item("blood_test", 150000)
        assert len(bill.items) == 2
        assert bill.total_amount == 350000

    def test_bill_calculate_total(self):
        bill = Bill("BILL000001", "P001", "D001", "DEPT01")
        bill.add_item("xray", 300000)
        bill.add_item("prescription", 50000)
        total = bill.calculate_total()
        assert total == 350000
        assert bill.total_amount == 350000

    def test_bill_mark_paid(self):
        bill = Bill("BILL000001", "P001", "D001", "DEPT01")
        bill.mark_paid()
        assert bill.is_paid is True

    def test_bill_repr(self):
        bill = Bill("BILL000001", "P001", "D001", "DEPT01")
        repr_str = repr(bill)
        assert "BILL000001" in repr_str
        assert "P001" in repr_str
        assert "0.0" in repr_str
        assert "False" in repr_str


class TestBillingSystemServiceCatalog:
    def test_default_services_exist(self):
        bs = BillingSystem()
        expected = [
            "consultation",
            "emergency_care",
            "blood_test",
            "xray",
            "ultrasound",
            "surgery",
            "prescription",
        ]
        for service in expected:
            assert service in bs.service_catalog

    def test_service_costs(self):
        bs = BillingSystem()
        assert bs.service_catalog["consultation"] == 200000.0
        assert bs.service_catalog["emergency_care"] == 500000.0
        assert bs.service_catalog["blood_test"] == 150000.0
        assert bs.service_catalog["xray"] == 300000.0
        assert bs.service_catalog["surgery"] == 2000000.0

    def test_add_service_to_catalog(self):
        bs = BillingSystem()
        bs.add_service_to_catalog("mri_scan", 800000)
        assert "mri_scan" in bs.service_catalog
        assert bs.service_catalog["mri_scan"] == 800000


class TestCreateBill:
    def test_create_bill_basic(self):
        bs = BillingSystem()
        bill = bs.create_bill("P001", "D001", "DEPT01")
        assert bill.bill_id in bs.bills
        assert bill.patient_id == "P001"
        assert bill.total_amount == 0.0

    def test_create_bill_with_services(self):
        bs = BillingSystem()
        bill = bs.create_bill("P001", "D001", "DEPT01", ["consultation", "blood_test"])
        assert bill.total_amount == 350000
        assert len(bill.items) == 2

    def test_create_bill_tracks_patient(self):
        bs = BillingSystem()
        bs.create_bill("P001", "D001", "DEPT01")
        assert "P001" in bs.patient_bills
        assert len(bs.patient_bills["P001"]) == 1

    def test_create_bill_multiple_for_patient(self):
        bs = BillingSystem()
        bs.create_bill("P001", "D001", "DEPT01")
        bs.create_bill("P001", "D002", "DEPT02")
        assert len(bs.patient_bills["P001"]) == 2

    def test_bill_id_generation(self):
        bs = BillingSystem()
        bill1 = bs.create_bill("P001", "D001", "DEPT01")
        bill2 = bs.create_bill("P002", "D001", "DEPT01")
        assert bill1.bill_id == "BILL000001"
        assert bill2.bill_id == "BILL000002"


class TestAddServiceToBill:
    def test_add_service_success(self):
        bs = BillingSystem()
        bill = bs.create_bill("P001", "D001", "DEPT01")
        result = bs.add_service_to_bill(bill.bill_id, "xray")
        assert result is True
        assert bill.total_amount == 300000

    def test_add_invalid_bill(self):
        bs = BillingSystem()
        result = bs.add_service_to_bill("INVALID", "xray")
        assert result is False

    def test_add_invalid_service(self):
        bs = BillingSystem()
        bill = bs.create_bill("P001", "D001", "DEPT01")
        result = bs.add_service_to_bill(bill.bill_id, "invalid_service")
        assert result is False

    def test_add_multiple_services(self):
        bs = BillingSystem()
        bill = bs.create_bill("P001", "D001", "DEPT01")
        bs.add_service_to_bill(bill.bill_id, "consultation")
        bs.add_service_to_bill(bill.bill_id, "prescription")
        assert bill.total_amount == 250000


class TestGetTotalRevenue:
    def test_total_revenue_empty(self):
        bs = BillingSystem()
        assert bs.get_total_revenue() == 0.0

    def test_total_revenue_unpaid(self):
        bs = BillingSystem()
        bs.create_bill("P001", "D001", "DEPT01", ["consultation"])
        assert bs.get_total_revenue() == 0.0

    def test_total_revenue_paid(self):
        bs = BillingSystem()
        bill = bs.create_bill("P001", "D001", "DEPT01", ["consultation", "blood_test"])
        bs.mark_bill_paid(bill.bill_id)
        assert bs.get_total_revenue() == 350000

    def test_total_revenue_multiple_paid(self):
        bs = BillingSystem()
        bill1 = bs.create_bill("P001", "D001", "DEPT01", ["consultation"])
        bill2 = bs.create_bill("P002", "D001", "DEPT01", ["emergency_care"])
        bs.mark_bill_paid(bill1.bill_id)
        bs.mark_bill_paid(bill2.bill_id)
        assert bs.get_total_revenue() == 700000


class TestGetDepartmentRevenue:
    def test_department_revenue_empty(self):
        bs = BillingSystem()
        assert bs.get_department_revenue("DEPT01") == 0.0

    def test_department_revenue_paid(self):
        bs = BillingSystem()
        bill = bs.create_bill("P001", "D001", "DEPT01", ["consultation"])
        bs.mark_bill_paid(bill.bill_id)
        assert bs.get_department_revenue("DEPT01") == 200000

    def test_department_revenue_multiple(self):
        bs = BillingSystem()
        bill1 = bs.create_bill("P001", "D001", "DEPT01", ["consultation"])
        bill2 = bs.create_bill("P002", "D002", "DEPT02", ["xray"])
        bs.mark_bill_paid(bill1.bill_id)
        bs.mark_bill_paid(bill2.bill_id)
        assert bs.get_department_revenue("DEPT01") == 200000
        assert bs.get_department_revenue("DEPT02") == 300000

    def test_department_revenue_unpaid_not_counted(self):
        bs = BillingSystem()
        bs.create_bill("P001", "D001", "DEPT01", ["consultation"])
        assert bs.get_department_revenue("DEPT01") == 0.0


class TestMarkBillPaid:
    def test_mark_bill_paid_success(self):
        bs = BillingSystem()
        bill = bs.create_bill("P001", "D001", "DEPT01")
        result = bs.mark_bill_paid(bill.bill_id)
        assert result is True
        assert bill.is_paid is True

    def test_mark_bill_paid_invalid(self):
        bs = BillingSystem()
        result = bs.mark_bill_paid("INVALID")
        assert result is False

    def test_mark_bill_paid_updates_revenue(self):
        bs = BillingSystem()
        bill = bs.create_bill("P001", "D001", "DEPT01", ["consultation"])
        assert bs.get_total_revenue() == 0.0
        bs.mark_bill_paid(bill.bill_id)
        assert bs.get_total_revenue() == 200000


class TestGetPatientBills:
    def test_get_patient_bills_empty(self):
        bs = BillingSystem()
        assert bs.get_patient_bills("P001") == []

    def test_get_patient_bills(self):
        bs = BillingSystem()
        bs.create_bill("P001", "D001", "DEPT01", ["consultation"])
        bills = bs.get_patient_bills("P001")
        assert len(bills) == 1
        assert bills[0].patient_id == "P001"

    def test_get_patient_bills_multiple(self):
        bs = BillingSystem()
        bs.create_bill("P001", "D001", "DEPT01", ["consultation"])
        bs.create_bill("P001", "D002", "DEPT02", ["xray"])
        bills = bs.get_patient_bills("P001")
        assert len(bills) == 2

    def test_get_nonexistent_patient_bills(self):
        bs = BillingSystem()
        assert bs.get_patient_bills("NONEXISTENT") == []
