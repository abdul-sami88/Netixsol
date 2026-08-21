"""
state.py
--------
Task 1: State schema for the LangGraph AFL assistant.

Design notes
------------
- `messages` carries full conversation history (LangChain BaseMessage objects),
  so multi-turn context (Task 5 follow-ups) and clarification loops (Task 4)
  work naturally with LangGraph's checkpointer.
- `intent` / `entities` are populated by the router node and consumed by the
  tool nodes -- this is the explicit "contract" that makes routing debuggable
  (see justification in README.md, Task 1).
- `tool_result` is a generic envelope so retrieval_node and prediction_node
  can share the same validation_node logic (Task 4) without special-casing.
- `route_count` / `trace` exist purely for observability: every node appends
  a short breadcrumb so we can print an annotated state trace (Task 5)
  without instrumenting the graph externally.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

Intent = Literal[
    "factual",           # general AFL knowledge question -> direct_answer_node
    "retrieval",          # "what were X's stats last round" -> retrieval_node
    "prediction_match",   # "who will win X vs Y" -> prediction_node
    "prediction_player",  # "who will top-score" -> prediction_node
    "off_topic",          # not AFL related -> refusal_node
    "unsupported",        # AFL related but out of modeled scope -> fallback_node
]

ValidationStatus = Literal["ok", "error", "needs_clarification", "unsupported"]


class ToolResult(TypedDict, total=False):
    ok: bool
    kind: str                    # "match_prediction" | "player_prediction" | "stat_retrieval"
    data: dict[str, Any]
    error: Optional[str]
    grounding: list[str]         # short bullet explanations (Task 3: top 2-3 features)


class Entities(TypedDict, total=False):
    team_a_raw: Optional[str]
    team_b_raw: Optional[str]
    team_a: Optional[str]        # resolved to dataset's canonical key
    team_b: Optional[str]
    player_raw: Optional[str]
    player: Optional[str]
    round_or_date_raw: Optional[str]   # e.g. "this week", "last round"
    resolved_fixture_id: Optional[str]
    resolved_round: Optional[int]
    stat_type: Optional[str]     # e.g. "disposals", "goals", "top_scorer"
    unresolved_reason: Optional[str]   # why resolution failed, for clarification prompt


class AFLState(TypedDict):
    # ---- conversation ----
    messages: Annotated[list[BaseMessage], add_messages]
    user_query: str

    # ---- routing ----
    intent: Optional[Intent]
    router_confidence: Optional[float]

    # ---- extraction / resolution ----
    entities: Entities

    # ---- tool execution ----
    tool_result: Optional[ToolResult]

    # ---- validation / fallback ----
    validation_status: Optional[ValidationStatus]
    clarification_question: Optional[str]

    # ---- output ----
    final_response: Optional[str]

    # ---- observability (Task 5) ----
    trace: list[str]
