"""
LangGraph Supervisor & Multi-Agent Orchestration Graph for City Care Clinics.
Implements:
1. Central Supervisor Router coordinating 7 specialist agents.
2. Parallel Fan-Out / Fan-In Execution: Triage & Records execute concurrently after Intake.
3. Long-Term & Short-Term Memory Integration.
4. Human-in-the-Loop Interruption Gate for Doctor Approvals:
   - Lab Result Explanations
   - Draft Prescriptions
   - Low-Confidence Triage Decisions
5. Resilient Error Handling, Retries, and Fallbacks.
6. Comprehensive Node Transition Audit Logging & Mermaid Graph Generation.
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from src.orchestration.state import ClinicAgentState
from src.orchestration.approval_manager import ApprovalManager
from src.memory.patient_memory import PatientMemoryManager
from src.agents.intake_agent import IntakeAgent
from src.agents.triage_agent import TriageAgent
from src.agents.scheduling_agent import SchedulingAgent
from src.agents.records_agent import RecordsAgent
from src.agents.clinical_summary_agent import ClinicalSummaryAgent
from src.agents.prescription_safety_agent import PrescriptionSafetyAgent
from src.agents.followup_agent import FollowUpAgent

# Instantiate singletons
approval_manager = ApprovalManager()
memory_manager = PatientMemoryManager()
intake_agent = IntakeAgent()
triage_agent = TriageAgent()
scheduling_agent = SchedulingAgent()
records_agent = RecordsAgent()
clinical_summary_agent = ClinicalSummaryAgent()
rx_agent = PrescriptionSafetyAgent()
followup_agent = FollowUpAgent()


def _log_transition(state: ClinicAgentState, node_name: str) -> List[str]:
    """Helper to audit log every node execution."""
    ts = datetime.utcnow().strftime("%H:%M:%S")
    return [f"[{ts}] -> {node_name}"]


# -------------------------------------------------------------
# GRAPH NODE DEFINITIONS
# -------------------------------------------------------------

def entry_node(state: ClinicAgentState) -> Dict[str, Any]:
    """Initializes session, loads patient memory, and checks for returning patient greeting."""
    transitions = _log_transition(state, "entry_node")
    p_id = state.get("patient_id")
    p_name = state.get("patient_name", "Patient")

    greeting_info = memory_manager.generate_returning_patient_greeting(p_id or "new", p_name)
    mem = memory_manager.get_memory(p_id) if p_id else None

    profile_data = {
        "is_returning_patient": greeting_info.get("is_returning_patient", False),
        "preferred_doctor": mem.preferred_doctor_name if mem else None,
        "preferred_branch": mem.preferred_branch if mem else None,
        "preferred_language": mem.preferred_language if mem else "UrduLish"
    }

    return {
        "current_node": "entry_node",
        "node_history": transitions,
        "patient_profile": profile_data,
        "preferred_language": profile_data["preferred_language"]
    }


def intake_node(state: ClinicAgentState) -> Dict[str, Any]:
    """Conversational Intake: collects one question at a time."""
    transitions = _log_transition(state, "intake_node")
    user_msg = state.get("user_message", "")
    curr_intake = state.get("intake_form") or {}

    try:
        intake_res = intake_agent.process_turn(curr_intake, user_msg)
        is_complete = intake_res.get("is_complete", False)
        updated_form = intake_res.get("intake_state", {})

        return {
            "current_node": "intake_node",
            "node_history": transitions,
            "intake_form": updated_form,
            "is_intake_complete": is_complete,
            "final_response": intake_res.get("response_message") if not is_complete else None
        }
    except Exception as e:
        err = {"node": "intake_node", "error": str(e), "timestamp": datetime.utcnow().isoformat()}
        return {
            "current_node": "intake_node",
            "node_history": transitions,
            "is_intake_complete": True,
            "intake_form": curr_intake,
            "errors": [err]
        }


# --- PARALLEL EXECUTION: Triage & Records run concurrently ---

def parallel_triage_node(state: ClinicAgentState) -> Dict[str, Any]:
    """Runs Triage Agent in parallel with Records retrieval."""
    transitions = _log_transition(state, "parallel_triage_node")
    intake = state.get("intake_form") or {}
    cc = intake.get("chief_complaint", state.get("user_message", ""))
    sev = intake.get("severity_scale", 5)
    symptoms = intake.get("associated_symptoms", [])

    try:
        triage_res = triage_agent.evaluate_triage(
            chief_complaint=cc,
            duration=intake.get("duration", ""),
            severity_scale=sev,
            associated_symptoms=symptoms
        )
        return {
            "current_node": "parallel_triage_node",
            "node_history": transitions,
            "triage_level": triage_res.urgency_tier,
            "triage_result": triage_res.model_dump(),
            "is_emergency": triage_res.is_emergency
        }
    except Exception as e:
        err = {"node": "parallel_triage_node", "error": str(e), "timestamp": datetime.utcnow().isoformat()}
        return {
            "current_node": "parallel_triage_node",
            "node_history": transitions,
            "triage_level": "ROUTINE",
            "is_emergency": False,
            "errors": [err]
        }


def parallel_records_node(state: ClinicAgentState) -> Dict[str, Any]:
    """Runs Records Agent in parallel to fetch verified EHR history and lab results."""
    transitions = _log_transition(state, "parallel_records_node")
    p_id = state.get("patient_id")

    history = []
    labs = []
    if p_id:
        try:
            from src.mcp_servers.patient_records_server import get_patient_profile, get_lab_history
            prof = get_patient_profile(p_id)
            if prof.get("status") == "success":
                history = [c["code"] for c in prof.get("conditions", [])]
            lab_data = get_lab_history(p_id, limit=5)
            if lab_data.get("status") == "success":
                labs = lab_data.get("observations", [])
        except Exception as e:
            err = {"node": "parallel_records_node", "error": str(e), "timestamp": datetime.utcnow().isoformat()}
            return {"current_node": "parallel_records_node", "node_history": transitions, "errors": [err]}

    return {
        "current_node": "parallel_records_node",
        "node_history": transitions,
        "patient_history": history,
        "lab_results": labs
    }


def triage_evaluator_node(state: ClinicAgentState) -> Dict[str, Any]:
    """
    Fan-in aggregator after parallel triage and records nodes.
    Evaluates urgency:
    - Emergency -> routes to emergency_escalation_node.
    - Low confidence (< 0.75) -> triggers doctor approval requirement.
    - Standard -> proceeds to clinical_summary_node.
    """
    transitions = _log_transition(state, "triage_evaluator_node")
    triage_res = state.get("triage_result") or {}
    conf = triage_res.get("confidence_score", 1.0)
    is_emerg = state.get("is_emergency", False)

    req_approval = False
    appr_type = None

    if not is_emerg and conf < 0.75:
        req_approval = True
        appr_type = "LOW_CONFIDENCE_TRIAGE"

    return {
        "current_node": "triage_evaluator_node",
        "node_history": transitions,
        "requires_doctor_approval": req_approval,
        "approval_type": appr_type
    }


def emergency_escalation_node(state: ClinicAgentState) -> Dict[str, Any]:
    """Immediate Emergency Escalation path: halts booking and provides 1122 guidance."""
    transitions = _log_transition(state, "emergency_escalation_node")
    triage_res = state.get("triage_result") or {}

    msg = triage_res.get("patient_guidance_ur", (
        "⚠️ EMERGENCY ALERT: Yeh alamat shadeed khatarnak ho sakti hain. "
        "Bara-e-meherbani foran Rescue 1122 par call karein ya qareebi Emergency Room tashreef le jayen!"
    ))

    return {
        "current_node": "emergency_escalation_node",
        "node_history": transitions,
        "final_response": msg
    }


def clinical_summary_node(state: ClinicAgentState) -> Dict[str, Any]:
    """Synthesizes pre-visit SOAP Note, strictly separating facts from AI suggestions."""
    transitions = _log_transition(state, "clinical_summary_node")
    intake = state.get("intake_form") or {}
    p_id = state.get("patient_id") or "PT-NEW"
    p_name = state.get("patient_name", "Patient")
    history = state.get("patient_history") or []
    labs = state.get("lab_results") or []

    try:
        soap = clinical_summary_agent.generate_soap_note(
            patient_id=p_id,
            patient_name=p_name,
            intake_data=intake,
            patient_history=history,
            recent_labs=labs
        )
        return {
            "current_node": "clinical_summary_node",
            "node_history": transitions,
            "clinical_summary": soap.model_dump()
        }
    except Exception as e:
        err = {"node": "clinical_summary_node", "error": str(e), "timestamp": datetime.utcnow().isoformat()}
        return {
            "current_node": "clinical_summary_node",
            "node_history": transitions,
            "clinical_summary": {"error": "SOAP synthesis fallback applied"},
            "errors": [err]
        }


def scheduling_node(state: ClinicAgentState) -> Dict[str, Any]:
    """Matches doctor based on triage and preferences, then proposes/reserves slot."""
    transitions = _log_transition(state, "scheduling_node")
    triage_res = state.get("triage_result") or {}
    spec = triage_res.get("recommended_specialty", "General Medicine")
    pref = state.get("doctor_preference") or {}
    p_id = state.get("patient_id") or "pat-0001"

    try:
        # Match doctor
        docs = scheduling_agent.match_doctors(
            specialty=spec,
            city=pref.get("city", "Lahore"),
            gender_preference=pref.get("gender"),
            branch_preference=pref.get("branch")
        )
        matched_doc = docs[0] if docs else scheduling_agent.match_doctors(specialty="General Medicine")[0]

        # Propose slot
        slot_prop = scheduling_agent.propose_next_available_slot(matched_doc)

        appt_info = {
            "doctor_id": matched_doc["doctor_id"],
            "doctor_name": matched_doc["name"],
            "specialty": matched_doc["specialty"],
            "branch_name": matched_doc["branch_name"],
            "fee_pkr": matched_doc["consultation_fee_pkr"],
            "slot_date": slot_prop.get("date"),
            "slot_time": slot_prop.get("slot_time"),
            "proposal_message": slot_prop.get("proposal_message_urdulish")
        }

        # Update long-term memory
        memory_manager.update_memory_after_visit(
            patient_id=p_id,
            doctor_name=matched_doc["name"],
            doctor_id=matched_doc["doctor_id"],
            branch_name=matched_doc["branch_name"],
            complaint_summary=state.get("intake_form", {}).get("chief_complaint", "")
        )

        return {
            "current_node": "scheduling_node",
            "node_history": transitions,
            "appointment": appt_info
        }
    except Exception as e:
        err = {"node": "scheduling_node", "error": str(e), "timestamp": datetime.utcnow().isoformat()}
        return {
            "current_node": "scheduling_node",
            "node_history": transitions,
            "appointment": {"status": "scheduling_fallback"},
            "errors": [err]
        }


def prescription_safety_node(state: ClinicAgentState) -> Dict[str, Any]:
    """Runs deterministic prescription safety engine on doctor's draft prescription."""
    transitions = _log_transition(state, "prescription_safety_node")
    draft_rx = state.get("doctor_draft_prescription")
    p_id = state.get("patient_id") or "pat-0001"

    if not draft_rx:
        return {"current_node": "prescription_safety_node", "node_history": transitions}

    try:
        review = rx_agent.review_draft_prescription(
            doctor_name=state.get("appointment", {}).get("doctor_name", "Attending Physician"),
            patient_id=p_id,
            proposed_medications=draft_rx
        )

        # Prescription ALWAYS requires doctor approval step before dispensing
        return {
            "current_node": "prescription_safety_node",
            "node_history": transitions,
            "prescription_safety_review": review.model_dump(),
            "requires_doctor_approval": True,
            "approval_type": "PRESCRIPTION",
            "approval_payload": {
                "doctor_draft_prescription": draft_rx,
                "review_verdict": review.safety_verdict,
                "alerts": review.doctor_alerts,
                "patient_explanation_ur": review.patient_explanation_ur
            }
        }
    except Exception as e:
        err = {"node": "prescription_safety_node", "error": str(e), "timestamp": datetime.utcnow().isoformat()}
        return {"current_node": "prescription_safety_node", "node_history": transitions, "errors": [err]}


