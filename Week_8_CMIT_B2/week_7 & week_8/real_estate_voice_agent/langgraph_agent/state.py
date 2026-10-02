from typing import TypedDict, Annotated, List, Dict, Any, Optional
import operator

class AgentState(TypedDict):
    """
    Task 1 — LangGraph State Design
    Comprehensive state schema tracking multi-turn conversation context, user profile,
    property preferences, budget, detected intent, tool outputs, appointment status,
    and annotated node execution traces.
    """
    messages: Annotated[List[Dict[str, str]], operator.add]
    user_profile: Dict[str, Any]
    property_preferences: Dict[str, Any]
    budget: Optional[float]
    intent: Optional[str]
    tool_outputs: Dict[str, Any]
    appointment_status: Dict[str, Any]
    execution_trace: Annotated[List[Dict[str, Any]], operator.add]

def create_initial_agent_state(session_id: str = "default_session") -> AgentState:
    """Helper to initialize a clean AgentState."""
    return {
        "messages": [],
        "user_profile": {
            "session_id": session_id,
            "client_name": None,
            "client_email": None,
            "client_phone": None,
            "preferred_city": None
        },
        "property_preferences": {
            "city": None,
            "area": None,
            "bedrooms": None,
            "property_type": None,
            "purpose": None
        },
        "budget": None,
        "intent": None,
        "tool_outputs": {},
        "appointment_status": {
            "status": None,
            "appointment_id": None,
            "date": None,
            "time": None,
            "is_available": True
        },
        "execution_trace": []
    }
