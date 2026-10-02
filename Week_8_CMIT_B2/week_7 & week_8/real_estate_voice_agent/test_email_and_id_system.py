import sys
import json
import sqlite3
sys.stdout.reconfigure(encoding='utf-8')

from memory import ConversationMemory, extract_spoken_email
from appointment_manager import appointment_manager
from email_service import email_service
from app import process_appointment_interaction

print("=" * 60)
print("TEST 1: Urdu & Spoken Email Extraction")
print("=" * 60)
test_inputs = [
    ("Urdu transcript with phonetic email", "میرا نام سمیع ہے اور میرا ای میل سمیع ورک سپیس ون ون جی میل ڈاٹ کام ہے اور میری پرفیکٹ سلوٹ ہے کل شام چار بجے"),
    ("English transcript with spoken email", "my email is sami workspace one one at gmail dot com please book tomorrow 11 am"),
    ("Standard email address", "please confirm to samiworkspace11@gmail.com for tomorrow 11:00 AM"),
]

for label, text in test_inputs:
    extracted = extract_spoken_email(text)
    print(f"[{label}] -> Extracted Email: {extracted}")
    assert extracted == "samiworkspace11@gmail.com", f"Expected samiworkspace11@gmail.com, got {extracted}"

print(">>> TEST 1 PASSED: All email variants successfully extracted as samiworkspace11@gmail.com!\n")

print("=" * 60)
print("TEST 2: Direct Booking, DB Insert, Appointment ID & Live Email Dispatch")
print("=" * 60)
open_slots = appointment_manager.get_available_slots("Tomorrow")
slot_to_book = open_slots[0]
reschedule_slot = open_slots[1] if len(open_slots) > 1 else "05:00 PM"
print(f"Available slots for Tomorrow: {open_slots}. Testing with: {slot_to_book}")

book_res = appointment_manager.book_appointment(
    session_id="test_automated_verification_session",
    client_name="Sami Test Client",
    client_email="samiworkspace11@gmail.com",
    city="Lahore",
    property_title="Lake City Sector M 10 Marla Luxury Villa",
    appointment_date="Tomorrow",
    appointment_time=slot_to_book,
    notes="Automated verification of Appointment ID and Add to Calendar button."
)

print("Booking Result:", json.dumps({k: v for k, v in book_res.items() if k != "email_result"}, indent=2))
app_id = book_res["appointment_id"]
assert book_res["success"] is True
assert app_id is not None
assert book_res["email_result"]["success"] is True
print(f">>> TEST 2 PASSED: Appointment #{app_id} booked & live confirmation email sent to samiworkspace11@gmail.com!\n")

print("=" * 60)
print("TEST 3: Repeat Caller Reschedule using Appointment ID")
print("=" * 60)
resched_res = appointment_manager.reschedule_appointment(
    appointment_id=app_id,
    new_date="Tomorrow",
    new_time=reschedule_slot
)
print("Reschedule Result:", json.dumps({k: v for k, v in resched_res.items() if k != "email_result"}, indent=2))
assert resched_res["success"] is True
assert resched_res["status"] == "RESCHEDULED"
assert resched_res["email_result"]["success"] is True
print(f">>> TEST 3 PASSED: Appointment #{app_id} rescheduled to {reschedule_slot} & live update email sent!\n")

print("=" * 60)
print("TEST 4: Repeat Caller Cancellation using Appointment ID")
print("=" * 60)
cancel_res = appointment_manager.cancel_appointment(appointment_id=app_id)
print("Cancel Result:", json.dumps({k: v for k, v in cancel_res.items() if k != "email_result"}, indent=2))
assert cancel_res["success"] is True
assert cancel_res["status"] == "CANCELLED"
assert cancel_res["email_result"]["success"] is True
print(f">>> TEST 4 PASSED: Appointment #{app_id} cancelled & live cancellation email sent!\n")

print("=" * 60)
print("TEST 5: End-to-End Controller Conversation with Appointment ID")
print("=" * 60)
mem = ConversationMemory("test_convo_session_e2e")
mem.update_context_from_user_input("Mujhe appointment cancel karni hai")
flow1 = process_appointment_interaction("test_convo_session_e2e", mem, "Mujhe appointment cancel karni hai")
print("[Agent Prompt when ID is missing]:\n", flow1["context_banner"].strip())
assert "APPOINTMENT ID REQUIRED" in flow1["context_banner"]

# User provides the ID
mem.update_context_from_user_input(f"Mera appointment ID {app_id} hai")
flow2 = process_appointment_interaction("test_convo_session_e2e", mem, f"Mera appointment ID {app_id} hai")
print("[Agent Action when ID is provided]:\n", flow2["context_banner"].strip())
assert f"APPOINTMENT CANCELLED (ID #{app_id})" in flow2["context_banner"]
print(">>> TEST 5 PASSED: ID-based repeat caller conversation logic verified!\n")

print("=" * 60)
print("ALL AUTOMATED TESTS PASSED SUCCESSFULLY!")
print("=" * 60)
