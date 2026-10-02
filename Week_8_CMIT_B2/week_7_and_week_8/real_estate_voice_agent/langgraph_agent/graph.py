from typing import Dict, Any, Literal, Optional
# pyrefly: ignore [missing-import]
from langgraph.graph import StateGraph, START, END

from langgraph_agent.state import AgentState, create_initial_agent_state
from langgraph_agent.nodes import (
    intent_detection_node,
    greeting_node,
    rag_search_node,
    recommendation_node,
    availability_check_node,
    booking_node,
    rescheduling_node,
    cancellation_node,
    email_node,
    clarification_node,
    goodbye_node
)
from langgraph_agent.tracer import tracer

# ==========================================
# TASK 2: GRAPH ROUTING LOGIC
# ==========================================

def route_by_intent(state: AgentState) -> Literal["greeting", "goodbye", "rag", "rescheduling", "cancellation", "availability_check", "recommendation"]:
    intent = state.get("intent", "recommendation")
    if intent == "greeting":
        return "greeting"
    elif intent == "goodbye":
        return "goodbye"
    elif intent == "rag":
        return "rag"
    elif intent == "reschedule":
        return "rescheduling"
    elif intent == "cancel":
        return "cancellation"
    elif intent == "booking":
        return "availability_check"
    else:
        return "recommendation"

def route_after_availability(state: AgentState) -> Literal["booking", "clarification"]:
    app_status = state.get("appointment_status", {})
    if app_status.get("is_available", True):
        return "booking"
    else:
        return "clarification"

# ==========================================
# GRAPH ASSEMBLY & COMPILATION
# ==========================================

builder = StateGraph(AgentState)

# Add Nodes
builder.add_node("intent_detection", intent_detection_node)
builder.add_node("greeting", greeting_node)
builder.add_node("rag", rag_search_node)
builder.add_node("recommendation", recommendation_node)
builder.add_node("availability_check", availability_check_node)
builder.add_node("booking", booking_node)
builder.add_node("rescheduling", rescheduling_node)
builder.add_node("cancellation", cancellation_node)
builder.add_node("email", email_node)
builder.add_node("clarification", clarification_node)
builder.add_node("goodbye", goodbye_node)

# Add Edges
builder.add_edge(START, "intent_detection")

builder.add_conditional_edges(
    "intent_detection",
    route_by_intent,
    {
        "greeting": "greeting",
        "goodbye": "goodbye",
        "rag": "rag",
        "rescheduling": "rescheduling",
        "cancellation": "cancellation",
        "availability_check": "availability_check",
        "recommendation": "recommendation"
    }
)

builder.add_conditional_edges(
    "availability_check",
    route_after_availability,
    {
        "booking": "booking",
        "clarification": "clarification"
    }
)

builder.add_edge("booking", "email")
builder.add_edge("rescheduling", "email")
builder.add_edge("cancellation", "email")

builder.add_edge("greeting", END)
builder.add_edge("goodbye", END)
builder.add_edge("rag", END)
builder.add_edge("recommendation", END)
builder.add_edge("email", END)
builder.add_edge("clarification", END)

# Compile Graph
langgraph_agent_app = builder.compile()

def run_agent_graph(session_id: str, user_message: str, current_state: Optional[AgentState] = None) -> Dict[str, Any]:
    """
    Main invocation entrypoint for the LangGraph AI Agent.
    Executes graph transitions, logs annotated traces, and returns final state + reply.
    """
    state = current_state or create_initial_agent_state(session_id)
    state["messages"].append({"role": "user", "content": user_message})

    # Run LangGraph pipeline
    final_state = langgraph_agent_app.invoke(state)

    # Log Execution Trace (Task 5)
    tracer.log_trace(session_id, final_state.get("execution_trace", []))

    # Extract final assistant reply
    assistant_msgs = [m["content"] for m in final_state.get("messages", []) if m["role"] == "assistant"]
    final_reply = assistant_msgs[-1] if assistant_msgs else "Ji bilkul sir! Main aap ki madad kar sakti hoon."

    return {
        "session_id": session_id,
        "reply": final_reply,
        "intent": final_state.get("intent"),
        "user_profile": final_state.get("user_profile"),
        "property_preferences": final_state.get("property_preferences"),
        "appointment_status": final_state.get("appointment_status"),
        "tool_outputs": final_state.get("tool_outputs"),
        "execution_trace": final_state.get("execution_trace", []),
        "raw_state": final_state
    }
