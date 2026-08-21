"""
nodes.py
--------
Task 3 (prediction tool node), Task 4 (validation + fallback + clarification).

Architecture note: factual/retrieval/off_topic all delegate wholesale to
`ai_chat_afl.invoke_afl_agent` (your real Day 3 agent), which already owns
retrieval tools, scope guardrails, and refusal wording -- reimplementing
that here would just be a worse copy. This graph's job is specifically to
intercept prediction-shaped queries BEFORE they reach that agent (which has
no prediction tools at all and would either refuse or hallucinate a winner)
and guarantee probability + disclaimer framing on the way out.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Optional

import day2_interface
from entity_resolution import resolve_team
from state import AFLState


def _push_trace(state: AFLState, msg: str) -> list[str]:
    trace = list(state.get("trace") or [])
    trace.append(msg)
    return trace


# ---------------------------------------------------------------------------
# Task 3: prediction tool node (real predict.py / fitted pipelines)
# ---------------------------------------------------------------------------

def prediction_node(state: AFLState) -> dict:
    entities = dict(state.get("entities") or {})
    intent = state["intent"]
    trace = list(state.get("trace") or [])

    available, load_error = day2_interface.is_available()
    if not available:
        trace.append(f"[prediction_tool] predictor unavailable: {load_error}")
        return {
            "tool_result": {"ok": False, "kind": "unavailable", "error": load_error},
            "trace": trace,
        }

    if intent == "prediction_match":
        team_a, reason_a = resolve_team(entities.get("team_a_raw"), for_prediction=True)
        team_b, reason_b = resolve_team(entities.get("team_b_raw"), for_prediction=True)
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

        try:
            # user's team_a is treated as "home" for the model's home/away
            # framing -- the model doesn't know about a real fixture's venue,
            # so this only affects which side gets the "home" numeric slot,
            # not which team is favoured (predict.py uses each team's own
            # latest rolling state regardless of home/away label).
            result = day2_interface.predict_match_winner(team_a, team_b)
            trace.append(
                f"[prediction_tool] predict_match_winner({team_a}, {team_b}) -> "
                f"winner={result['winner']} p={result['probability']:.3f} "
                f"confidence={result['confidence']}"
            )
            return {
                "entities": entities,
                "tool_result": {
                    "ok": True,
                    "kind": "match_prediction",
                    "data": result,
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
        team, reason = resolve_team(entities.get("team_a_raw"), for_prediction=True)
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
            result = day2_interface.predict_top_player(team)
            trace.append(
                f"[prediction_tool] predict_top_player({team}) -> "
                f"player_id={result['player_id']} predicted_disposals={result['predicted_disposals']:.1f}"
            )
            return {
                "entities": entities,
                "tool_result": {
                    "ok": True,
                    "kind": "player_prediction",
                    "data": {**result, "team": team},
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

    trace.append("[prediction_tool] reached with unexpected intent")
    return {
        "tool_result": {"ok": False, "kind": "unknown", "error": "unexpected intent for prediction_node"},
        "trace": trace,
    }


# ---------------------------------------------------------------------------
# Delegate to the real Day 3 chat/retrieval agent for everything else
# (factual, retrieval, off_topic) -- it owns its own tools + scope guardrail.
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_chat_agent():
    from ai_chat_afl import create_afl_agent
    return create_afl_agent()


# Test hook: tests/test_e2e.py can monkeypatch this instead of hitting a
# real Gemini API key + real CSVs, so the graph is still exercisable offline.
_CHAT_AGENT_OVERRIDE: Optional[Any] = None


def set_chat_agent_override(fn) -> None:
    """Inject a stand-in for ai_chat_afl.invoke_afl_agent (used by offline tests)."""
    global _CHAT_AGENT_OVERRIDE
    _CHAT_AGENT_OVERRIDE = fn


def chat_agent_node(state: AFLState, config=None) -> dict:
    trace = _push_trace(state, f"[chat_agent] delegating to ai_chat_afl (intent={state['intent']})")
    thread_id = (config or {}).get("configurable", {}).get("thread_id", "default")

    if _CHAT_AGENT_OVERRIDE is not None:
        answer = _CHAT_AGENT_OVERRIDE(state["user_query"], thread_id=thread_id)
        trace.append("[chat_agent] used test override (no live Gemini call)")
        return {"final_response": answer, "trace": trace}

    try:
        from ai_chat_afl import invoke_afl_agent
        agent = _get_chat_agent()
        result = invoke_afl_agent(state["user_query"], agent=agent, thread_id=thread_id)
        trace.append(f"[chat_agent] grounded={result['grounding']['grounded']}")
        return {"final_response": result["answer"], "trace": trace}
    except Exception as exc:
        trace.append(f"[chat_agent] EXCEPTION: {exc}")
        return {
            "final_response": (
                "I couldn't reach the AFL chat/retrieval agent just now "
                f"({exc}). Please check GEMINI_API_KEY and that the feature "
                "CSVs are present, then try again."
            ),
            "trace": trace,
        }


# ---------------------------------------------------------------------------
# Fallback (prediction-shaped but unsupported, e.g. exact score/margin)
# ---------------------------------------------------------------------------

def fallback_node(state: AFLState) -> dict:
    trace = _push_trace(state, "[fallback] unsupported prediction type")
    return {
        "final_response": (
            "I can predict match winners (with a win probability) and a likely "
            "top disposal-getter, but I don't have a model for that specific "
            "request (e.g. an exact score or margin). Try asking who I think "
            "will win a match, or who's likely to lead a team in disposals."
        ),
        "trace": trace,
    }


# ---------------------------------------------------------------------------
# Task 4: validation node (prediction path only)
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

    if result.get("kind") == "unavailable":
        trace.append("[validation] predictor unavailable -> fallback")
        return {"validation_status": "unsupported", "trace": trace}

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
        or "Could you clarify the team/player you mean?",
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
        text = (
            f"**Prediction (not a certainty):** {data['winner']} "
            f"({data['probability']:.0%} estimated win probability, "
            f"{data['confidence']} confidence)\n\n"
            "Key factors:\n" + "\n".join(f"- {g}" for g in grounding)
            + "\n\n_Model: Logistic Regression, ~63% test accuracy. "
              "This is a statistical estimate, not a guarantee -- upsets happen._"
        )
    elif kind == "player_prediction":
        top_n = data.get("top_n", [])
        top_n_text = ", ".join(f"#{pid} (~{disp:.1f})" for pid, disp in top_n[1:4])
        player_label = data.get("player_name") or f"Player #{data['player_id']}"
        text = (
            f"**Prediction (not a certainty):** {player_label} "
            f"is the most likely top disposal-getter for {data.get('team', 'this team')} "
            f"(~{data['predicted_disposals']:.1f} predicted disposals).\n\n"
            "Key factors:\n" + "\n".join(f"- {g}" for g in grounding)
            + (f"\n\nOther contenders (by player_id): {top_n_text}" if top_n_text else "")
            + "\n\n_Model: Gradient Boosting Regressor, ~63% top-5 hit rate "
              "(a simple 'last week's leader repeats' baseline gets ~72%, so treat "
              "this as one signal, not gospel). This is a statistical estimate, not a guarantee._"
        )
    else:
        # chat_agent / fallback / clarification already set final_response directly
        text = state.get("final_response") or "Here's the result."

    trace.append(f"[response_formatter] kind={kind}")
    return {"final_response": text, "trace": trace}
