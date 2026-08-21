"""
day2_interface.py
------------------
Thin adapter over your REAL `predict.py` (Day 2). This is the only file
that talks to the fitted sklearn pipelines.

Why an adapter instead of calling predict.py directly from nodes.py:
1. `predict.py` raises at IMPORT time if `artifacts/` is incomplete (see its
   top-of-file `if not _ARTIFACTS.exists(): raise FileNotFoundError`). That's
   correct for a production script, but it would crash the entire LangGraph
   app before the graph is even built if artifacts are missing/partial. This
   adapter isolates that failure so the rest of the graph still runs and
   reports a clear tool error instead of a hard crash.
2. `predict.py` doesn't return grounding/explanations (Task 3 requires
   2-3 human-readable factors per prediction). This adapter adds that layer
   on top by reading the same `_latest_team_state` / `_latest_player_state`
   tables `predict.py` already loaded (via its private helpers -- see
   `_team_grounding` / `_player_grounding` below).

INTEGRATION STATUS
-------------------
Wired directly to your real predict.py / match_winner_pipeline.joblib /
top_player_pipeline.joblib. The only thing NOT yet supplied is the full
`artifacts/` folder (numeric_features.joblib, categorical_features.joblib,
player_numeric_features.joblib, valid_teams.joblib, date_range.joblib,
latest_team_state.parquet, latest_player_state.parquet, match_history.parquet)
-- drop your real Day 2 artifacts/ folder next to predict.py and this
module picks it up automatically, no code changes needed.
"""

from __future__ import annotations

import importlib
from typing import Optional

# ---------------------------------------------------------------------------
# Import predict.py defensively: its module-level artifact loading can raise
# if artifacts/ is missing/incomplete. We don't want that to take down the
# whole graph at import time.
# ---------------------------------------------------------------------------
PREDICT_AVAILABLE = False
_predict = None
_load_error: Optional[str] = None

try:
    _predict = importlib.import_module("predict")
    PREDICT_AVAILABLE = True
except Exception as exc:  # noqa: BLE001 - genuinely want to catch anything here
    _load_error = str(exc)


def is_available() -> tuple[bool, Optional[str]]:
    return PREDICT_AVAILABLE, _load_error


def list_valid_teams() -> list[str]:
    if not PREDICT_AVAILABLE:
        return []
    return _predict.list_valid_teams()


# ---------------------------------------------------------------------------
# Grounding helpers -- read the same latest-state tables predict.py already
# loaded, to produce short human-readable "why" bullets. These are simple
# rule-based comparisons (which side has better recent form/ladder position),
# not a SHAP/feature-importance explanation of the model's internals -- we
# say so explicitly in the formatted response.
# ---------------------------------------------------------------------------

def _team_grounding(home_team: str, away_team: str, predicted_winner: str) -> list[str]:
    if not PREDICT_AVAILABLE:
        return []
    try:
        home = _predict._get_team_features(home_team)
        away = _predict._get_team_features(away_team)
    except Exception:
        return []

    bullets = []
    fav, other = (home, away) if predicted_winner == home_team else (away, home)
    fav_name, other_name = (home_team, away_team) if predicted_winner == home_team else (away_team, home_team)

    if fav["form_last5_win_rate"] > other["form_last5_win_rate"]:
        bullets.append(
            f"better recent form: {fav_name} won {fav['form_last5_win_rate']:.0%} of "
            f"their last 5 vs {other_name}'s {other['form_last5_win_rate']:.0%}"
        )
    if fav["ladder_position"] < other["ladder_position"]:
        bullets.append(
            f"higher on the ladder: {fav_name} is {int(fav['ladder_position'])} vs "
            f"{other_name}'s {int(other['ladder_position'])}"
        )
    if fav["season_wins"] > other["season_wins"]:
        bullets.append(
            f"more wins this season: {fav_name} has {int(fav['season_wins'])} vs "
            f"{other_name}'s {int(other['season_wins'])}"
        )
    if not bullets:
        bullets.append("model's learned combination of recent form, ladder position, and season record")
    return bullets[:3]


def _player_grounding(row) -> list[str]:
    bullets = []
    try:
        if row.get("player_form_last5_disposals_avg", 0) and row["player_form_last5_disposals_avg"] > 20:
            bullets.append(f"averaging {row['player_form_last5_disposals_avg']:.1f} disposals over their last 5 games")
        if row.get("player_form_last5_fantasy_points_avg", 0) and row["player_form_last5_fantasy_points_avg"] > 80:
            bullets.append(f"strong recent fantasy output ({row['player_form_last5_fantasy_points_avg']:.0f} avg over last 5)")
        if row.get("own_team_team_venue_win_rate", 0) and row["own_team_team_venue_win_rate"] > 0.5:
            bullets.append(f"team wins {row['own_team_team_venue_win_rate']:.0%} of games at this venue")
    except Exception:
        pass
    if not bullets:
        bullets.append("highest model-predicted disposal count among the team's current roster")
    return bullets[:3]


# ---------------------------------------------------------------------------
# Public prediction wrappers -- what nodes.py actually calls
# ---------------------------------------------------------------------------

def predict_match_winner(home_team: str, away_team: str) -> dict:
    """
    Returns:
        {"winner": str, "probability": float (0-1, P(winner wins)),
         "prediction_outcome": "Win"/"Loss"/"Draw", "confidence": str,
         "top_features": list[str]}
    Raises ValueError/RuntimeError on invalid team / prediction failure
    (nodes.py catches these and converts to a validation error).
    """
    if not PREDICT_AVAILABLE:
        raise RuntimeError(f"predictor not available in this environment: {_load_error}")

    result = _predict.predict_match_winner(home_team, away_team)
    result["top_features"] = _team_grounding(home_team, away_team, result["winner"])
    return result


def predict_top_player(team: str, return_top_n: int = 3) -> dict:
    """
    Returns:
        {"player_id": int, "player_name": str, "predicted_disposals": float,
         "top_n": list[tuple[int, float]], "top_features": list[str]}
    """
    if not PREDICT_AVAILABLE:
        raise RuntimeError(f"predictor not available in this environment: {_load_error}")

    result = _predict.predict_top_player(team, return_top_n=return_top_n)

    grounding: list[str] = []
    try:
        row = _predict._latest_player_state.loc[result["top_player_id"]]
        grounding = _player_grounding(row)
    except Exception:
        grounding = ["highest model-predicted disposal count among the team's current roster"]

    player_name = _resolve_player_name(result["top_player_id"])

    return {
        "player_id": result["top_player_id"],
        "player_name": player_name,
        "predicted_disposals": result["predicted_disposals"],
        "top_n": result["top_n_predictions"],
        "top_features": grounding,
    }


def _resolve_player_name(player_id: int) -> str:
    """Best-effort player_id -> display name, reusing ai_chat_afl's name
    lookup (merged_players.csv) since predict.py's artifacts only carry
    numeric player_id, no names."""
    try:
        from ai_chat_afl import _id_to_name
        return _id_to_name(int(player_id))
    except Exception:
        return f"player_id {player_id}"
