from typing import Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
from langchain_core.tools import tool

from database import query_properties_sql, get_db_connection, get_agent_by_city
from appointment_manager import appointment_manager
from email_service import email_service, DEFAULT_MANAGER_EMAIL
from calendar_service import calendar_service
from crm_store import crm_store
from rag_engine import RAGEngine

# Initialize shared RAG engine
rag_engine = RAGEngine(chunk_size=128)

@tool
def search_property_tool(
    city: Optional[str] = None,
    area: Optional[str] = None,
    max_price_pkr: Optional[float] = None,
    bedrooms: Optional[int] = None,
    purpose: Optional[str] = None,
    property_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Task 3 & 4 Tool: Search Property Tool.
    Queries verified SQL database for AVAILABLE properties matching client criteria.
    Enforces Task 4 Validation: Never recommends unavailable properties (status = AVAILABLE).
    """
    results = query_properties_sql(
        city=city,
        area=area,
        max_price_pkr=max_price_pkr,
        bedrooms=bedrooms,
        purpose=purpose,
        property_type=property_type,
        limit=5
    )
    # Task 4 Guardrail: Filter to ensure status is AVAILABLE
    available_results = [p for p in results if p.get("status", "AVAILABLE") == "AVAILABLE"]
    return available_results

@tool
def availability_checker_tool(
    date_str: str,
    time_str: str,
    city: str = "Lahore"
) -> Dict[str, Any]:
    """
    Task 3 & 4 Tool: Availability Checker Tool.
    Verifies if a requested appointment date and time slot is available.
    If unavailable, dynamically returns alternative available slots on the same date.
    """
    avail = appointment_manager.check_availability(date_str, time_str)
    if avail["is_available"]:
        return {
            "date": date_str,
            "time": time_str,
            "city": city,
            "is_available": True,
            "conflict_reason": None,
            "available_slots": []
        }
    else:
        alt_slots = appointment_manager.get_available_slots(date_str)
        alt_slots = [s for s in alt_slots if s.lower() != time_str.lower()]
        return {
            "date": date_str,
            "time": time_str,
            "city": city,
            "is_available": False,
            "conflict_reason": f"Slot {date_str} at {time_str} is already booked.",
            "available_slots": alt_slots[:3]
        }

@tool
def calendar_tool(
    client_name: str,
    client_email: str,
    employee_name: str,
    property_title: str,
    date_str: str,
    time_str: str,
    notes: str = ""
) -> Dict[str, Any]:
    """
    Task 3 Tool: Calendar Tool.
    Creates Google Calendar event for site visits using client's actual email.
    """
    return calendar_service.create_event(
        client_name=client_name,
        client_email=client_email,
        client_phone="Email Priority Client",
        employee_name=employee_name,
        employee_email=DEFAULT_MANAGER_EMAIL,
        property_title=property_title,
        date_str=date_str,
        time_str=time_str,
        meeting_notes=notes
    )

@tool
def email_tool(
    action_type: str,
    client_name: str,
    client_email: str,
    employee_name: str,
    property_title: str,
    appointment_date: str,
    appointment_time: str,
    notes: str = ""
) -> Dict[str, Any]:
    """
    Task 3 Tool: Email Tool.
    Dispatches confirmation email directly to client_email and alert to manager.
    """
    return email_service.send_appointment_notification(
        action_type=action_type,
        client_name=client_name,
        client_email=client_email,
        client_phone="Email Priority Client",
        employee_name=employee_name,
        employee_email=DEFAULT_MANAGER_EMAIL,
        property_title=property_title,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        requirements_summary=notes
    )

@tool
def crm_tool(
    session_id: str,
    client_email: str,
    raw_transcript: str,
    agent_response: str,
    latency_sec: float = 0.0,
    appointment_id: Optional[int] = None,
    action_type: str = "INTERACTION"
) -> Dict[str, Any]:
    """
    Task 3 Tool: CRM Store Logging Tool.
    Logs call transcripts, preference profiles, and appointment history.
    """
    target_email = client_email if (client_email and "@" in client_email) else "client@realestatehub.pk"
    crm_store.log_transcript(
        session_id=session_id,
        client_email=target_email,
        raw_transcript=raw_transcript,
        normalized_transcript=raw_transcript,
        agent_response=agent_response,
        latency_sec=latency_sec
    )
    if appointment_id:
        crm_store.log_appointment_history(
            appointment_id=appointment_id,
            client_email=target_email,
            action_type=action_type,
            details=f"Appointment {action_type} logged via LangGraph Agent."
        )
    return {"status": "SUCCESS", "logged_session": session_id}

@tool
def rag_search_tool(query: str) -> str:
    """
    Task 3 Tool: RAG Search Tool.
    Searches Knowledge Base vector embeddings for legal NOCs, payment plans, and DHA transfer procedures.
    """
    return rag_engine.get_context_str(query, top_k=2)
