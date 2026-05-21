#!/usr/bin/env python3
"""Batch update templates to use i18n translation keys."""

import os
import re

# Mapping of common English text to translation keys
TRANSLATION_MAP = {
    # Navigation
    "Dashboard": "{{ t('nav_dashboard') }}",
    "Patients": "{{ t('nav_patients') }}",
    "Doctors": "{{ t('nav_doctors') }}",
    "Departments": "{{ t('nav_departments') }}",
    "Appointments": "{{ t('nav_appointments') }}",
    "Check-In": "{{ t('nav_checkin') }}",
    "Examination": "{{ t('nav_examination') }}",
    "Billing": "{{ t('nav_billing') }}",
    "Reports": "{{ t('nav_reports') }}",
    # Dashboard specific
    "Department Status": "{{ t('dept_status') }}",
    "Department Overview": "{{ t('dept_overview') }}",
    "Current": "{{ t('dept_current') }}",
    "Waiting": "{{ t('dept_waiting') }}",
    "In Progress": "{{ t('dept_in_progress') }}",
    "Utilization": "{{ t('dept_utilization') }}",
    "Available Doctors": "{{ t('dept_available_doctors') }}",
    "Queue Length": "{{ t('dept_queue_length') }}",
    "Status": "{{ t('dept_status') }}",
    # Patients
    "Patient Management": "{{ t('patients_title') }}",
    "Patient List": "{{ t('patients_list') }}",
    "Add Patient": "{{ t('patients_add') }}",
    "Edit Patient": "{{ t('patients_edit') }}",
    "Delete Patient": "{{ t('patients_delete') }}",
    "Search patients...": "{{ t('patients_search') }}",
    "Name": "{{ t('patients_name') }}",
    "Age": "{{ t('patients_age') }}",
    "Gender": "{{ t('patients_gender') }}",
    "Phone": "{{ t('patients_phone') }}",
    "Email": "{{ t('patients_email') }}",
    "Address": "{{ t('patients_address') }}",
    "Symptoms": "{{ t('patients_symptoms') }}",
    "Priority": "{{ t('patients_priority') }}",
    "Actions": "{{ t('table_actions') }}",
    # Doctors
    "Doctor Management": "{{ t('doctors_title') }}",
    "Doctor List": "{{ t('doctors_list') }}",
    "Add Doctor": "{{ t('doctors_add') }}",
    "Edit Doctor": "{{ t('doctors_edit') }}",
    "Specialty": "{{ t('doctors_specialty') }}",
    "Department": "{{ t('doctors_department') }}",
    "Years Experience": "{{ t('doctors_experience') }}",
    "Current Patient": "{{ t('doctors_current_patient') }}",
    "Queue": "{{ t('doctors_queue') }}",
    # Appointments
    "Appointment Management": "{{ t('appointments_title') }}",
    "Appointment List": "{{ t('appointments_list') }}",
    "Book Appointment": "{{ t('appointments_add') }}",
    "Patient": "{{ t('appointments_patient') }}",
    "Doctor": "{{ t('appointments_doctor') }}",
    "Date": "{{ t('appointments_date') }}",
    "Time": "{{ t('appointments_time') }}",
    "Notes": "{{ t('appointments_notes') }}",
    # Check-In
    "Patient Check-In": "{{ t('checkin_title') }}",
    "Select Patient": "{{ t('checkin_select_patient') }}",
    "Select Department": "{{ t('checkin_select_dept') }}",
    "Critical": "{{ t('checkin_critical') }}",
    "Urgent": "{{ t('checkin_urgent') }}",
    "Normal": "{{ t('checkin_normal') }}",
    "Low": "{{ t('checkin_low') }}",
    "Additional Notes": "{{ t('checkin_notes') }}",
    "Check-In Patient": "{{ t('checkin_button') }}",
    "Recent Check-Ins": "{{ t('checkin_recent') }}",
    # Examination
    "Doctor Examination": "{{ t('examination_title') }}",
    "Select Doctor": "{{ t('examination_select_doctor') }}",
    "Next Patient": "{{ t('examination_next') }}",
    "Start Examination": "{{ t('examination_start') }}",
    "Complete Examination": "{{ t('examination_complete') }}",
    "Patient Queue": "{{ t('examination_queue') }}",
    "Examination Notes": "{{ t('examination_notes') }}",
    "Diagnosis": "{{ t('examination_diagnosis') }}",
    "Treatment Plan": "{{ t('examination_treatment') }}",
    # Billing
    "Billing & Payments": "{{ t('billing_title') }}",
    "Bill List": "{{ t('billing_list') }}",
    "Create Bill": "{{ t('billing_create') }}",
    "Amount": "{{ t('billing_amount') }}",
    "Payment Status": "{{ t('billing_status') }}",
    "Paid": "{{ t('billing_paid') }}",
    "Unpaid": "{{ t('billing_unpaid') }}",
    "Bill Items": "{{ t('billing_items') }}",
    "Total": "{{ t('billing_total') }}",
    "Add Item": "{{ t('billing_add_item') }}",
    "Service": "{{ t('billing_service') }}",
    "Price": "{{ t('billing_price') }}",
    "Process Payment": "{{ t('billing_pay') }}",
    # Reports
    "Reports & Analytics": "{{ t('reports_title') }}",
    "Daily Report": "{{ t('reports_daily') }}",
    "Weekly Report": "{{ t('reports_weekly') }}",
    "Monthly Report": "{{ t('reports_monthly') }}",
    "Department Report": "{{ t('reports_department') }}",
    "Revenue Report": "{{ t('reports_revenue') }}",
    "Patient Statistics": "{{ t('reports_patients') }}",
    "Export Report": "{{ t('reports_export') }}",
    "From Date": "{{ t('reports_from') }}",
    "To Date": "{{ t('reports_to') }}",
    "Generate Report": "{{ t('reports_generate') }}",
    "Summary": "{{ t('reports_summary') }}",
    # Common
    "Save": "{{ t('common_save') }}",
    "Cancel": "{{ t('common_cancel') }}",
    "Delete": "{{ t('common_delete') }}",
    "Edit": "{{ t('common_edit') }}",
    "View": "{{ t('common_view') }}",
    "Search": "{{ t('common_search') }}",
    "Filter": "{{ t('common_filter') }}",
    "Export": "{{ t('common_export') }}",
    "Submit": "{{ t('common_submit') }}",
    "Close": "{{ t('common_close') }}",
    "Back": "{{ t('common_back') }}",
    "Next": "{{ t('common_next') }}",
    "Previous": "{{ t('common_previous') }}",
    "Confirm": "{{ t('common_confirm') }}",
    "Yes": "{{ t('common_yes') }}",
    "No": "{{ t('common_no') }}",
    "Loading...": "{{ t('common_loading') }}",
    "Refresh": "{{ t('common_refresh') }}",
    "Settings": "{{ t('common_settings') }}",
    "Logout": "{{ t('common_logout') }}",
    "Login": "{{ t('common_login') }}",
    "Welcome": "{{ t('common_welcome') }}",
    "Today": "{{ t('common_today') }}",
    "All": "{{ t('common_all') }}",
    "None": "{{ t('common_none') }}",
    "Select": "{{ t('common_select') }}",
    "Optional": "{{ t('common_optional') }}",
    "Required": "{{ t('common_required') }}",
    "Success": "{{ t('common_success') }}",
    "Error": "{{ t('common_error') }}",
    "Warning": "{{ t('common_warning') }}",
    "Info": "{{ t('common_info') }}",
    # Table
    "ID": "{{ t('table_id') }}",
    "Details": "{{ t('table_details') }}",
    "Created": "{{ t('table_created') }}",
    "Updated": "{{ t('table_updated') }}",
    # Gender
    "Male": "{{ t('gender_male') }}",
    "Female": "{{ t('gender_female') }}",
    "Other": "{{ t('gender_other') }}",
}


def update_template(filepath):
    """Update a single template file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # Replace exact matches in HTML text (between tags or in attributes)
    for text, replacement in TRANSLATION_MAP.items():
        # Match text that's not inside {{ }} or {% %} or <script> tags
        # Pattern: text between > and < (HTML content)
        pattern = f">([^<]*?{re.escape(text)}[^<]*?)<"

        def replacer(match):
            inner = match.group(1)
            # Only replace if it's plain text (not already a Jinja expression)
            if "{{" not in inner and "{%" not in inner:
                new_inner = inner.replace(text, replacement)
                return ">" + new_inner + "<"
            return match.group(0)

        content = re.sub(pattern, replacer, content)

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated: {filepath}")
    else:
        print(f"No changes: {filepath}")


def update_all_templates():
    """Update all template files."""
    templates_dir = "templates"

    if not os.path.exists(templates_dir):
        print(f"Directory not found: {templates_dir}")
        return

    for filename in os.listdir(templates_dir):
        if filename.endswith(".html"):
            filepath = os.path.join(templates_dir, filename)
            update_template(filepath)


if __name__ == "__main__":
    update_all_templates()
    print("\nTemplate update complete!")