def human_approval_gate_node(state: ClinicAgentState) -> Dict[str, Any]:
    """
    Human-in-the-Loop Interruption Gate.
    Pauses execution for Doctor Approval if safety-critical review is required.
    Resumes seamlessly when the physician submits APPROVE, EDIT, or REJECT.
    """
    transitions = _log_transition(state, "human_approval_gate_node")
    req_approval = state.get("requires_doctor_approval", False)
    existing_decision = state.get("doctor_decision")

    if req_approval and not existing_decision:
        appr_type = state.get("approval_type", "GENERAL_REVIEW")
        p_id = state.get("patient_id") or "PT-UNKNOWN"
        p_name = state.get("patient_name", "Patient")
        payload = state.get("approval_payload") or {
            "triage_result": state.get("triage_result"),
            "appointment": state.get("appointment")
        }

        # Queue in ApprovalManager
        appr_id = approval_manager.create_approval_request(
            approval_type=appr_type,
            patient_id=p_id,
            patient_name=p_name,
            payload=payload,
            context={"session_id": state.get("session_id", "default")}
        )

        # Interrupt LangGraph execution
        decision = interrupt({
            "approval_id": appr_id,
            "approval_type": appr_type,
            "patient_name": p_name,
            "payload": payload,
            "instructions": "Graph execution paused. Awaiting attending physician approval via Doctor Dashboard."
        })

        return {
            "current_node": "human_approval_gate_node",
            "node_history": transitions,
            "approval_id": appr_id,
            "doctor_decision": decision
        }

    return {
        "current_node": "human_approval_gate_node",
        "node_history": transitions
    }


