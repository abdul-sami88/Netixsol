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

from entity_resolution import resolve_team
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
    "chances of", "will win", "beat ", " vs ", " v ", "who's going to win",
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


def _extract_single_team(q: str) -> Optional[str]:
    """Find a raw team-name substring in free text using the REAL canonical
    team list from ai_chat_afl (so this stays consistent with the actual
    resolver -- no hardcoded alias dict to maintain separately)."""
    try:
        from ai_chat_afl import _canonical_teams
        canonical = _canonical_teams()
    except Exception:
        return None

    q_cf = q.casefold()
    candidates: list[tuple[int, str]] = []
    for name in canonical:
        name_cf = name.casefold()
        nickname = name_cf.split()[-1].rstrip("s")
        first_word = name_cf.split()[0]
        for token in (name_cf, nickname, first_word):
            if token and re.search(rf"\b{re.escape(token)}\b", q_cf):
                candidates.append((len(token), token))
    if not candidates:
        return None
    candidates.sort(reverse=True)  # prefer the longest / most specific match
    return candidates[0][1]


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
    afl_terms = [
        "afl", "footy", "grand final", "brownlow", "ladder", "premiership",
        "holding the ball", "high tackle", "free kick", "umpire", "ruck",
        "50m penalty", "50 metre", "out of bounds", "interchange", "spoil",
        "mark", "behind", "quarter", "coach", "australian football", "australian rules",
    ]
    if any(t in q for t in afl_terms) or _extract_single_team(q):
        return RouterDecision(intent="factual", confidence=0.55)

    return RouterDecision(intent="off_topic", confidence=0.5)


# ---------------------------------------------------------------------------
# LLM-based classifier (production path)
# ---------------------------------------------------------------------------

def classify_llm(query: str, history_summary: str = "") -> RouterDecision:
    """
    Structured-output LLM router using Gemini 3.5 Flash Lite (same provider
    already used by ai_chat_afl.py's chat agent, so only one API key
    -- GEMINI_API_KEY -- is needed for the whole project). Not exercised by
    the offline tests in this repo (they use the deterministic rule-based
    classifier), but this is the version to actually deploy -- it
    generalises far better than the keyword rules above to novel phrasing
    and to coreference across turns ("their stats" -> resolves via
    history_summary).
    """
    import os

    from langchain_google_genai import ChatGoogleGenerativeAI  # local import: optional dep

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0,
    )
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
        "(do not normalize team names yourself -- that happens downstream). "
        "Use the conversation history to resolve pronouns/references like "
        "'their', 'that team', or 'his' back to a concrete team/player name."
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

    # Reset per-turn volatile fields explicitly. Without this, a multi-turn
    # conversation on the same thread_id would leak a PREVIOUS turn's
    # tool_result/validation_status into this turn's state (the checkpointer
    # persists state across invocations on a thread; fields this turn's
    # nodes don't touch simply keep their last value otherwise) -- caught by
    # the Task 5 multi-turn e2e test, where a prediction's tool_result was
    # bleeding into the *next* turn's unrelated retrieval question.
    entities = dict(state.get("entities") or {})
    entities.update({
        "team_a_raw": decision.team_a,
        "team_b_raw": decision.team_b,
        "player_raw": decision.player,
        "round_or_date_raw": decision.round_or_date,
        "stat_type": decision.stat_type,
        "unresolved_reason": None,
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
        "tool_result": None,
        "validation_status": None,
        "clarification_question": None,
        "final_response": None,
        "trace": trace,
    }


def route_from_intent(state: AFLState) -> str:
    """Conditional-edge function: maps intent -> next node name.

    factual / retrieval / off_topic all delegate to `chat_agent` (the real
    Day 3 ai_chat_afl agent), which already has its own retrieval tools,
    scope guardrails, and refusal wording -- no need to reimplement that
    here. Only prediction-shaped intents get routed to our new tool node,
    and only prediction-shaped-but-unsupported queries get the fallback.
    """
    return {
        "factual": "chat_agent",
        "retrieval": "chat_agent",
        "prediction_match": "prediction_tool",
        "prediction_player": "prediction_tool",
        "off_topic": "chat_agent",
        "unsupported": "fallback",
    }[state["intent"]]
