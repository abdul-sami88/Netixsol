"""
LangGraph Shared State Schema for City Care Clinics.
Maintains state across all specialist agents:
- Patient Profile & Long-Term Memory
- Intake Form & Conversational State
- Triage Urgency Level & Red Flags
- Verified EHR Records & Lab Observations
- Pre-Visit Clinical SOAP Note
- Appointment Booking Details
- Doctor Draft Prescription & Safety Review
- Human-in-the-Loop Doctor Approval Gate
- Follow-up Care Plan & Notifications
- Comprehensive Node Transition Audit History
"""

from typing import Dict, Any, List, Optional, Annotated
from typing_extensions import TypedDict
import operator


def merge_lists(left: List[Any], right: List[Any]) -> List[Any]:
    """Appends new items to existing list without duplicates where appropriate."""
    if not left:
        return right or []
    if not right:
        return left or []
    return left + right


def merge_node_name(left: str, right: str) -> str:
    """Merges current_node in parallel branches without conflict."""
    if left and right and left != right:
        return f"{left}+{right}"
    return right or left or ""



class ClinicAgentState(TypedDict, total=False):
    # 1. Patient & Session Context
    patient_id: Optional[str]
    patient_name: str
    patient_profile: Optional[Dict[str, Any]]
    session_id: str
    preferred_language: str # "UrduLish" or "English"

    # 2. Dialogue & Conversation
    user_message: str
    messages: Annotated[List[Dict[str, str]], merge_lists]
    final_response: Optional[str]

    # 3. Intake State
    intake_form: Optional[Dict[str, Any]]
    is_intake_complete: bool

    # 4. Triage State
    triage_level: Optional[str] # "EMERGENCY", "URGENT", "ROUTINE"
    triage_result: Optional[Dict[str, Any]]
    is_emergency: bool

    # 5. Records & Clinical Summary
    patient_history: Optional[List[str]]
    lab_results: Optional[List[Dict[str, Any]]]
    clinical_summary: Optional[Dict[str, Any]] # Pre-visit SOAP Note

    # 6. Scheduling State
    appointment: Optional[Dict[str, Any]]
    doctor_preference: Optional[Dict[str, Any]]

    # 7. Prescription & Safety
    doctor_draft_prescription: Optional[List[Dict[str, Any]]]
    prescription_safety_review: Optional[Dict[str, Any]]

    # 8. Human-in-the-Loop (Doctor Approval Gate)
    requires_doctor_approval: bool
    approval_type: Optional[str] # "LAB_EXPLANATION", "PRESCRIPTION", "LOW_CONFIDENCE_TRIAGE"
    approval_id: Optional[str]
    approval_payload: Optional[Dict[str, Any]]
    doctor_decision: Optional[Dict[str, Any]] # {"action": "APPROVE"|"EDIT"|"REJECT", "doctor_name": str, "notes": str, "edited_payload": ...}

    # 9. Follow-up Care Plan
    follow_up_plan: Optional[Dict[str, Any]]

    # 10. Audit Logging & Routing
    node_history: Annotated[List[str], merge_lists]
    current_node: Annotated[str, merge_node_name]
    next_node: Optional[str]
    errors: Annotated[List[Dict[str, Any]], merge_lists]