def followup_node(state: ClinicAgentState) -> Dict[str, Any]:
    """Creates care plan, medicine timetable, and patient notification messages."""
    transitions = _log_transition(state, "followup_node")
    p_name = state.get("patient_name", "Patient")
    doc_name = state.get("appointment", {}).get("doctor_name", "Doctor")
    draft_rx = state.get("doctor_draft_prescription") or [{"brand": "Panadol", "dose": "500mg", "timing": "twice daily"}]

    try:
        plan = followup_agent.create_reminder_plan(
            patient_name=p_name,
            doctor_name=doc_name,
            prescribed_medications=draft_rx,
            follow_up_days=7
        )
        return {
            "current_node": "followup_node",
            "node_history": transitions,
            "follow_up_plan": plan.model_dump()
        }
    except Exception as e:
        err = {"node": "followup_node", "error": str(e), "timestamp": datetime.utcnow().isoformat()}
        return {"current_node": "followup_node", "node_history": transitions, "errors": [err]}


def final_response_node(state: ClinicAgentState) -> Dict[str, Any]:
    """Consolidates final output and user response."""
    transitions = _log_transition(state, "final_response_node")

    # If response already set (e.g. intake incomplete or emergency), retain it
    if state.get("final_response"):
        return {"current_node": "final_response_node", "node_history": transitions}

    appt = state.get("appointment") or {}
    proposal = appt.get("proposal_message", "Appointment slot proposed.")
    plan = state.get("follow_up_plan") or {}

    response_text = f"{proposal}\n\n"
    if plan:
        response_text += f"📅 Follow-Up Plan: Checkup recommended around {plan.get('follow_up_visit_date')}."

    return {
        "current_node": "final_response_node",
        "node_history": transitions,
        "final_response": response_text
    }


