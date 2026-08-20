"""
nodes.py
--------
Task 3 (tool nodes), Task 4 (validation + fallback + clarification).
"""

from __future__ import annotations

from day2_interface import get_player_stats, predict_match_winner, predict_top_player
from entity_resolution import resolve_fixture, resolve_team
from state import AFLState


def _push_trace(state: AFLState, msg: str) -> list[str]:
    trace = list(state.get("trace") or [])
    trace.append(msg)
    return trace


# ---------------------------------------------------------------------------
# Task 3: prediction tool node
# ---------------------------------------------------------------------------

def prediction_node(state: AFLState) -> dict:
    entities = dict(state.get("entities") or {})
    intent = state["intent"]
    trace = list(state.get("trace") or [])

    if intent == "prediction_match":
        team_a, reason_a = resolve_team(entities.get("team_a_raw"))
        team_b, reason_b = resolve_team(entities.get("team_b_raw"))
        entities["team_a"], entities["team_b"] = team_a, team_b

        if not team_a or not team_b:
            reason = reason_a or reason_b or "couldn't identify both teams"
            entities["unresolved_reason"] = reason
            trace.append(f"[prediction_tool] team resolution failed: {reason}")
            return {
                "entities": entities,
                "tool_result": {"ok": False, "kind": "match_prediction", "error": reason},
                "trace": trace,
            }

        fixture, fixture_reason = resolve_fixture(
            team_a, team_b, entities.get("round_or_date_raw")
        )
        if not fixture:
            entities["unresolved_reason"] = fixture_reason
            trace.append(f"[prediction_tool] fixture resolution failed: {fixture_reason}")
            return {
                "entities": entities,
                "tool_result": {"ok": False, "kind": "match_prediction", "error": fixture_reason},
                "trace": trace,
            }

        entities["resolved_fixture_id"] = fixture.fixture_id
        entities["resolved_round"] = fixture.round_number

        try:
            result = predict_match_winner(team_a, team_b, fixture_id=fixture.fixture_id)
            trace.append(
                f"[prediction_tool] predict_match_winner({team_a}, {team_b}) -> "
                f"winner={result['winner']} p={result['probability']}"
            )
            return {
                "entities": entities,
                "tool_result": {
                    "ok": True,
                    "kind": "match_prediction",
                    "data": {**result, "fixture": fixture.__dict__},
                    "grounding": result["top_features"],
                },
                "trace": trace,
            }
        except Exception as exc:  # never let a raw model exception leak to the user
            trace.append(f"[prediction_tool] EXCEPTION: {exc}")
            return {
                "entities": entities,
                "tool_result": {"ok": False, "kind": "match_prediction", "error": str(exc)},
                "trace": trace,
            }

    elif intent == "prediction_player":
        team, reason = resolve_team(entities.get("team_a_raw"))
        entities["team_a"] = team
        if not team:
            entities["unresolved_reason"] = reason
            trace.append(f"[prediction_tool] team resolution failed: {reason}")
            return {
                "entities": entities,
                "tool_result": {"ok": False, "kind": "player_prediction", "error": reason},
                "trace": trace,
            }
        try:
            result = predict_top_player(team=team)
            trace.append(
                f"[prediction_tool] predict_top_player({team}) -> "
                f"player={result['player']} p={result['probability']}"
            )
            return {
                "entities": entities,
                "tool_result": {
                    "ok": True,
                    "kind": "player_prediction",
                    "data": result,
                    "grounding": result["top_features"],
                },
                "trace": trace,
            }
        except Exception as exc:
            trace.append(f"[prediction_tool] EXCEPTION: {exc}")
            return {
                "entities": entities,
                "tool_result": {"ok": False, "kind": "player_prediction", "error": str(exc)},
                "trace": trace,
            }

    # Shouldn't happen given the router's conditional edge, but fail safe.
    trace.append("[prediction_tool] reached with unexpected intent")
    return {
        "tool_result": {"ok": False, "kind": "unknown", "error": "unexpected intent for prediction_node"},
        "trace": trace,
    }


# ---------------------------------------------------------------------------
# Task 3-adjacent: retrieval tool node
# ---------------------------------------------------------------------------

def retrieval_node(state: AFLState) -> dict:
    entities = dict(state.get("entities") or {})
    trace = list(state.get("trace") or [])

    team, reason = resolve_team(entities.get("team_a_raw"))
    entities["team_a"] = team
    if not team:
        entities["unresolved_reason"] = reason
        trace.append(f"[retrieval_tool] team resolution failed: {reason}")
        return {
            "entities": entities,
            "tool_result": {"ok": False, "kind": "stat_retrieval", "error": reason},
            "trace": trace,
        }

    stats = get_player_stats(team=team)
    if stats is None:
        err = f"no stats on record for {team} for the requested round"
        trace.append(f"[retrieval_tool] {err}")
        return {
            "entities": entities,
            "tool_result": {"ok": False, "kind": "stat_retrieval", "error": err},
            "trace": trace,
        }

    trace.append(f"[retrieval_tool] get_player_stats({team}) -> {stats}")
    return {
        "entities": entities,
        "tool_result": {"ok": True, "kind": "stat_retrieval", "data": stats},
        "trace": trace,
    }


