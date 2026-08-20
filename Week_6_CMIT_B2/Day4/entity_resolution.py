"""
entity_resolution.py
---------------------
Team-name resolution for the router/prediction path.

INTEGRATION STATUS
-------------------
This does NOT reimplement nickname/partial-name matching -- it reuses your
real `ai_chat_afl._resolve_team_name`, which already handles "Cats" ->
"Geelong Cats", "Geelong" -> "Geelong Cats", exact full names, and
ambiguous-nickname errors, resolved against whatever teams actually appear
in `afl_match_features_v2.csv`.

For PREDICTION requests specifically, the resolved name is then cross-checked
against `predict.py`'s own `valid_teams` (from Day 2's artifacts/valid_teams.joblib)
since the prediction models can only score teams they were trained on. In the
(expected) common case both datasets use the same club-name convention
("Melbourne Demons", "Collingwood Magpies", ...) this cross-check is a no-op;
it exists as a safety net in case the two datasets ever drift, so a
prediction never silently fires on a team-name variant the model wasn't
fitted on.

Fixture/date resolution: the historical match-feature CSVs described in this
project are completed-match records (every row has a final score/result), so
there's no "future fixture calendar" to resolve "this week" against. The
prediction models don't need one either -- predict.py always predicts against
each team's LATEST known rolling state, i.e. "if these two played next" --
so `resolve_when` below is intentionally a no-op passthrough that just
records what the user said, for logging/trace purposes only. If your Day 2
artifacts later include a real fixture list, wire it in here.
"""

from __future__ import annotations

from typing import Optional

import day2_interface

try:
    from ai_chat_afl import _resolve_team_name as _resolve_against_chat_dataset
    CHAT_TEAM_RESOLUTION_AVAILABLE = True
    _chat_import_error = None
except Exception as exc:  # noqa: BLE001
    CHAT_TEAM_RESOLUTION_AVAILABLE = False
    _chat_import_error = str(exc)

    def _resolve_against_chat_dataset(team: str):  # type: ignore
        return None, f"chat dataset unavailable: {_chat_import_error}"


def _fuzzy_against_predict_teams(raw: str) -> Optional[str]:
    """Fallback: substring/nickname match directly against predict.py's valid_teams,
    used only if ai_chat_afl's resolver isn't available or its answer isn't in
    predict.py's set."""
    valid = day2_interface.list_valid_teams()
    if not valid:
        return None
    normalized = raw.strip().casefold()
    for name in valid:
        if name.casefold() == normalized:
            return name
    hits = [name for name in valid if normalized in name.casefold() or name.casefold().split()[-1].rstrip("s") == normalized.rstrip("s")]
    if len(hits) == 1:
        return hits[0]
    return None


def resolve_team(raw: Optional[str], *, for_prediction: bool = False) -> tuple[Optional[str], Optional[str]]:
    """Return (canonical_team_or_None, failure_reason_or_None).

    for_prediction=True additionally requires the resolved name to be one
    predict.py's models were trained on.
    """
    if not raw or not raw.strip():
        return None, "no team text was extracted from the query"

    try:
        resolved, reason = _resolve_against_chat_dataset(raw)
    except Exception as exc:  # e.g. afl_match_features_v2.csv missing in this environment
        resolved, reason = None, f"team-name dataset unavailable ({exc})"

    if for_prediction:
        valid_teams = set(day2_interface.list_valid_teams())
        if resolved and (not valid_teams or resolved in valid_teams):
            return resolved, None
        # try a direct fuzzy match against predict.py's own team list as a fallback
        fallback = _fuzzy_against_predict_teams(raw)
        if fallback:
            return fallback, None
        if resolved and valid_teams:
            return None, f"'{resolved}' isn't one of the teams the prediction model was trained on"
        return None, reason or f"'{raw}' didn't match a known team"

    return resolved, reason


def resolve_when(round_or_date_raw: Optional[str]) -> dict:
    """No-op passthrough -- see module docstring. Kept as a function (not a
    constant) so a real fixture-calendar lookup can be dropped in later
    without touching call sites in nodes.py."""
    return {"round_or_date_raw": round_or_date_raw, "resolved_fixture": None}