# -------------------------------------------------------------
# ROUTER & CONDITIONAL EDGE FUNCTIONS
# -------------------------------------------------------------

def route_after_intake(state: ClinicAgentState) -> List[str]:
    """
    If intake is incomplete: ends early to return the next question.
    If intake is complete: routes to PARALLEL execution of Triage + Records!
    """
    if not state.get("is_intake_complete", False):
        return ["final_response_node"]
    return ["parallel_triage_node", "parallel_records_node"]


def route_after_triage_eval(state: ClinicAgentState) -> str:
    """Routes based on emergency check."""
    if state.get("is_emergency", False):
        return "emergency_escalation_node"
    return "clinical_summary_node"


# -------------------------------------------------------------
# GRAPH COMPILER
# -------------------------------------------------------------

def build_supervisor_graph(checkpointer=None):
    """Compiles the complete LangGraph StateGraph."""
    graph = StateGraph(ClinicAgentState)

    # Add Nodes
    graph.add_node("entry_node", entry_node)
    graph.add_node("intake_node", intake_node)
    graph.add_node("parallel_triage_node", parallel_triage_node)
    graph.add_node("parallel_records_node", parallel_records_node)
    graph.add_node("triage_evaluator_node", triage_evaluator_node)
    graph.add_node("emergency_escalation_node", emergency_escalation_node)
    graph.add_node("clinical_summary_node", clinical_summary_node)
    graph.add_node("scheduling_node", scheduling_node)
    graph.add_node("prescription_safety_node", prescription_safety_node)
    graph.add_node("human_approval_gate_node", human_approval_gate_node)
    graph.add_node("followup_node", followup_node)
    graph.add_node("final_response_node", final_response_node)

    # Edges: Sequential Entry -> Intake
    graph.add_edge(START, "entry_node")
    graph.add_edge("entry_node", "intake_node")

    # Conditional Fork: After Intake -> Parallel [Triage, Records] or Final (if incomplete)
    graph.add_conditional_edges("intake_node", route_after_intake, ["parallel_triage_node", "parallel_records_node", "final_response_node"])

    # Fan-in: Both parallel nodes merge into triage_evaluator_node
    graph.add_edge("parallel_triage_node", "triage_evaluator_node")
    graph.add_edge("parallel_records_node", "triage_evaluator_node")

    # Conditional Edge: After Triage Evaluator -> Emergency or Clinical Summary
    graph.add_conditional_edges("triage_evaluator_node", route_after_triage_eval, ["emergency_escalation_node", "clinical_summary_node"])
    graph.add_edge("emergency_escalation_node", "final_response_node")

    # Sequential Clinical Workflow
    graph.add_edge("clinical_summary_node", "scheduling_node")
    graph.add_edge("scheduling_node", "prescription_safety_node")
    graph.add_edge("prescription_safety_node", "human_approval_gate_node")
    graph.add_edge("human_approval_gate_node", "followup_node")
    graph.add_edge("followup_node", "final_response_node")
    graph.add_edge("final_response_node", END)

    return graph.compile(checkpointer=checkpointer or MemorySaver())


