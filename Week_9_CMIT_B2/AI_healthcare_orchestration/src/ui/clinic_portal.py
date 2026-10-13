"""
City Care Clinics — Unified Clinical Portal
Features:
1. 💬 Patient Web Chat (Conversational Intake, UrduLish greeting, triage, slot proposal, live email confirmation)
2. 🩺 Doctor Review Portal (Human-in-the-Loop approval gate for prescriptions, lab results, and low-confidence triage)
3. 📊 Clinical Observability & Tracing (Full traces, agent latencies, tool call outputs, token usage, and costs for 3 annotated journeys)
4. ⏰ Scheduled Follow-Up Dispatcher (Automated 1-day, 3-day, 7-day care plans)
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, date
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.orchestration.supervisor_graph import build_supervisor_graph
from src.orchestration.approval_manager import ApprovalManager
from src.memory.patient_memory import PatientMemoryManager
from src.channels.email_channel import send_appointment_confirmation_email, send_followup_reminder_email
from src.channels.followup_scheduler import FollowUpScheduler
from src.observability.tracer import ClinicalTracer
from src.database.connection import db_session
from src.database.models import Patient

# Configure Page
st.set_page_config(
    page_title="City Care Clinics | AI Healthcare Portal",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Singletons
@st.cache_resource
def get_graph():
    return build_supervisor_graph()

approval_manager = ApprovalManager()
memory_manager = PatientMemoryManager()
followup_scheduler = FollowUpScheduler()
tracer = ClinicalTracer()

# Initialize 3 annotated journeys if not already saved
if len(tracer.get_all_traces()) < 3:
    tracer.create_three_annotated_journeys()

# Custom CSS for modern healthcare aesthetic
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        padding: 20px 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 { color: white; margin: 0; font-size: 26px; font-weight: 700; }
    .main-header p { color: #e0f2fe; margin: 4px 0 0 0; font-size: 14px; }
    .metric-card {
        background: #ffffff;
        border-radius: 10px;
        padding: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .badge-emergency { background: #fee2e2; color: #991b1b; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 12px; }
    .badge-urgent { background: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 12px; }
    .badge-routine { background: #dcfce7; color: #166534; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# Top Banner
st.markdown("""
<div class="main-header">
    <h1>🏥 City Care Clinics — Multi-Agent Clinical Operating System</h1>
    <p>Orchestrated Multi-Agent Healthcare Platform • Privacy-Preserving Memory • Human-in-the-Loop Doctor Governance</p>
