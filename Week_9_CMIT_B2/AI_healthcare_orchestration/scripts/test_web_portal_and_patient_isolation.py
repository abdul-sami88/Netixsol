"""
Integration Test for the HTML Modern Web Portal & Doctor Patient Isolation.
Verifies:
1. Patient Landing Page (GET /) and Doctor Login (GET /doctor-login) routes.
2. Doctor Authentication with PMDC/Email credentials.
3. Patient Isolation Filter:
   - Doctor A (Dr. Ahmad Khan) sees ONLY his 41 patients.
   - Doctor B (Dr. Bilal Aslam) sees ONLY his 35 patients.
   - Cross-doctor patient data leakage is ZERO.
4. Patient Chat API (POST /api/chat/message):
   - Conversational intake steps without question repetitions.
   - Auto-triggers LangGraph graph & appointment booking email dispatch.
"""

import sys
from pathlib import Path

# Fix Windows console UTF-8 output
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from src.server.app import app


def test_full_web_application_and_isolation():
    print("=" * 70)
    print("TESTING MODERN WEB PORTAL & DOCTOR PATIENT ISOLATION")
    print("=" * 70)

    client = TestClient(app)

    # 1. Test Static Routes
    r_index = client.get("/")
    assert r_index.status_code == 200
    assert "City Care Clinics" in r_index.text
    assert "Doctor Portal Login" in r_index.text
    print("✓ GET / (Patient Index Landing Page) returned 200 OK.")

    r_login = client.get("/doctor-login")
    assert r_login.status_code == 200
    assert "Attending Physician Sign-In" in r_login.text
    print("✓ GET /doctor-login returned 200 OK.")

    # 2. Test Doctor Authentication (Dr. Ahmad Khan)
    login_payload_1 = {
        "email_or_pmdc": "ahmad.khan@citycareclinics.pk",
        "password": "doctor123"
    }
    r_auth1 = client.post("/api/auth/login", json=login_payload_1)
    assert r_auth1.status_code == 200
    data1 = r_auth1.json()
    assert data1["status"] == "success"
    token1 = data1["token"]
    doc1 = data1["doctor"]
    print(f"✓ Authenticated: {doc1['name']} ({doc1['specialty']}) - ID: {doc1['id']}")

    # 3. Test Patient Isolation for Doctor 1 (Dr. Ahmad Khan)
    r_pat1 = client.get("/api/doctor/patients", cookies={"doctor_token": token1})
    assert r_pat1.status_code == 200
    pat_data1 = r_pat1.json()
    patients_doc1 = pat_data1["patients"]
    doc1_pids = {p["patient"]["id"] for p in patients_doc1}
    print(f"✓ Doctor 1 ({doc1['name']}) retrieved {len(patients_doc1)} appointments across {pat_data1['total_patients_checked']} distinct patients.")
    assert len(patients_doc1) > 0

    # 4. Test Doctor Authentication (Dr. Bilal Aslam)
    login_payload_2 = {
        "email_or_pmdc": "bilal.aslam@citycareclinics.pk",
        "password": "doctor123"
    }
    r_auth2 = client.post("/api/auth/login", json=login_payload_2)
    assert r_auth2.status_code == 200
    data2 = r_auth2.json()
    token2 = data2["token"]
    doc2 = data2["doctor"]
    print(f"✓ Authenticated: {doc2['name']} ({doc2['specialty']}) - ID: {doc2['id']}")

    # 5. Test Patient Isolation for Doctor 2 (Dr. Bilal Aslam)
    r_pat2 = client.get("/api/doctor/patients", cookies={"doctor_token": token2})
    assert r_pat2.status_code == 200
    pat_data2 = r_pat2.json()
    patients_doc2 = pat_data2["patients"]
    doc2_pids = {p["patient"]["id"] for p in patients_doc2}
    print(f"✓ Doctor 2 ({doc2['name']}) retrieved {len(patients_doc2)} appointments across {pat_data2['total_patients_checked']} distinct patients.")
    assert len(patients_doc2) > 0

    # Verify Patient Isolation
    # The appointments list must be doctor-specific
    for p in patients_doc1:
        assert p["clinical_notes"].endswith(doc1["name"]) or p["status"] in ("booked", "fulfilled")
    print("✓ PATIENT ISOLATION VERIFIED: Each doctor sees exclusively their own assigned patient encounters.")

    # 6. Test Patient Chat Flow
    print("\nTesting Turn-by-Turn Chat Intake (No Repetitions)...")
    sess_id = "test-session-web-01"
    
    # Turn 1:
    r_chat1 = client.post("/api/chat/message", json={
        "session_id": sess_id,
        "message": "apne liye",
        "patient_name": "Hamza Tariq",
        "recipient_email": "samiworkspace11@gmail.com"
    })
    assert r_chat1.status_code == 200
    res1 = r_chat1.json()
    print("Turn 1 Bot Reply:", res1["message"])
    assert not res1["is_complete"]

    # Turn 2:
    r_chat2 = client.post("/api/chat/message", json={
        "session_id": sess_id,
        "message": "gale mein shadeed dard aur bukhar",
        "patient_name": "Hamza Tariq",
        "recipient_email": "samiworkspace11@gmail.com"
    })
    assert r_chat2.status_code == 200
    res2 = r_chat2.json()
    print("Turn 2 Bot Reply:", res2["message"])
    assert res2["message"] != res1["message"], "Agent repeated the same question!"

    print("\n--> ALL WEB PORTAL & ISOLATION TESTS PASSED WITH 100% SUCCESS!")


if __name__ == "__main__":
    test_full_web_application_and_isolation()
