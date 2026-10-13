"""
Doctor Dashboard (Streamlit Web Interface) for City Care Clinics.
Implements Week 9 Day 4 Task 3:
- Human-in-the-Loop Doctor Review Queue.
- Review and action (Approve / Edit / Reject) for:
  1. Lab Result Explanations
  2. Draft Prescriptions & Medication Messages
  3. Low-Confidence Triage Decisions
- Live audit log tracking and resolution history.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.orchestration.approval_manager import ApprovalManager

# Set page config
st.set_page_config(
    page_title="Doctor Review Dashboard | City Care Clinics",
    page_icon="🩺",
    layout="wide"
)

approval_manager = ApprovalManager()

# Top Header
st.title("🩺 City Care Clinics — Attending Physician Review Portal")
st.markdown(
    "*Human-in-the-Loop Clinical Governance System: Reviews, overrides, and approves all safety-critical AI generations.*"
)

# Sidebar with doctor info & filters
st.sidebar.header("Physician On Duty")
doctor_name = st.sidebar.selectbox(
    "Attending Doctor",
    ["Dr. Farhan Tariq (Cardiology)", "Dr. Fatima Tahir (General Medicine)", "Dr. Kamran Qureshi (Cardiology)", "Dr. Farzana Malik (Gynaecology)"]
)
st.sidebar.divider()
st.sidebar.info(
    "🔒 **Regulatory Gate:** No prescription or lab interpretation can reach a patient without physician digital authorization."
)

# Fetch approvals
all_items = approval_manager.get_all_approvals()
pending_items = [i for i in all_items if i.get("status") == "PENDING"]
resolved_items = [i for i in all_items if i.get("status") != "PENDING"]

# KPI Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Pending Doctor Review", len(pending_items), delta=f"{len(pending_items)} urgent" if pending_items else "0")
col2.metric("Approved", len([i for i in resolved_items if i.get("status") == "APPROVED"]))
col3.metric("Edited by Doctor", len([i for i in resolved_items if i.get("status") == "EDITED"]))
col4.metric("Rejected / Halted", len([i for i in resolved_items if i.get("status") == "REJECTED"]))

st.divider()

# Tabs
tab1, tab2, tab3 = st.tabs(["📋 Pending Approvals Queue", "📜 Historical Decisions Audit", "🧪 Inject Test Case"])

with tab1:
    if not pending_items:
        st.success("🎉 No pending clinical reviews. All patient dispatches are up to date.")
    else:
        st.subheader(f"Items Awaiting Physician Sign-Off ({len(pending_items)})")

        for item in pending_items:
            appr_id = item["approval_id"]
            appr_type = item["approval_type"]
            p_name = item["patient_name"]
            p_id = item["patient_id"]
            created = item["created_at"]
            payload = item.get("payload", {})

            with st.expander(f"🔴 [{appr_type}] {p_name} ({p_id}) — ID: {appr_id}", expanded=True):
                st.caption(f"Submitted for review at: {created}")

                # Context-specific view
                if appr_type == "PRESCRIPTION":
                    st.markdown("#### 💊 Draft Prescription Details")
                    draft_meds = payload.get("doctor_draft_prescription", [])
                    st.json(draft_meds)

                    verdict = payload.get("review_verdict", "UNKNOWN")
                    if verdict == "BLOCKED":
                        st.error(f"⚠️ **Safety Engine Verdict: BLOCKED**")
                    else:
                        st.warning(f"⚠️ **Safety Engine Verdict: {verdict}**")

                    alerts = payload.get("alerts", [])
                    if alerts:
                        st.markdown("**Safety Alerts Detected:**")
                        for a in alerts:
                            st.write(f"- {a}")

                    patient_msg = payload.get("patient_explanation_ur", "")
                    st.text_area("Patient Explanation Preview (UrduLish):", patient_msg, height=90, key=f"preview_{appr_id}", disabled=True)

                elif appr_type == "LAB_EXPLANATION":
                    st.markdown("#### 🧪 Lab Result Interpretation")
                    st.json(payload.get("lab_results", {}))
                    st.markdown(f"**AI Draft Explanation for Patient:**")
                    st.info(payload.get("explanation_draft", "No draft text provided."))

                elif appr_type == "LOW_CONFIDENCE_TRIAGE":
                    st.markdown("#### ⚖️ Borderline / Low-Confidence Triage Decision")
                    st.write(f"**Triage Level Proposed:** `{payload.get('triage_level', 'UNKNOWN')}`")
                    st.write(f"**Confidence Score:** `{payload.get('confidence_score', 'N/A')}`")
                    st.write(f"**Clinical Reasoning:** {payload.get('reasoning', 'N/A')}")

                # Doctor Review Action Controls
                st.markdown("---")
                st.markdown("##### 📝 Physician Action & Sign-Off")

                action_col1, action_col2 = st.columns([2, 1])
                with action_col1:
                    notes = st.text_input("Physician Clinical Notes / Rationale:", key=f"notes_{appr_id}", placeholder="e.g. Dose adjusted for renal function or Approved after review")

                with action_col2:
                    action_choice = st.radio("Action:", ["Approve", "Edit & Approve", "Reject"], key=f"action_{appr_id}", horizontal=True)

                edited_content = None
                if action_choice == "Edit & Approve":
                    edited_content = st.text_area("Modified Text / Prescription Order:", value=json.dumps(payload, indent=2), key=f"edit_box_{appr_id}")

                if st.button("Submit Clinical Decision", key=f"submit_{appr_id}", type="primary"):
                    ed_dict = None
                    if edited_content:
                        try:
                            ed_dict = json.loads(edited_content)
                        except Exception:
                            ed_dict = {"edited_text": edited_content}

                    act_map = {"Approve": "APPROVE", "Edit & Approve": "EDIT", "Reject": "REJECT"}
                    res = approval_manager.submit_doctor_decision(
                        approval_id=appr_id,
                        action=act_map[action_choice],
                        doctor_name=doctor_name,
                        notes=notes,
                        edited_payload=ed_dict
                    )
                    st.success(f"Decision recorded: {res['action']} for {appr_id}!")
                    st.rerun()

with tab2:
    st.subheader("Completed Reviews & Immutable Audit History")
    if not resolved_items:
        st.write("No historical actions recorded yet.")
    else:
        for r in resolved_items:
            dec = r.get("doctor_decision") or {}
            color = "🟢" if r["status"] == "APPROVED" else ("🟡" if r["status"] == "EDITED" else "🔴")
            st.markdown(
                f"{color} **[{r['status']}]** {r['approval_type']} — Patient: **{r['patient_name']}** "
                f"| Signed by: *{dec.get('doctor_name', 'Doctor')}* at {r.get('resolved_at', 'N/A')}"
            )
            if dec.get("notes"):
                st.caption(f"Notes: {dec.get('notes')}")

with tab3:
    st.subheader("Generate Sample Review Case for Testing")
    test_type = st.selectbox("Select Case Type to Inject:", ["PRESCRIPTION", "LAB_EXPLANATION", "LOW_CONFIDENCE_TRIAGE"])
    sample_patient = st.text_input("Patient Name:", "Zainab Bibi")

    if st.button("Inject Test Review Request into Queue"):
        sample_payloads = {
            "PRESCRIPTION": {
                "doctor_draft_prescription": [{"drug_name": "Amoxil", "dose": "500mg tid"}],
                "review_verdict": "BLOCKED",
                "alerts": ["Contraindicated: Patient documented Penicillin Allergy."],
                "patient_explanation_ur": "⚠️ Yeh dawa Penicillin allergy ki wajah se rok di gayi hai."
            },
            "LAB_EXPLANATION": {
                "lab_results": {"HbA1c": "9.4%", "Fast Blood Glucose": "210 mg/dL"},
                "explanation_draft": "Aap ka sugar level high hai. Doctor se follow-up mashwara zaroori hai."
            },
            "LOW_CONFIDENCE_TRIAGE": {
                "triage_level": "URGENT",
                "confidence_score": 0.62,
                "reasoning": "Atypical headache with nausea in elderly patient, requires physician validation."
            }
        }
        new_id = approval_manager.create_approval_request(
            approval_type=test_type,
            patient_id="pat-0042",
            patient_name=sample_patient,
            payload=sample_payloads[test_type]
        )
        st.success(f"Injected new approval item: {new_id}!")
        st.rerun()
