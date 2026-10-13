"""
Comprehensive Integration Test for Week 9 Day 4 Tasks 4 & 5:
Channels (Web Chat, Email Confirmations, Follow-up Scheduler)
& Observability (3 Annotated Patient Journey Traces, Tool Calls, Latency, Tokens, Costs).
"""

import os
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Fix Windows console UTF-8 output
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.channels.email_channel import send_appointment_confirmation_email, send_followup_reminder_email
from src.channels.followup_scheduler import FollowUpScheduler
from src.observability.tracer import ClinicalTracer


def test_channels_email_and_reminders():
    print("=" * 70)
    print("TEST 1: CHANNELS — EMAIL CONFIRMATION & SCHEDULED FOLLOW-UPS")
    print("=" * 70)

    # 1. Test live appointment confirmation email
    print("Sending live appointment confirmation email to samiworkspace11@gmail.com...")
    res = send_appointment_confirmation_email(
        patient_name="Samiullah Khan",
        doctor_name="Dr. Haris Nadeem",
        specialty="ENT",
        branch_name="City Care Clinics - Main Gulberg",
        slot_date="2026-10-08",
        slot_time="09:30 AM",
        fee_pkr=3000,
        token_number="CC-108",
        recipient_email="samiworkspace11@gmail.com"
    )
    print("Email Delivery Result:", res)
    assert res.get("status") in ("delivered", "simulated_success", "logged")
    print("✓ Email confirmation verified.")

    # 2. Test Follow-up Scheduler
    scheduler = FollowUpScheduler()
    new_jobs = scheduler.schedule_patient_care_plan(
        patient_id="pat-test-101",
        patient_name="Samiullah Khan",
        doctor_name="Dr. Haris Nadeem",
        recipient_email="samiworkspace11@gmail.com"
    )
    print(f"\nScheduled {len(new_jobs)} follow-up milestones for patient pat-test-101:")
    for j in new_jobs:
        print(f"  - [{j['due_date']}] {j['title']}")

    assert len(new_jobs) == 3
    assert new_jobs[0]["title"] == "Day 1 Medication Adherence Check"
    assert new_jobs[1]["title"] == "Day 3 Recovery & Symptom Check"
    assert new_jobs[2]["title"] == "Day 7 Clinic Follow-Up Checkup"

    # 3. Test Triggering Due Reminders
    dispatched = scheduler.trigger_due_reminders(force_all_pending=True)
    print(f"\nDispatched {len(dispatched)} due reminders via Email & simulated WhatsApp:")
    for d in dispatched:
        print(f"  - Dispatched: {d['title']} -> {d['recipient_email']}")
    assert len(dispatched) >= 1
    scheduler.shutdown()
    print("✓ Follow-up automated reminder scheduler verified.")

    print("\n--> TEST 1 PASSED: Channels (Email Confirmations & Scheduled Reminders) Fully Verified!")


def test_observability_and_annotated_journeys():
    print("\n" + "=" * 70)
    print("TEST 2: OBSERVABILITY — 3 ANNOTATED PATIENT JOURNEY TRACES")
    print("=" * 70)

    tracer = ClinicalTracer()
    journeys = tracer.create_three_annotated_journeys()

    print(f"Generated and persisted {len(journeys)} annotated patient journeys.")
    assert len(journeys) == 3

    for idx, j in enumerate(journeys, 1):
        print(f"\n[{idx}] {j.journey_title}")
        print(f"    Trace ID: {j.trace_id} | Patient: {j.patient_name} ({j.patient_id})")
        print(f"    Total Latency: {j.total_latency_ms} ms | Spans Count: {len(j.spans)}")
        print(f"    Tokens: {j.total_tokens} (Prompt: {j.total_prompt_tokens}, Completion: {j.total_completion_tokens})")
        print(f"    Inference Cost: ${j.total_cost_usd:.6f} USD")
        print(f"    Escalation Triggered: {j.escalation_triggered} | Doctor Override: {j.doctor_override}")
        print(f"    Quality Score: ⭐ {j.quality_score} / 5.0")
        print("    Clinical Annotations:")
        for ann in j.clinical_annotations[:2]:
            print(f"      • {ann}")

        # Check tool calls
        total_tools = sum(len(s.tool_calls) for s in j.spans)
        print(f"    Total Tool Calls Executed: {total_tools}")

    # Specific assertions
    j1 = journeys[0] # Routine
    assert not j1.escalation_triggered
    assert not j1.doctor_override

    j2 = journeys[1] # Emergency
    assert j2.escalation_triggered
    assert j2.escalation_details["urgency_tier"] == "EMERGENCY"
    assert "1122" in j2.escalation_details["protocol"]

    j3 = journeys[2] # Doctor Override
    assert j3.escalation_triggered
    assert j3.doctor_override
    assert j3.doctor_override_details["action"] == "EDITED_AND_AUTHORIZED"
    assert "Klaricid" in str(j3.doctor_override_details["substitute_order"])

    print("\n--> TEST 2 PASSED: Observability & 3 Annotated Journey Traces Fully Verified!")


if __name__ == "__main__":
    print("=" * 70)
    print("STARTING TEST SUITE FOR WEEK 9 DAY 4 TASKS 4 & 5")
    print("=" * 70)
    test_channels_email_and_reminders()
    test_observability_and_annotated_journeys()
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)
