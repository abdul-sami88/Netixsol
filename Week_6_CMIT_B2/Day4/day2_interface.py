"""
day2_interface.py
------------------
Task 3: this is the ONLY file you should need to edit to wire in your
real Day 2 artifacts. Everything below is a deterministic stand-in so the
graph is runnable/testable right now; swap the bodies for your real calls
and keep the function signatures + return shape identical and the rest of
the graph (nodes.py, validation, formatting) needs no changes.

Expected return shapes
-----------------------
predict_match_winner(team_a, team_b, fixture_id=None) -> dict:
    {
        "winner": str,               # canonical team key
        "probability": float,        # 0-1, P(winner wins)
        "top_features": list[str],   # 2-3 short human-readable drivers
    }

predict_top_player(team=None, fixture_id=None) -> dict:
    {
        "player": str,
        "probability": float,        # 0-1, P(this player top-scores)
        "top_features": list[str],
    }

get_player_stats(player, round_number=None) -> dict | None:
    Return None if the player/round can't be found (triggers validation
    error, not a hallucinated guess).
"""

from __future__ import annotations

import hashlib
import random
from typing import Optional
import joblib

match_model = joblib.load('Day2/artifacts/match_winner_pipeline.joblib')
player_model = joblib.load('Day2/artifacts/match_winner_pipeline.joblib')

# ---------------------------------------------------------------------------
# TODO(you): replace this whole block with:
#
#   import joblib
#   match_model = joblib.load("artifacts/day2/match_winner_model.pkl")
#   player_model = joblib.load("artifacts/day2/top_player_model.pkl")
#   feature_frame = pd.read_parquet("artifacts/day2/features.parquet")
#
# and call match_model.predict_proba(...) etc. inside the functions below.
# ---------------------------------------------------------------------------


def _seeded_rng(*parts: str) -> random.Random:
    """Deterministic per-input RNG so demo predictions are stable across runs."""
    seed = int(hashlib.sha256("|".join(parts).encode()).hexdigest(), 16) % (2**32)
    return random.Random(seed)


PLAUSIBLE_MATCH_FEATURES = [
    "higher recent scoring differential",
    "home ground advantage",
    "stronger head-to-head record last 5 meetings",
    "opponent missing key forward (injury list)",
    "better inside-50 efficiency this season",
    "significantly higher ladder position",
]

PLAUSIBLE_PLAYER_FEATURES = [
    "leads team in goals per game this season",
    "favourable match-up vs opponent's weakest defender",
    "high recent scoring form (last 3 games)",
    "plays in a high-possession midfield role",
]


def predict_match_winner(team_a: str, team_b: str, fixture_id: Optional[str] = None) -> dict:
    rng = _seeded_rng(team_a, team_b, fixture_id or "")
    winner = rng.choice([team_a, team_b])
    prob = round(rng.uniform(0.52, 0.78), 2)
    features = rng.sample(PLAUSIBLE_MATCH_FEATURES, k=3)
    return {"winner": winner, "probability": prob, "top_features": features}


def predict_top_player(team: Optional[str] = None, fixture_id: Optional[str] = None) -> dict:
    if not team:
        raise ValueError("predict_top_player requires a resolved team")
    rng = _seeded_rng(team, fixture_id or "")
    # fabricate a small squad so the demo has something to pick from
    squad = [f"{team[:3].upper()} Player {i}" for i in range(1, 6)]
    player = rng.choice(squad)
    prob = round(rng.uniform(0.15, 0.45), 2)
    features = rng.sample(PLAUSIBLE_PLAYER_FEATURES, k=2)
    return {"player": player, "probability": prob, "top_features": features}


_FAKE_STATS_DB = {
    ("Collingwood", 98): {"disposals_avg": 21.4, "goals_last_round": 3, "tackles_last_round": 5},
    ("Geelong", 98): {"disposals_avg": 23.1, "goals_last_round": 1, "tackles_last_round": 6},
}


def get_player_stats(team: Optional[str], round_number: Optional[int] = None) -> Optional[dict]:
    """
    TODO(you): replace with a real lookup, e.g.
        df[(df.team == team) & (df.round == round_number)].to_dict()
    Returns None (not a guess) if not found -- validation_node treats that
    as an error and routes to clarification/fallback.
    """
    round_number = round_number or 98
    return _FAKE_STATS_DB.get((team, round_number))
