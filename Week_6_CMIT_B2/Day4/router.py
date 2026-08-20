"""
router.py
---------
Task 2: intent-classification router node.

Two implementations are provided:

1. `classify_rule_based` -- a lightweight, dependency-free keyword/regex
   classifier. This is what's wired into the graph by default so the whole
   project runs offline/deterministically (useful for grading + CI).

2. `classify_llm` -- a small LLM call with structured output (Pydantic
   schema via `.with_structured_output`), which is what you'd actually run
   in production for better generalisation to phrasing the rules don't
   cover. Toggle with the USE_LLM_ROUTER env var.

Both return the same `RouterDecision` shape so `router_node` doesn't care
which one is active.
"""

from __future__ import annotations

import os
import re
from typing import Optional

from pydantic import BaseModel, Field

from entity_resolution import TEAM_ALIASES, resolve_team
from state import AFLState, Intent


class RouterDecision(BaseModel):
    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0)
    team_a: Optional[str] = None
    team_b: Optional[str] = None
    player: Optional[str] = None
    round_or_date: Optional[str] = None
    stat_type: Optional[str] = None


# ---------------------------------------------------------------------------
# Rule-based classifier (default, offline-friendly)
# ---------------------------------------------------------------------------

_OFF_TOPIC_HINTS = [
    "weather", "recipe", "capital of", "stock price", "movie", "python code",
    "who is the president", "translate", "joke",
]

_PREDICTION_PLAYER_HINTS = [
    "top score", "top-score", "top scorer", "who will top", "best player",
    "most disposals will", "leading goalkicker",
]

_PREDICTION_MATCH_HINTS = [
    "who will win", "will beat", "who wins", "predict", "chances of winning",
    "chances of", "will win", "beat the", " vs ", " v ", "who's going to win",
    "winning next round", "winning this week",
]

_RETRIEVAL_HINTS = [
    "stats last", "what were", "how many disposals", "how many goals did",
    "last round", "average this season", "how many tackles",
    "what was the score", "ladder position",
]

_UNSUPPORTED_HINTS = [
    "margin will be", "by how many points", "exact score", "predict the score",
    "injury list next season", "predict the weather", "final score",
    "exact margin", "by how much",
]


_LEADING_PHRASES = [
    r"who('?s| is| will)? (going to )?win(s)?( the game between)?",
    r"predict(ed|ing)? the winner of",
    r"predict",
    r"what are the chances of",
    r"chances of",
]


def _strip_leading_phrase(text: str) -> str:
    for pattern in _LEADING_PHRASES:
        text = re.sub(rf"^\s*{pattern}\s*", "", text, flags=re.I)
    return text.strip()


_TRAILING_PHRASES = [
    r"\s+this (week|weekend|round)\b.*",
    r"\s+next (week|weekend|round)\b.*",
    r"\s+(the )?game\b.*",
    r"[?.!]+$",
]


def _strip_trailing_phrase(text: str) -> str:
    for pattern in _TRAILING_PHRASES:
        text = re.sub(pattern, "", text, flags=re.I)
    return text.strip()


def _extract_teams(text: str) -> tuple[Optional[str], Optional[str]]:
    """Small heuristic: strip leading/trailing filler, then split on 'vs'/'v'/'beat'."""
    cleaned = _strip_leading_phrase(text)

    m = re.search(r"(.+?)\s+(?:vs\.?|v\.?)\s+(.+)", cleaned, re.I)
    if m:
        team_a, team_b = m.group(1).strip(), m.group(2).strip()
        return team_a, _strip_trailing_phrase(team_b)

    m = re.search(
        r"(?:will|can)\s+(?:the\s+)?(.+?)\s+beat\s+(?:the\s+)?(.+?)(?:\s+this|\s+next|\?|$)",
        cleaned, re.I,
    )
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return None, None


def _extract_single_team(text: str) -> Optional[str]:
    """Find the longest known team-alias substring mentioned in free text."""
    hits = [alias for alias in TEAM_ALIASES if alias in text]
    if not hits:
        return None
    return max(hits, key=len)  # prefer "port adelaide" over "port", etc.


