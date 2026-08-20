"""
graph.py
--------
Task 1 (sketch) realised as an actual compiled LangGraph.

    START
      |
      v
   router  ------------------------------------------------------.
      |                 |                   |                    |
      | factual         | retrieval         | prediction_*       | off_topic/unsupported
      v                 v                   v                    v
 direct_answer     retrieval_tool     prediction_tool      refusal / fallback
      |                 |                   |                    |
      |                 v                   v                    |
      |            validation ---------------                    |
      |               |     \\__needs_clarification__> clarification
      |               |ok                                        |
      |               v                                          |
      '---------> response_formatter <---------------------------'
                        |
                        v
                       END

Why explicit LangGraph routing instead of one free-form agent?
- Predictions MUST always carry a probability + disclaimer. A single agent
  deciding tool-by-tool can forget the disclaimer on some turns; a router
  that always funnels prediction_* intents through response_formatter's
  prediction branch makes that a structural guarantee, not a prompting hope.
- Entity resolution failures need a *deterministic* clarification loop
  rather than an agent creatively guessing a team name.
- Debuggability: state.trace gives an exact node-by-node path per request,
  which a single ReAct-style agent's freeform tool-call log doesn't give
  you as cleanly (Task 5 log/annotate requirement).
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from nodes import (
    clarification_node,
    direct_answer_node,
    fallback_node,
    prediction_node,
    refusal_node,
    response_formatter_node,
    retrieval_node,
    route_after_validation,
    validation_node,
)
from router import route_from_intent, router_node
from state import AFLState


def build_graph(with_memory: bool = True):
    g = StateGraph(AFLState)

    g.add_node("router", router_node)
    g.add_node("direct_answer", direct_answer_node)
    g.add_node("retrieval_tool", retrieval_node)
    g.add_node("prediction_tool", prediction_node)
    g.add_node("refusal", refusal_node)
    g.add_node("fallback", fallback_node)
    g.add_node("validation", validation_node)
    g.add_node("clarification", clarification_node)
    g.add_node("response_formatter", response_formatter_node)

    g.add_edge(START, "router")

    g.add_conditional_edges(
        "router",
        route_from_intent,
        {
            "direct_answer": "direct_answer",
            "retrieval_tool": "retrieval_tool",
            "prediction_tool": "prediction_tool",
            "refusal": "refusal",
            "fallback": "fallback",
        },
    )

    # direct_answer / refusal / fallback go straight to formatting or END
    g.add_edge("direct_answer", "response_formatter")
    g.add_edge("refusal", END)
    g.add_edge("fallback", END)

    # tool nodes are validated before formatting
    g.add_edge("retrieval_tool", "validation")
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
    out = run_query(app, "will the Pies beat the Cats this week")
    print(out["final_response"])
    print("\n--- trace ---")
    for line in out["trace"]:
        print(line)
