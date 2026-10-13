"""
Comprehensive Test Harness for MCP Servers.
Tests each of the 4 MCP servers independently:
1. patient-records
2. scheduling
3. drug-database
4. notifications
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.mcp_servers.patient_records_server import (
    get_patient_profile,
    get_patient_allergies,
    get_active_medications,
    get_lab_history
)
from src.mcp_servers.scheduling_server import (
    find_doctors,
    get_available_slots,
    book_appointment,
    reschedule_appointment,
    cancel_appointment
)
from src.mcp_servers.drug_database_server import (
    lookup_drug,
    check_drug_interactions,
    check_max_dose,
    check_allergy_contraindication
)
from src.mcp_servers.notifications_server import (
    send_email,
    send_appointment_confirmation,
    send_prescription_safety_alert,
    send_whatsapp,
    send_sms
)
from src.database.connection import db_session
from src.database.models import Patient, Practitioner, Appointment


def test_patient_records():
    print("\n" + "="*60)
    print("TEST 1: patient-records MCP Server")
    print("="*60)

    session = db_session()
    # Find a patient with known conditions/allergies
    sample_patient = session.query(Patient).first()
    session.close()

    assert sample_patient is not None, "No patients found in DB!"
    p_id = sample_patient.id
    print(f"Testing with sample patient ID: {p_id} ({sample_patient.full_name})")

    # 1. Profile
    profile = get_patient_profile(p_id)
    print(f"[get_patient_profile] Status: {profile.get('status')}, Name: {profile.get('full_name')}, Conditions: {profile.get('conditions_count')}")
    assert profile.get("status") == "success"

    # 2. Allergies
    allergies = get_patient_allergies(p_id)
    print(f"[get_patient_allergies] Status: {allergies.get('status')}, Allergies: {allergies.get('allergies_count')}")
    assert allergies.get("status") == "success"

    # 3. Medications
    meds = get_active_medications(p_id)
    print(f"[get_active_medications] Status: {meds.get('status')}, Meds count: {meds.get('medications_count')}")
    assert meds.get("status") == "success"

    # 4. Labs
    labs = get_lab_history(p_id, limit=3)
    print(f"[get_lab_history] Status: {labs.get('status')}, Observations: {labs.get('observations_count')}")
    assert labs.get("status") == "success"

    print("--> patient-records MCP Server: PASSED ALL TESTS")


def test_scheduling():
    print("\n" + "="*60)
    print("TEST 2: scheduling MCP Server")
    print("="*60)

    # 1. find_doctors
    doc_res = find_doctors(specialty="Cardiology", city="Lahore")
    print(f"[find_doctors] Found: {doc_res.get('matches_found')} cardiologists in Lahore")
    assert doc_res.get("status") == "success"
    assert doc_res.get("matches_found") > 0
    doctor = doc_res["doctors"][0]
    doctor_id = doctor["doctor_id"]
    print(f"Selected Doctor: {doctor['name']} ({doctor['branch_name']})")

    # 2. get_available_slots (Pick next Monday)
    test_date = "2026-10-12" # A Monday
    slots_res = get_available_slots(doctor_id, test_date)
    print(f"[get_available_slots] Date: {test_date}, Free slots: {slots_res.get('available_slots_count')}")
    assert slots_res.get("status") == "success"
    available_slots = slots_res.get("available_slots", [])

    if not available_slots:
        # Try Tuesday
        test_date = "2026-10-13"
        slots_res = get_available_slots(doctor_id, test_date)
        available_slots = slots_res.get("available_slots", [])

    chosen_slot = available_slots[0] if available_slots else "10:00"
    print(f"Choosing slot: {chosen_slot}")

    # 3. book_appointment
    session = db_session()
    sample_patient = session.query(Patient).first()
    session.close()

    book_res = book_appointment(
        patient_id=sample_patient.id,
        doctor_id=doctor_id,
        date_str=test_date,
        slot_time=chosen_slot,
        chief_complaint="Chest tightness during exertion",
        urgency_tier="URGENT"
    )
    print(f"[book_appointment] Status: {book_res.get('status')}, Token: {book_res.get('token_number')}, GCal: {book_res.get('google_calendar_sync', {}).get('status')}")
    assert book_res.get("status") == "success"
    appt_id = book_res.get("appointment_id")

    # 4. reschedule_appointment
    next_slot = available_slots[1] if len(available_slots) > 1 else "10:15"
    resched_res = reschedule_appointment(
        appointment_id=appt_id,
        new_date_str=test_date,
        new_slot_time=next_slot
    )
    print(f"[reschedule_appointment] Status: {resched_res.get('status')}, New time: {resched_res.get('new_slot_time')}")
    assert resched_res.get("status") == "success"

    # 5. cancel_appointment
    cancel_res = cancel_appointment(
        appointment_id=appt_id,
        cancellation_reason="Testing MCP cancellation endpoint"
    )
    print(f"[cancel_appointment] Status: {cancel_res.get('status')}, Cancellation reason: {cancel_res.get('cancellation_reason')}")
    assert cancel_res.get("status") == "success"

    print("--> scheduling MCP Server: PASSED ALL TESTS")


def test_drug_database():
    print("\n" + "="*60)
    print("TEST 3: drug-database MCP Server")
    print("="*60)

    # 1. lookup_drug
    lookup = lookup_drug("Augmentin")
    print(f"[lookup_drug] 'Augmentin': Found {lookup.get('match_count')} forms. Generic: {lookup['results'][0]['generic']}")
    assert lookup.get("status") == "success"
    assert lookup.get("match_count") > 0

    # 2. check_drug_interactions (Aspirin + Plavix)
    interactions = check_drug_interactions(["Loprin", "Plavix", "Panadol"])
    print(f"[check_drug_interactions] Has interactions: {interactions.get('has_interactions')}, Found: {interactions.get('interactions_count')}")
    assert interactions.get("status") == "success"
    assert interactions.get("has_interactions") is True
    print(f"Detected: {interactions['interactions'][0]['severity']} - {interactions['interactions'][0]['clinical_effect']}")

    # 3. check_max_dose
    # Panadol: safe 2000mg vs unsafe 5000mg
    safe_dose = check_max_dose("Panadol", 2000)
    print(f"[check_max_dose] Panadol 2000mg safe? {safe_dose.get('is_safe')} ({safe_dose.get('percentage_of_max_dose')})")
    assert safe_dose.get("is_safe") is True

    unsafe_dose = check_max_dose("Panadol", 5000)
    print(f"[check_max_dose] Panadol 5000mg safe? {unsafe_dose.get('is_safe')} (Alert: {unsafe_dose.get('alert')})")
    assert unsafe_dose.get("is_safe") is False

    # 4. check_allergy_contraindication
    penicillin_check = check_allergy_contraindication("Augmentin", ["Penicillin Allergy", "Dust"])
    print(f"[check_allergy_contraindication] Augmentin with Penicillin allergy safe? {penicillin_check.get('is_safe')}")
    assert penicillin_check.get("is_safe") is False
    print(f"Contraindication: {penicillin_check['contraindications'][0]['risk']}")

    safe_check = check_allergy_contraindication("Panadol", ["Penicillin Allergy"])
    print(f"[check_allergy_contraindication] Panadol with Penicillin allergy safe? {safe_check.get('is_safe')}")
    assert safe_check.get("is_safe") is True

    print("--> drug-database MCP Server: PASSED ALL TESTS")


def test_notifications():
    print("\n" + "="*60)
    print("TEST 4: notifications MCP Server")
    print("="*60)

    target_email = "samiworkspace11@gmail.com"

    # 1. send_email
    email_res = send_email(
        subject="City Care Clinics Test Notification",
        body_text="Assalam-o-Alaikum, this is an automated test from City Care Clinics MCP Server.",
        to_email=target_email
    )
    print(f"[send_email] Status: {email_res.get('status')}, Mode: {email_res.get('mode')}, To: {email_res.get('recipient')}")
    assert email_res.get("status") in ("delivered", "simulated_success")

    # 2. send_appointment_confirmation
    conf_res = send_appointment_confirmation(
        patient_name="Sami Test",
        doctor_name="Dr. Farhan Tariq",
        specialty="Cardiology",
        clinic_branch="City Care Clinics - Main Gulberg",
        appointment_date="2026-10-15",
        slot_time="10:30",
        token_number="CC-1015-TEST",
        to_email=target_email
    )
    print(f"[send_appointment_confirmation] Status: {conf_res.get('status')}, To: {conf_res.get('recipient')}")
    assert conf_res.get("status") in ("delivered", "simulated_success")

    # 3. send_prescription_safety_alert
    alert_res = send_prescription_safety_alert(
        patient_name="Sami Test",
        doctor_name="Dr. Farhan Tariq",
        alert_type="DRUG_ALLERGY_CONTRAINDICATION",
        alert_details="Augmentin prescribed to patient with confirmed Penicillin allergy.",
        to_email=target_email
    )
    print(f"[send_prescription_safety_alert] Status: {alert_res.get('status')}")
    assert alert_res.get("status") in ("delivered", "simulated_success")

    # 4. send_whatsapp
    wa_res = send_whatsapp(
        phone_number="+92-300-1234567",
        message="Aap ka City Care Clinics appointment token: CC-1015-TEST hai."
    )
    print(f"[send_whatsapp] Status: {wa_res.get('status')}, Recipient: {wa_res.get('recipient')}")
    assert wa_res.get("status") == "success"

    # 5. send_sms
    sms_res = send_sms(
        phone_number="+92-300-1234567",
        message="City Care Clinics: Reminder appointment on 15 Oct at 10:30."
    )
    print(f"[send_sms] Status: {sms_res.get('status')}, Characters: {sms_res.get('characters_count')}")
    assert sms_res.get("status") == "success"

    print("--> notifications MCP Server: PASSED ALL TESTS")


if __name__ == "__main__":
    print("="*60)
    print("STARTING INDEPENDENT TEST OF ALL 4 MCP SERVERS")
    print("="*60)
    test_patient_records()
    test_scheduling()
    test_drug_database()
    test_notifications()
    print("\n" + "="*60)
    print("ALL 4 MCP SERVERS TESTED AND VERIFIED SUCCESSFULLY!")
    print("="*60)