def classify_rule_based(query: str) -> RouterDecision:
    q = query.lower().strip()

    if any(h in q for h in _OFF_TOPIC_HINTS):
        return RouterDecision(intent="off_topic", confidence=0.9)

    if any(h in q for h in _UNSUPPORTED_HINTS):
        return RouterDecision(intent="unsupported", confidence=0.75)

    if any(h in q for h in _PREDICTION_PLAYER_HINTS):
        team_a = _extract_single_team(q)
        return RouterDecision(intent="prediction_player", confidence=0.8, team_a=team_a)

    if any(h in q for h in _PREDICTION_MATCH_HINTS):
        team_a, team_b = _extract_teams(q)
        when = "this week" if "this week" in q or "this weekend" in q else (
            "next round" if "next round" in q else None
        )
        return RouterDecision(
            intent="prediction_match", confidence=0.8,
            team_a=team_a, team_b=team_b, round_or_date=when,
        )

    if any(h in q for h in _RETRIEVAL_HINTS):
        if " vs " in q or " v " in q:
            team_a, _ = _extract_teams(q)
        else:
            team_a = _extract_single_team(q)
        when = "last round" if "last round" in q else None
        return RouterDecision(intent="retrieval", confidence=0.75, team_a=team_a, round_or_date=when)

    # AFL-ish default: treat as factual if it mentions a known team/league term,
    # otherwise off_topic.
    afl_terms = ["afl", "footy", "grand final", "brownlow", "ladder", "premiership"]
    if any(t in q for t in afl_terms) or resolve_team(q.split()[0] if q.split() else "")[0]:
        return RouterDecision(intent="factual", confidence=0.55)

    return RouterDecision(intent="off_topic", confidence=0.5)


# ---------------------------------------------------------------------------
# LLM-based classifier (production path)
# ---------------------------------------------------------------------------

def classify_llm(query: str, history_summary: str = "") -> RouterDecision:
    """
    Structured-output LLM router. Requires ANTHROPIC_API_KEY in the
    environment. Not exercised by the offline tests in this repo, but this
    is the version to actually deploy -- it generalises far better than the
    keyword rules above to novel phrasing.
    """
    from langchain_anthropic import ChatAnthropic  # local import: optional dep

    llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)
    structured_llm = llm.with_structured_output(RouterDecision)

    system = (
        "You are an intent router for an AFL (Australian Football League) assistant. "
        "Classify the user's query into exactly one intent:\n"
        "- factual: general AFL knowledge/history/rules question\n"
        "- retrieval: asking for a specific stat that already happened (e.g. last round's numbers)\n"
        "- prediction_match: asking who will win a future match\n"
        "- prediction_player: asking who will top-score / best player in a future match\n"
        "- unsupported: an AFL prediction question outside modeled scope (e.g. exact final score/margin)\n"
        "- off_topic: not about AFL at all\n\n"
        "Also extract any team names, player names, and time references "
        "(e.g. 'this week', 'last round') mentioned, verbatim as written by the user "
        "(do not normalize team names yourself -- that happens downstream)."
    )
    return structured_llm.invoke(
        [("system", system), ("human", f"Conversation so far: {history_summary}\nQuery: {query}")]
    )


def classify(query: str, history_summary: str = "") -> RouterDecision:
    if os.environ.get("USE_LLM_ROUTER") == "1":
        return classify_llm(query, history_summary)
    return classify_rule_based(query)


# ---------------------------------------------------------------------------
# Graph node
# ---------------------------------------------------------------------------

def router_node(state: AFLState) -> dict:
    query = state["user_query"]
    decision = classify(query)

    entities = dict(state.get("entities") or {})
    entities.update({
        "team_a_raw": decision.team_a,
        "team_b_raw": decision.team_b,
        "player_raw": decision.player,
        "round_or_date_raw": decision.round_or_date,
        "stat_type": decision.stat_type,
    })

    trace = list(state.get("trace") or [])
    trace.append(
        f"[router] intent={decision.intent} confidence={decision.confidence:.2f} "
        f"team_a_raw={decision.team_a!r} team_b_raw={decision.team_b!r}"
    )

    return {
        "intent": decision.intent,
        "router_confidence": decision.confidence,
        "entities": entities,
        "trace": trace,
    }


def route_from_intent(state: AFLState) -> str:
    """Conditional-edge function: maps intent -> next node name."""
    return {
        "factual": "direct_answer",
        "retrieval": "retrieval_tool",
        "prediction_match": "prediction_tool",
        "prediction_player": "prediction_tool",
        "off_topic": "refusal",
        "unsupported": "fallback",
    }[state["intent"]]
