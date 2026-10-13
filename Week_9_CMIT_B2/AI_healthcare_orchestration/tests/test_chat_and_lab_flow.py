import os
import sys
import io
from pathlib import Path

# Force UTF-8 stdout on Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import requests
import json
import time
from fastapi.testclient import TestClient

from src.server.app import app

client = TestClient(app)

def test_full_patient_journey():
    print("=== TEST 1: Endpoints & Pages ===")
    r = client.get("/")
    assert r.status_code == 200
    print("[PASS] Index page loaded")

    r = client.get("/chat")
    assert r.status_code == 200
    assert "City Care AI Assistant" in r.text
    print("[PASS] Dedicated Chat Consultation page loaded")

    print("\n=== TEST 2: Patient Intake & Demographics Gathering ===")
    sess_id = f"test-sess-{int(time.time())}"

    # Turn 1: Who it is for (Family member)
    r = client.post("/api/chat/message", json={"session_id": sess_id, "message": "ghar k fard k liyay"})
    d = r.json()
    print("Turn 1 Bot:", d.get("message"))
    assert any(w in d.get("message").lower() for w in ["naam", "name"]), "Must ask for patient name!"

    # Turn 2: Patient Name
    r = client.post("/api/chat/message", json={"session_id": sess_id, "message": "Ali Raza Khan"})
    d = r.json()
    print("Turn 2 Bot:", d.get("message"))
    assert any(w in d.get("message").lower() for w in ["mobile", "number", "rabtay"]), "Must ask for contact number!"

    # Turn 3: Phone Number
    r = client.post("/api/chat/message", json={"session_id": sess_id, "message": "0300-9876543"})
    d = r.json()
    print("Turn 3 Bot:", d.get("message"))

    # Turn 4: Chief Complaint
    r = client.post("/api/chat/message", json={"session_id": sess_id, "message": "kal se shadeed bukhar hai"})
    d = r.json()
    print("Turn 4 Bot:", d.get("message"))

    # Turn 5: Duration
    r = client.post("/api/chat/message", json={"session_id": sess_id, "message": "2 din se"})
    d = r.json()
    print("Turn 5 Bot:", d.get("message"))

    # Turn 6: Severity scale
    r = client.post("/api/chat/message", json={"session_id": sess_id, "message": "6"})
    d = r.json()
    print("Turn 6 Bot:", d.get("message"))

    # Turn 7: Associated symptoms
    r = client.post("/api/chat/message", json={"session_id": sess_id, "message": "khansi aur galay mein dard"})
    d = r.json()
    print("Turn 7 Bot:", d.get("message"))

    # Turn 8: Allergies
    r = client.post("/api/chat/message", json={"session_id": sess_id, "message": "egg se allergy hai"})
    d = r.json()
    print("Turn 8 Bot:", d.get("message"))

    # Turn 9: Medications
    if d.get("stage") == "INTAKE":
        r = client.post("/api/chat/message", json={"session_id": sess_id, "message": "koi regular dawa nahi"})
        d = r.json()
        print("Turn 9 Bot:", d.get("message"))

    # Turn 10: Chronic conditions / Medical history
    if d.get("stage") == "INTAKE":
        r = client.post("/api/chat/message", json={"session_id": sess_id, "message": "ni koi bimari nahi"})
        d = r.json()
        print("Turn 10 Bot:", d.get("message"))

    # Verify Proposal Stage
    assert d.get("stage") == "AWAITING_CONFIRMATION", f"Expected AWAITING_CONFIRMATION, got {d.get('stage')}"
    assert "confirm" in d.get("message").lower(), "Must prompt for patient confirmation"
    assert "confirmation email dispatched" not in d.get("message").lower(), "Must NOT dispatch email prior to confirmation!"
    print("[PASS] Appointment proposed without premature email dispatch!")

    # Turn 11: Patient Confirms ("g kr dyn")
    print("\n=== TEST 3: Patient Explicit Confirmation ('g kr dyn') ===")
    r = client.post("/api/chat/message", json={"session_id": sess_id, "message": "g kr dyn"})
    d = r.json()
    print("Turn 11 Bot:\n", d.get("message"))
    assert d.get("stage") == "CONFIRMED"
    assert "confirmation email dispatched" in d.get("message").lower()
    token = d.get("token_number")
    assert token and token.startswith("CC-"), f"Expected token CC-xxx, got {token}"
    print(f"[PASS] Confirmed! Single Token generated: {token} and email dispatched.")

    # Turn 12: Subsequent Turn
    print("\n=== TEST 4: Idempotent Subsequent Turns (No Duplicate Emails/Tokens) ===")
    r = client.post("/api/chat/message", json={"session_id": sess_id, "message": "clinic ka address kya hai?"})
    d = r.json()
    print("Turn 12 Bot:\n", d.get("message"))
    assert d.get("stage") == "CONFIRMED"
    assert d.get("token_number") == token
    assert "confirmation email dispatched" not in d.get("message").lower(), "Should NOT send duplicate email on subsequent messages!"
    print("[PASS] Subsequent turns handled gracefully without duplicate tokens or emails.")

    # Test 5: Upload Lab Report Attachment
    print("\n=== TEST 5: Lab Report Attachment Upload & Vision Parsing ===")
    sample_report = Path("data/synthetic_lab_reports/report_01.png")
    assert sample_report.exists(), "Sample report not found"

    with open(sample_report, "rb") as f:
        files = {"file": ("report_01.png", f, "image/png")}
        data = {"session_id": sess_id}
        r = client.post("/api/chat/upload-lab-report", files=files, data=data)

    assert r.status_code == 200, f"Upload failed: {r.text}"
    up_res = r.json()
    print("Upload Result Status:", up_res.get("status"))
    print("Panel:", up_res.get("panel_name"))
    print("Approval ID:", up_res.get("approval_id"))
    print("Extracted Parameters Count:", len(up_res.get("parsed_report", {}).get("parameters", [])))
    print("Chat message preview:\n", up_res.get("chat_message")[:200])

    assert up_res.get("status") == "success"
    assert up_res.get("approval_id") is not None
    assert len(up_res.get("parsed_report", {}).get("parameters", [])) > 0
    print("[PASS] Lab report parsed, structured, and queued for doctor approval!")

if __name__ == "__main__":
    test_full_patient_journey()