# ---------------------------------------------------------------------------
# Direct-answer / refusal / fallback (no external tool call needed)
# ---------------------------------------------------------------------------

def direct_answer_node(state: AFLState) -> dict:
    trace = _push_trace(state, "[direct_answer] answering from general AFL knowledge")
    # TODO(you): replace with an actual LLM call for open-ended factual Q&A,
    # e.g. llm.invoke([...]) grounded with a short AFL knowledge/rules doc.
    return {
        "tool_result": {"ok": True, "kind": "factual", "data": {"note": "handled by direct_answer_node"}},
        "trace": trace,
    }


def refusal_node(state: AFLState) -> dict:
    trace = _push_trace(state, "[refusal] off-topic query")
    return {
        "final_response": (
            "I'm an AFL assistant, so I can only help with AFL stats, facts, and "
            "predictions -- that question is outside what I can answer here."
        ),
        "trace": trace,
    }


def fallback_node(state: AFLState) -> dict:
    trace = _push_trace(state, "[fallback] unsupported prediction type")
    return {
        "final_response": (
            "I can predict match winners and likely top-scorers, but I don't have a "
            "model for that specific request (e.g. exact scores/margins). "
            "Try asking who I think will win a match, or who's likely to top-score."
        ),
        "trace": trace,
    }


# ---------------------------------------------------------------------------
# Task 4: validation node
# ---------------------------------------------------------------------------

def validation_node(state: AFLState) -> dict:
    result = state.get("tool_result")
    trace = list(state.get("trace") or [])

    if result is None:
        trace.append("[validation] no tool_result present -> error")
        return {"validation_status": "error", "trace": trace}

    if result.get("ok"):
        trace.append("[validation] tool_result ok")
        return {"validation_status": "ok", "trace": trace}

    # ok == False: distinguish "we can fix this by asking the user" from
    # a genuine unsupported/hard error.
    reason = state.get("entities", {}).get("unresolved_reason") or result.get("error", "unknown error")
    question = f"I couldn't resolve that -- {reason}. Could you clarify which team/player you mean?"
    trace.append(f"[validation] tool_result failed ({reason}) -> needs_clarification")
    return {
        "validation_status": "needs_clarification",
        "clarification_question": question,
        "trace": trace,
    }


def route_after_validation(state: AFLState) -> str:
    status = state["validation_status"]
    if status == "ok":
        return "response_formatter"
    if status == "needs_clarification":
        return "clarification"
    return "fallback"


# ---------------------------------------------------------------------------
# Task 4: clarification node (loop back instead of guessing)
# ---------------------------------------------------------------------------

def clarification_node(state: AFLState) -> dict:
    trace = _push_trace(state, "[clarification] asking user instead of guessing")
    return {
        "final_response": state.get("clarification_question")
        or "Could you clarify the team/player/date you mean?",
        "trace": trace,
    }


# ---------------------------------------------------------------------------
# Task 3: response formatting -- predictions ALWAYS get a disclaimer
# ---------------------------------------------------------------------------

def response_formatter_node(state: AFLState) -> dict:
    result = state.get("tool_result") or {}
    kind = result.get("kind")
    data = result.get("data", {})
    grounding = result.get("grounding", [])
    trace = list(state.get("trace") or [])

    if kind == "match_prediction":
        fixture = data.get("fixture", {})
        text = (
            f"**Prediction (not a certainty):** {data['winner']} is favoured to win "
            f"({data['probability']:.0%} estimated probability)"
            + (f", round {fixture.get('round_number')}." if fixture else ".")
            + "\n\nKey factors:\n" + "\n".join(f"- {g}" for g in grounding)
            + "\n\n_This is a statistical estimate, not a guarantee -- upsets happen._"
        )
    elif kind == "player_prediction":
        text = (
            f"**Prediction (not a certainty):** {data['player']} is the most likely "
            f"top-scorer ({data['probability']:.0%} estimated probability).\n\n"
            "Key factors:\n" + "\n".join(f"- {g}" for g in grounding)
            + "\n\n_This is a statistical estimate, not a guarantee._"
        )
    elif kind == "stat_retrieval":
        text = "Here's what I have on record:\n" + "\n".join(f"- {k}: {v}" for k, v in data.items())
    elif kind == "factual":
        text = state.get("final_response") or "Here's what I know about that."
    else:
        text = "Here's the result."

    trace.append(f"[response_formatter] kind={kind}")
    return {"final_response": text, "trace": trace}