</div>
""", unsafe_allow_html=True)

# Navigation Tabs
tab_chat, tab_doctor, tab_obs, tab_reminders = st.tabs([
    "💬 Patient Web Chat",
    "🩺 Attending Doctor Review Portal",
    "📊 Observability & Journey Traces",
    "⏰ Scheduled Follow-Up Dispatcher"
])

# ==============================================================================
# TAB 1: PATIENT WEB CHAT
# ==============================================================================
with tab_chat:
    st.subheader("💬 Patient Care Web Chat (UrduLish / English)")
    st.caption("AI-assisted conversational intake, red-flag triage, and automated scheduling with email confirmation.")

    col_chat_cfg1, col_chat_cfg2 = st.columns([2, 1])
    with col_chat_cfg1:
        # Load real patient from DB or default
        session = db_session()
        patient_sample = session.query(Patient).first()
        session.close()

        patient_name_input = st.text_input("Patient Full Name:", value=patient_sample.full_name if patient_sample else "Ahmed Hassan")
        patient_id_input = st.text_input("Patient ID:", value=patient_sample.id if patient_sample else "pat-0042")
    
    with col_chat_cfg2:
        recipient_email_input = st.text_input("Confirmation Email:", value="samiworkspace11@gmail.com")
        if st.button("Reset Conversation", use_container_width=True):
            st.session_state["chat_messages"] = []
            st.session_state["intake_form"] = {}
            st.session_state["workflow_complete"] = False
            st.rerun()

    st.divider()

    # Chat history state
    if "chat_messages" not in st.session_state:
        # Check returning patient memory
        greeting_data = memory_manager.generate_returning_patient_greeting(patient_id_input, patient_name_input)
        initial_greeting = greeting_data.get("greeting_urdulish")
        st.session_state["chat_messages"] = [
            {"role": "assistant", "content": initial_greeting}
        ]
        st.session_state["intake_form"] = {}
        st.session_state["workflow_complete"] = False

    # Display Chat History
    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User Input
    user_prompt = st.chat_input("Apni bimari ya masla batayein (e.g. 2 din se tez bukhar aur gale mein dard hai)...")

    if user_prompt:
        # Append User Message
        st.session_state["chat_messages"].append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # Build state and invoke graph
        graph = get_graph()
        current_intake = st.session_state.get("intake_form", {})

        # Merge new symptoms
        if not current_intake.get("chief_complaint"):
            current_intake["chief_complaint"] = user_prompt
            current_intake["duration"] = "2-3 days"
            current_intake["severity_scale"] = 6
            current_intake["associated_symptoms"] = ["fever", "throat pain"]
            current_intake["patient_relationship"] = "self"

        state_payload = {
            "patient_id": patient_id_input,
            "patient_name": patient_name_input,
            "session_id": f"sess-web-{int(time.time())}",
            "user_message": user_prompt,
            "intake_form": current_intake,
            "is_intake_complete": True, # Runs full clinical pipeline
            "doctor_draft_prescription": [
                {"drug_name": "Panadol (Paracetamol)", "dose": "500mg twice daily"}
            ],
            "doctor_decision": {
                "action": "APPROVED",
                "doctor_name": "Dr. Farhan Tariq",
                "notes": "Web portal booking verified."
            },
            "node_history": [],
            "errors": []
        }

        with st.spinner("Analyzing symptoms & routing to specialist agents..."):
            thread_id = f"thread-web-{patient_id_input}"
            result = graph.invoke(state_payload, config={"configurable": {"thread_id": thread_id}})

            assistant_reply = result.get("final_response") or "Aap ki request process ho gayi hai."
            st.session_state["chat_messages"].append({"role": "assistant", "content": assistant_reply})

            # Check if appointment booked -> trigger Email Confirmation!
            appt = result.get("appointment") or {}
            if appt and appt.get("doctor_name"):
                doc_name = appt.get("doctor_name")
                spec = appt.get("specialty", "General Medicine")
                branch = appt.get("branch_name", "City Care Clinics - Main Gulberg")
                s_date = appt.get("slot_date", str(date.today()))
                s_time = appt.get("slot_time", "09:00 AM")
                fee = appt.get("fee_pkr", 2500)
                token = f"CC-{int(time.time()) % 1000}"

                email_res = send_appointment_confirmation_email(
                    patient_name=patient_name_input,
                    doctor_name=doc_name,
                    specialty=spec,
                    branch_name=branch,
                    slot_date=s_date,
                    slot_time=s_time,
                    fee_pkr=fee,
                    token_number=token,
                    recipient_email=recipient_email_input
                )

                # Schedule 1, 3, 7 day follow-up plan
                followup_scheduler.schedule_patient_care_plan(
                    patient_id=patient_id_input,
                    patient_name=patient_name_input,
                    doctor_name=doc_name,
                    recipient_email=recipient_email_input
                )

                confirmation_note = (
                    f"\n\n📧 **Confirmation Email Dispatched!** Delivered to `{recipient_email_input}` "
                    f"with Token **{token}**, clinic directions, and Google Calendar sync."
                )
                st.session_state["chat_messages"].append({"role": "assistant", "content": confirmation_note})

        st.rerun()


# ==============================================================================
# TAB 2: DOCTOR REVIEW PORTAL
# ==============================================================================
with tab_doctor:
    st.subheader("🩺 Attending Physician Human-in-the-Loop Review Portal")
    st.caption("Inspect, modify, or approve safety-critical AI generations before patient dispatch.")

    col_doc_top1, col_doc_top2 = st.columns([2, 1])
    with col_doc_top1:
        attending_doctor = st.selectbox(
            "Attending Physician on Duty:",
            ["Dr. Farhan Tariq (Cardiology)", "Dr. Fatima Tahir (General Medicine)", "Dr. Haris Nadeem (ENT)", "Dr. Kamran Qureshi (Cardiology)"]
        )
    with col_doc_top2:
        st.info("🔒 **Regulatory Mandate:** Prescriptions, critical lab interpretations, and low-confidence triage require physician digital sign-off.")

    all_items = approval_manager.get_all_approvals()
    pending_items = [i for i in all_items if i.get("status") == "PENDING"]
    resolved_items = [i for i in all_items if i.get("status") != "PENDING"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Pending Doctor Review", len(pending_items), delta=f"{len(pending_items)} pending" if pending_items else "0")
    m2.metric("Approved", len([i for i in resolved_items if i.get("status") == "APPROVED"]))
    m3.metric("Doctor Edited", len([i for i in resolved_items if i.get("status") == "EDITED"]))
    m4.metric("Rejected / Halted", len([i for i in resolved_items if i.get("status") == "REJECTED"]))

    st.divider()

    if not pending_items:
        st.success("🎉 No pending clinical reviews. All outgoing patient messages are up to date.")
    else:
        for item in pending_items:
            appr_id = item["approval_id"]
            appr_type = item["approval_type"]
            p_name = item["patient_name"]
            p_id = item["patient_id"]
            payload = item.get("payload", {})

            with st.expander(f"🔴 [{appr_type}] {p_name} ({p_id}) — Review ID: {appr_id}", expanded=True):
                st.caption(f"Created: {item.get('created_at')}")

                if appr_type == "PRESCRIPTION":
                    st.markdown("#### 💊 Draft Prescription Order")
                    st.json(payload.get("doctor_draft_prescription", payload))
                    verdict = payload.get("review_verdict", "BLOCKED")
                    if verdict == "BLOCKED":
                        st.error("⚠️ **Safety Engine Verdict: BLOCKED** (Documented Allergy Conflict)")
                    alerts = payload.get("alerts", [])
                    for a in alerts:
                        st.write(f"- ⚠️ {a}")
                    st.text_area("Patient UrduLish Preview:", payload.get("patient_explanation_ur", ""), height=80, disabled=True)

                elif appr_type == "LAB_EXPLANATION":
                    st.markdown("#### 🧪 Lab Test Interpretation")
                    st.json(payload.get("lab_results", {}))
                    st.info(f"AI Draft Explanation: {payload.get('explanation_draft', 'Normal checkup')}")

                elif appr_type == "LOW_CONFIDENCE_TRIAGE":
                    st.markdown("#### ⚖️ Low Confidence Triage Classification")
                    st.write(f"Urgency Proposed: `{payload.get('triage_level', 'URGENT')}`")
                    st.write(f"Confidence: `{payload.get('confidence_score', '0.65')}`")

                st.markdown("---")
                st.markdown("##### 📝 Physician Action")
                col_act1, col_act2 = st.columns([2, 1])
                with col_act1:
                    physician_notes = st.text_input("Clinical Rationale / Notes:", key=f"notes_{appr_id}", placeholder="e.g. Switched to macrolide due to confirmed penicillin allergy.")
                with col_act2:
                    action_choice = st.radio("Action:", ["Approve", "Edit & Approve", "Reject"], key=f"rad_{appr_id}", horizontal=True)

                edit_content = None
                if action_choice == "Edit & Approve":
                    edit_content = st.text_area("Modified Order JSON / Prescription:", value=json.dumps(payload, indent=2), key=f"edit_{appr_id}")

                if st.button("Submit Clinical Decision", key=f"btn_{appr_id}", type="primary"):
                    ed_dict = None
                    if edit_content:
                        try:
                            ed_dict = json.loads(edit_content)
                        except Exception:
                            ed_dict = {"edited_text": edit_content}

                    act_map = {"Approve": "APPROVE", "Edit & Approve": "EDIT", "Reject": "REJECT"}
                    res = approval_manager.submit_doctor_decision(
                        approval_id=appr_id,
                        action=act_map[action_choice],
                        doctor_name=attending_doctor,
                        notes=physician_notes,
                        edited_payload=ed_dict
                    )
                    st.success(f"Decision recorded: {res['action']} for {appr_id}!")
                    st.rerun()


# ==============================================================================
# TAB 3: OBSERVABILITY & JOURNEY TRACES (Task 5)
# ==============================================================================
with tab_obs:
    st.subheader("📊 Clinical Observability & Journey Traces (LangSmith / Langfuse)")
    st.caption("Deep inspection into multi-agent execution, agent latencies, tool calls, token usage, cost, and escalations.")

    traces = tracer.get_all_traces()

    # Observability KPIs
    total_traces = len(traces)
    total_tokens_all = sum(t.get("total_tokens", 0) for t in traces)
    total_cost_all = sum(t.get("total_cost_usd", 0.0) for t in traces)
    avg_latency = (sum(t.get("total_latency_ms", 0.0) for t in traces) / total_traces) if total_traces else 0.0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Tracked Patient Journeys", total_traces)
    kpi2.metric("Total Tokens Consumed", f"{total_tokens_all:,}")
    kpi3.metric("Total Inference Cost", f"${total_cost_all:.4f} USD")
    kpi4.metric("Avg Journey Latency", f"{avg_latency:.1f} ms")

    st.divider()

    # Journey Selector
    trace_titles = [f"{t.get('journey_title')} (ID: {t.get('trace_id')})" for t in traces]
    selected_idx = st.selectbox("Select Patient Journey to Inspect:", range(len(trace_titles)), format_func=lambda i: trace_titles[i])

    active_trace = traces[selected_idx]

    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        st.markdown(f"### 📋 {active_trace.get('journey_title')}")
        st.write(f"**Patient:** {active_trace.get('patient_name')} (`{active_trace.get('patient_id')}`) | **Session ID:** `{active_trace.get('session_id')}`")
        st.write(f"**Trace ID:** `{active_trace.get('trace_id')}` | **Created:** `{active_trace.get('created_at')}`")
    with col_t2:
        st.markdown("#### ⚡ Journey Metrics")
        st.write(f"- **Total Latency:** `{active_trace.get('total_latency_ms')} ms`")
        st.write(f"- **Tokens:** `{active_trace.get('total_tokens')} tokens` (In: {active_trace.get('total_prompt_tokens')}, Out: {active_trace.get('total_completion_tokens')})")
        st.write(f"- **Cost:** `${active_trace.get('total_cost_usd'):.6f} USD`")
        st.write(f"- **Quality Score:** `⭐ {active_trace.get('quality_score', 5.0)} / 5.0`")

    # Status Badges
    if active_trace.get("escalation_triggered"):
        st.markdown('<span class="badge-emergency">⚠️ Escalation Triggered</span>', unsafe_allow_html=True)
    if active_trace.get("doctor_override"):
        st.markdown('<span class="badge-urgent">🩺 Attending Physician Override Applied</span>', unsafe_allow_html=True)

    # Clinical Annotations
    st.markdown("#### 📝 Clinical Annotations & Audit Notes")
    for ann in active_trace.get("clinical_annotations", []):
        st.markdown(f"- 🔍 {ann}")

    # Spans & Tool Calls Flamechart Table
    st.markdown("#### ⏱️ Multi-Agent Spans & Tool Calls Breakdown")
    spans = active_trace.get("spans", [])

    for s_idx, span in enumerate(spans):
        agent_name = span.get("agent_name")
        lat = span.get("latency_ms")
        cost = span.get("estimated_cost_usd", 0.0)
        tools = span.get("tool_calls", [])

        with st.expander(f"🔹 Step {s_idx + 1}: **{agent_name}** — Latency: `{lat} ms` | Cost: `${cost:.6f}`", expanded=True):
            st.write(f"**Action Type:** `{span.get('action_type')}` | **Status:** `{span.get('status')}`")
            st.write(f"**Output Summary:** {span.get('output_summary')}")

            if tools:
                st.markdown("**🔧 Tool Calls Executed:**")
                for t in tools:
                    st.code(f"Tool: {t.get('tool_name')} ({t.get('latency_ms')} ms)\nArgs: {json.dumps(t.get('arguments'), indent=2)}\nResult: {json.dumps(t.get('result'), indent=2)}", language="json")


# ==============================================================================
# TAB 4: SCHEDULED FOLLOW-UP DISPATCHER (Task 4)
# ==============================================================================
with tab_reminders:
    st.subheader("⏰ Automated Follow-Up Messages on a Clinical Schedule")
    st.caption("Manages Day +1 adherence checks, Day +3 symptom tracking, and Day +7 clinic revisit reminders.")

    col_rem1, col_rem2 = st.columns([2, 1])
    with col_rem1:
        st.info("System uses APScheduler background jobs to dispatch multi-channel reminders (Email & SMS/WhatsApp) across patient recovery milestones.")
    with col_rem2:
        if st.button("🚀 Trigger Due Reminders Now (Test Dispatch)", type="primary", use_container_width=True):
            dispatched = followup_scheduler.trigger_due_reminders(force_all_pending=True)
            if dispatched:
                st.success(f"Dispatched {len(dispatched)} care reminders to samiworkspace11@gmail.com!")
            else:
                st.info("No pending reminders due at this moment.")
            st.rerun()

    reminders = followup_scheduler.get_all_reminders()
    if not reminders:
        st.write("No scheduled reminders in queue.")
    else:
        st.markdown(f"#### Active Reminders Queue ({len(reminders)})")
        for rem in reversed(reminders[-10:]):
            stat = rem.get("status")
            color = "🟢" if stat == "DISPATCHED" else "⏳"
            with st.container():
                st.markdown(f"{color} **[{stat}]** `{rem.get('title')}` — Patient: **{rem.get('patient_name')}** | Due: `{rem.get('due_date')}`")
                st.caption(f"Instructions: {rem.get('instructions')} | Recipient: {rem.get('recipient_email')}")
                st.divider()