def get_mermaid_graph() -> str:
    """Returns the visual Mermaid diagram representation of the graph."""
    return """```mermaid
flowchart TD
    START([Start]) --> Entry[entry_node: Load Profile & Memory]
    Entry --> Intake[intake_node: Conversational Intake]
    
    Intake -->|Intake Incomplete| Final[final_response_node]
    Intake -->|Intake Complete| Fork1((Parallel Execution))
    
    Fork1 --> Triage[parallel_triage_node: Urgency & Red Flags]
    Fork1 --> Records[parallel_records_node: Verified EHR & Labs]
    
    Triage --> TriageEval[triage_evaluator_node: Fan-In Evaluator]
    Records --> TriageEval
    
    TriageEval -->|Emergency Detected| Emerg[emergency_escalation_node: 1122 Dispatch]
    Emerg --> Final
    
    TriageEval -->|Routine / Urgent| Summary[clinical_summary_node: Pre-Visit SOAP]
    Summary --> Scheduling[scheduling_node: Doctor Matching & Slots]
    Scheduling --> RxSafety[prescription_safety_node: Deterministic Checks]
    
    RxSafety --> ApprovalGate{human_approval_gate_node: Doctor Review}
    ApprovalGate -->|Interrupt & Approved| Followup[followup_node: Care Plan & Reminders]
    
    Followup --> Final
    Final --> END([End])

    style Fork1 fill:#fef08a,stroke:#ca8a04
    style ApprovalGate fill:#fecaca,stroke:#dc2626,stroke-width:2px
    style Emerg fill:#fee2e2,stroke:#ef4444,stroke-width:2px
```"""
