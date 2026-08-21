"""
graph.py
--------
Task 1 (sketch) realised as an actual compiled LangGraph, now wired to the
REAL Day 2 (predict.py) and Day 3 (ai_chat_afl.py) artifacts.

    START
      |
      v
   router
      |               |                              |
      | prediction_*   | factual/retrieval/off_topic  | unsupported
      v               v                              v
 prediction_tool   chat_agent (ai_chat_afl)        fallback
      |               |                              |
      v               |                              |
  validation           |                              |
   |ok    (needs_clarification branch)-> clarification    |
   v                                                    |
response_formatter <-----------------------------------'
      |
      v
     END

Why explicit LangGraph routing instead of one free-form agent handling
prediction too? The Day 3 agent (`ai_chat_afl.create_afl_agent`) has NO
prediction tools -- if a prediction-shaped query reached it directly, it
would either refuse (wrong -- we DO support predictions) or worse, try to
answer from "knowledge" and hallucinate a winner (very wrong for a stats
assistant whose whole premise is grounded numbers). The router's job is to
catch prediction-shaped queries BEFORE they reach that agent and force them
through a path that always attaches a probability + disclaimer. Everything
the Day 3 agent is already good at (retrieval, factual Q&A, off-topic
refusal, multi-turn memory) is left entirely to it rather than reimplemented.
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from nodes import (
    chat_agent_node,
    clarification_node,
    fallback_node,
    prediction_node,
    response_formatter_node,
    validation_node,
    route_after_validation,
)
from router import route_from_intent, router_node
from state import AFLState


def build_graph(with_memory: bool = True):
    g = StateGraph(AFLState)

    g.add_node("router", router_node)
    g.add_node("chat_agent", chat_agent_node)
    g.add_node("prediction_tool", prediction_node)
    g.add_node("fallback", fallback_node)
    g.add_node("validation", validation_node)
    g.add_node("clarification", clarification_node)
    g.add_node("response_formatter", response_formatter_node)

    g.add_edge(START, "router")

    g.add_conditional_edges(
        "router",
        route_from_intent,
        {
            "chat_agent": "chat_agent",
            "prediction_tool": "prediction_tool",
            "fallback": "fallback",
        },
    )

    # chat_agent already produces a complete final_response (incl. its own
    # off-topic refusal wording) -- still pass through response_formatter so
    # the trace/observability path is uniform across all branches.
    g.add_edge("chat_agent", "response_formatter")
    g.add_edge("fallback", END)

    g.add_edge("prediction_tool", "validation")

    g.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "response_formatter": "response_formatter",
            "clarification": "clarification",
            "fallback": "fallback",
        },
    )

    g.add_edge("clarification", END)
    g.add_edge("response_formatter", END)

    if with_memory:
        return g.compile(checkpointer=MemorySaver())
    return g.compile()


def run_query(app, query: str, thread_id: str = "default") -> dict:
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "user_query": query,
        "messages": [("human", query)],
        "entities": {},
        "trace": [],
    }
    return app.invoke(initial_state, config=config)


if __name__ == "__main__":
    app = build_graph()
    out = run_query(app, "will Melbourne Demons beat Richmond Tigers this week")
    print(out["final_response"])
    print("\n--- trace ---")
    for line in out["trace"]:
        print(line)
