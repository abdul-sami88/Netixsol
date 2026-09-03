import time
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from langgraph_agent.state import AgentState
from langgraph_agent.tools import (
    search_property_tool,
    availability_checker_tool,
    calendar_tool,
    email_tool,
    crm_tool,
    rag_search_tool
)
from llm_client import llm_client
from system_prompt import get_system_prompt_with_context
from appointment_manager import appointment_manager
from email_service import DEFAULT_MANAGER_EMAIL

def _create_trace_event(node_name: str, intent: Optional[str], details: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to construct annotated execution trace events for Task 5."""
    return {
        "node": node_name,
        "timestamp": datetime.now().isoformat(),
        "intent": intent,
        "details": details
    }

# ==========================================
# TASK 2 & TASK 4: GRAPH NODES DEFINITIONS
# ==========================================

def intent_detection_node(state: AgentState) -> Dict[str, Any]:
    """
    Task 2 Node: Intent Detection Node.
    Analyzes last user message and updates state.intent.
    """
    user_msg = state["messages"][-1]["content"] if state["messages"] else ""
    text = user_msg.lower()

    # Intent Classification Rules
    intent = "recommendation"
    if any(w in text for w in ["salam", "assalam", "hello", "hi", "kaun", "kon"]):
        intent = "greeting"
    elif any(w in text for w in ["bye", "khuda hafiz", "allah hafiz", "shukriya", "thanks"]):
        intent = "goodbye"
    elif any(w in text for w in ["reschedule", "time change", "postpone"]):
        intent = "reschedule"
    elif any(w in text for w in ["cancel", "mansookh"]):
        intent = "cancel"
    elif any(w in text for w in ["book", "booking", "appointment", "visit", "schedule", "meeting", "email", "mail", "بک", "وزٹ", "سائیڈ", "سکیجول", "ای میل"]):
        intent = "booking"
    elif any(w in text for w in ["noc", "transfer", "installment", "document", "legal", "dha procedure"]):
        intent = "rag"
    
    # Extract City & Budget preferences
    prefs = dict(state.get("property_preferences", {}))
    if "lahore" in text or "لاہور" in text:
        prefs["city"] = "Lahore"
    elif "islamabad" in text or "اسلام آباد" in text:
        prefs["city"] = "Islamabad"
    elif "karachi" in text or "کراچی" in text:
        prefs["city"] = "Karachi"

    if "buy" in text or "khareedna" in text or "sale" in text:
        prefs["purpose"] = "Sale"
    elif "rent" in text or "kiraya" in text:
        prefs["purpose"] = "Rent"

    # Extract spoken email if present
    profile = dict(state.get("user_profile", {}))
    m_email = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', user_msg)
    if m_email:
        profile["client_email"] = m_email.group(0)

    trace = [_create_trace_event("intent_detection_node", intent, {
        "user_message": user_msg,
        "detected_intent": intent,
        "extracted_city": prefs.get("city"),
        "extracted_purpose": prefs.get("purpose")
    })]

    return {
        "intent": intent,
        "property_preferences": prefs,
        "user_profile": profile,
        "execution_trace": trace
    }

def greeting_node(state: AgentState) -> Dict[str, Any]:
    """Task 2 Node: Greeting Node."""
    user_msg = state["messages"][-1]["content"] if state["messages"] else ""
    reply = "Assalam-o-Alaikum sir! RealEstate Hub se Zara baat kar rahi hoon. Main aap ki kis tarah madad kar sakti hoon? Aap kaun se city (Lahore, Islamabad, ya Karachi) aur budget mein property dekh rahe hain?"
    
    trace = [_create_trace_event("greeting_node", state["intent"], {"greeting_response": reply})]
    return {
        "messages": [{"role": "assistant", "content": reply}],
        "execution_trace": trace
    }

def rag_search_node(state: AgentState) -> Dict[str, Any]:
    """Task 2 Node: RAG Search Node."""
    user_msg = state["messages"][-1]["content"] if state["messages"] else ""
    rag_ctx = rag_search_tool.invoke({"query": user_msg})
    
    sys_prompt = get_system_prompt_with_context(rag_ctx)
    reply = llm_client.generate_response(state["messages"], sys_prompt)
    
    trace = [_create_trace_event("rag_search_node", state["intent"], {"rag_context_length": len(rag_ctx)})]
    return {
        "messages": [{"role": "assistant", "content": reply}],
        "tool_outputs": {"rag_context": rag_ctx},
        "execution_trace": trace
    }

def recommendation_node(state: AgentState) -> Dict[str, Any]:
    """Task 2 & 4 Node: Recommendation Node with Guardrails."""
    user_msg = state["messages"][-1]["content"] if state["messages"] else ""
    prefs = state.get("property_preferences", {})
    city = prefs.get("city") or "Lahore"
    
    # Task 4 Guardrail: Never recommend unavailable properties
    available_props = search_property_tool.invoke({
        "city": city,
        "purpose": prefs.get("purpose")
    })
    
    formatted_props = ""
    if available_props:
        formatted_props = "\n".join([f"- {p['title']} ({p['city']}): PKR {p['price_pkr']:,} | {p['bedrooms']} Beds | Area: {p['area']}" for p in available_props])
    else:
        formatted_props = "No direct matching properties available right now."

    sys_prompt = get_system_prompt_with_context(formatted_props)
    reply = llm_client.generate_response(state["messages"], sys_prompt)
    
    trace = [_create_trace_event("recommendation_node", state["intent"], {
        "properties_count": len(available_props),
        "city": city
    })]
    return {
        "messages": [{"role": "assistant", "content": reply}],
        "tool_outputs": {"recommended_properties": available_props},
        "execution_trace": trace
    }

def availability_check_node(state: AgentState) -> Dict[str, Any]:
    """
    Task 2 & 4 Node: Availability Check Node.
    Task 4 Validation: Never book unavailable slots.
    """
    app_status = dict(state.get("appointment_status", {}))
    date_str = app_status.get("date") or "Tomorrow"
    time_str = app_status.get("time") or "11:00 AM"
    
    avail_res = availability_checker_tool.invoke({"date_str": date_str, "time_str": time_str})
    app_status["is_available"] = avail_res["is_available"]
    
    trace = [_create_trace_event("availability_check_node", state["intent"], avail_res)]
    return {
        "appointment_status": app_status,
        "execution_trace": trace
    }

def booking_node(state: AgentState) -> Dict[str, Any]:
    """Task 2 Node: Booking Node."""
    user_msg = state["messages"][-1]["content"] if state["messages"] else ""
    profile = state.get("user_profile", {})
    client_email = profile.get("client_email") or ""
    
    app_status = dict(state.get("appointment_status", {}))
    app_date = app_status.get("date") or "Tomorrow"
    app_time = app_status.get("time") or "11:00 AM"

    # Execute appointment booking
    res = appointment_manager.book_appointment(
        session_id=profile.get("session_id", "langgraph_session"),
        client_name=profile.get("client_name") or "Valued Client",
        client_email=client_email,
        city=state.get("property_preferences", {}).get("city") or "Lahore",
        property_title="Real Estate Site Visit Consultation",
        appointment_date=app_date,
        appointment_time=app_time
    )
    
    if res.get("success"):
        app_status["status"] = "BOOKED"
        app_status["appointment_id"] = res.get("appointment_id")
        reply = f"Bohat shukriya sir! Main ne aap ke email ({client_email}) par confirmation mail bhej di hai aur Google Calendar invite schedule kar diya hai."
    elif res.get("status") == "SLOT_UNAVAILABLE":
        alt_str = ", ".join(res.get("available_slots", [])[:3])
        reply = f"Sir {app_time} busy hai, lekin usi din hamare paas {alt_str} available hain. Kya main in mein se kisi par book kar doon?"
    else:
        reply = "Ji bilkul sir! Booking ke liye please apna email address aur preferred time confirm karwa dein."
    
    trace = [_create_trace_event("booking_node", state["intent"], {"booking_result": res})]
    return {
        "messages": [{"role": "assistant", "content": reply}],
        "appointment_status": app_status,
        "tool_outputs": {"booking_res": res},
        "execution_trace": trace
    }

def rescheduling_node(state: AgentState) -> Dict[str, Any]:
    """Task 2 Node: Rescheduling Node."""
    profile = state.get("user_profile", {})
    client_email = profile.get("client_email")
    if client_email:
        existing = appointment_manager.get_latest_appointment_by_email(client_email)
        if existing:
            reply = f"Ji sir! Aap ki {existing['property_title']} ki appointment find ho gayi hai. Kis new date aur time par reschedule karna chahte hain?"
        else:
            reply = f"Sir {client_email} par koi active appointment nahi mili. Kya aap new appointment schedule karna chahte hain?"
    else:
        reply = "Appointment reschedule karne ke liye, please apna registered email address batayein sir?"
        
    trace = [_create_trace_event("rescheduling_node", state["intent"], {"rescheduled": True})]
    return {
        "messages": [{"role": "assistant", "content": reply}],
        "execution_trace": trace
    }

def cancellation_node(state: AgentState) -> Dict[str, Any]:
    """Task 2 Node: Cancellation Node."""
    profile = state.get("user_profile", {})
    client_email = profile.get("client_email")
    if client_email:
        existing = appointment_manager.get_latest_appointment_by_email(client_email)
        if existing:
            appointment_manager.cancel_appointment(existing["id"])
            reply = f"Aap ki appointment cancel kar di gayi hai aur update confirmation email {client_email} par bhej di gayi hai."
        else:
            reply = f"Sir {client_email} par koi active appointment nahi mili."
    else:
        reply = "Appointment cancel karne ke liye, please apna registered email address batayein sir?"
        
    trace = [_create_trace_event("cancellation_node", state["intent"], {"cancelled": True})]
    return {
        "messages": [{"role": "assistant", "content": reply}],
        "execution_trace": trace
    }

def email_node(state: AgentState) -> Dict[str, Any]:
    """Task 2 Node: Email Dispatch Node."""
    profile = state.get("user_profile", {})
    client_email = profile.get("client_email") or ""
    tool_outs = state.get("tool_outputs", {})
    
    # If booking/cancellation/reschedule node already dispatched emails, avoid duplicate dispatch
    if tool_outs.get("booking_res", {}).get("success") or tool_outs.get("cancellation_res", {}).get("success") or tool_outs.get("reschedule_res", {}).get("success"):
        email_res = {"success": True, "status": "ALREADY_DISPATCHED", "client_email": client_email}
    elif client_email:
        app_status = state.get("appointment_status", {})
        email_res = email_tool.invoke({
            "action_type": "BOOKING",
            "client_name": profile.get("client_name") or "Valued Client",
            "client_email": client_email,
            "employee_name": "Zara",
            "property_title": "Real Estate Consultation",
            "appointment_date": app_status.get("date") or "Tomorrow",
            "appointment_time": app_status.get("time") or "11:00 AM"
        })
    else:
        email_res = {"success": False, "error": "No client email provided."}
    
    trace = [_create_trace_event("email_node", state["intent"], {"email_result": email_res})]
    return {
        "tool_outputs": {"email_res": email_res},
        "execution_trace": trace
    }

def clarification_node(state: AgentState) -> Dict[str, Any]:
    """
    Task 2 & 4 Node: Clarification Node.
    Task 4 Validation: Ask clarification instead of guessing.
    """
    reply = "Ji bilkul sir! Main aap ki site visit schedule kar deti hoon. Aap ka naam, email address, aur preferred date & time slot kya hai sir?"
    trace = [_create_trace_event("clarification_node", state["intent"], {"asked_clarification": True})]
    return {
        "messages": [{"role": "assistant", "content": reply}],
        "execution_trace": trace
    }

def goodbye_node(state: AgentState) -> Dict[str, Any]:
    """Task 2 Node: Goodbye Node."""
    reply = "Bohat shukriya sir! RealEstate Hub se rabta karne ka shukriya. Apna khayal rakhyega, Allah Hafiz!"
    trace = [_create_trace_event("goodbye_node", state["intent"], {"closed_session": True})]
    return {
        "messages": [{"role": "assistant", "content": reply}],
        "execution_trace": trace
    }
