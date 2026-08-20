"""
entity_resolution.py
---------------------
Task 3 (input resolution) + Task 4 (fail closed, not silently).

Resolves free-text team nicknames ("Pies", "the Cats") to your dataset's
canonical team keys, and resolves relative date phrases ("this week",
"last round") to a concrete fixture / round number.

INTEGRATION POINT
------------------
Replace `CANONICAL_TEAMS` and `TEAM_ALIASES` with whatever your Day 2
dataset actually uses as team keys (e.g. the exact strings your model's
encoder/one-hot columns expect). Replace `_get_fixtures()` with a real
lookup against your fixture table / API.

Everything here fails LOUD (returns None + a reason) rather than guessing,
per Task 4's "loop back to ask instead of guessing" requirement.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

# ---------------------------------------------------------------------------
# TODO(you): swap this for the canonical team keys your Day 2 model was
# trained on (e.g. df["team"].unique() from your dataset).
# ---------------------------------------------------------------------------
CANONICAL_TEAMS = [
    "Collingwood", "Geelong", "Carlton", "Essendon", "Richmond",
    "West Coast", "Fremantle", "Adelaide", "Port Adelaide", "Sydney",
    "GWS", "Brisbane", "Gold Coast", "St Kilda", "Melbourne",
    "North Melbourne", "Western Bulldogs", "Hawthorn",
]

TEAM_ALIASES: dict[str, str] = {
    # Collingwood
    "pies": "Collingwood", "magpies": "Collingwood", "collingwood": "Collingwood",
    # Geelong
    "cats": "Geelong", "geelong": "Geelong",
    # Carlton
    "blues": "Carlton", "carlton": "Carlton",
    # Essendon
    "bombers": "Essendon", "dons": "Essendon", "essendon": "Essendon",
    # Richmond
    "tigers": "Richmond", "richmond": "Richmond",
    # West Coast
    "eagles": "West Coast", "west coast": "West Coast",
    # Fremantle
    "dockers": "Fremantle", "freo": "Fremantle", "fremantle": "Fremantle",
    # Adelaide
    "crows": "Adelaide", "adelaide": "Adelaide",
    # Port Adelaide
    "power": "Port Adelaide", "port": "Port Adelaide", "port adelaide": "Port Adelaide",
    # Sydney
    "swans": "Sydney", "sydney": "Sydney",
    # GWS
    "giants": "GWS", "gws": "GWS",
    # Brisbane
    "lions": "Brisbane", "brisbane": "Brisbane",
    # Gold Coast
    "suns": "Gold Coast", "gold coast": "Gold Coast",
    # St Kilda
    "saints": "St Kilda", "st kilda": "St Kilda",
    # Melbourne
    "demons": "Melbourne", "dees": "Melbourne", "melbourne": "Melbourne",
    # North Melbourne
    "roos": "North Melbourne", "kangaroos": "North Melbourne", "north melbourne": "North Melbourne",
    # Western Bulldogs
    "bulldogs": "Western Bulldogs", "dogs": "Western Bulldogs", "western bulldogs": "Western Bulldogs",
    # Hawthorn
    "hawks": "Hawthorn", "hawthorn": "Hawthorn",
}


def resolve_team(raw: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Return (canonical_team_or_None, failure_reason_or_None)."""
    if not raw or not raw.strip():
        return None, "no team text was extracted from the query"

    key = raw.strip().lower()
    key = key.removeprefix("the ").strip()

    if key in TEAM_ALIASES:
        return TEAM_ALIASES[key], None

    # exact canonical match (case-insensitive)
    for team in CANONICAL_TEAMS:
        if team.lower() == key:
            return team, None

    # fuzzy fallback (handles typos like "colingwood") -- but require a high
    # cutoff so we don't silently guess between two plausible teams (Task 4).
    candidates = difflib.get_close_matches(key, list(TEAM_ALIASES.keys()), n=1, cutoff=0.8)
    if candidates:
        return TEAM_ALIASES[candidates[0]], None

    return None, f"'{raw}' didn't match any known team or nickname"


# ---------------------------------------------------------------------------
# Fixture / round resolution
# TODO(you): replace with a real fixture-table lookup keyed on your DB/CSV.
# This stub deterministically synthesises an "upcoming round" so the graph
# is runnable end-to-end without your real data.
# ---------------------------------------------------------------------------
@dataclass
class Fixture:
    fixture_id: str
    round_number: int
    home: str
    away: str
    kickoff: date


def _get_fixtures() -> list[Fixture]:
    today = date.today()
    # Fabricate a small round of fixtures anchored on "today" for demo purposes.
    next_saturday = today + timedelta(days=(5 - today.weekday()) % 7 or 7)
    return [
        Fixture("R99-1", 99, "Collingwood", "Geelong", next_saturday),
        Fixture("R99-2", 99, "Carlton", "Essendon", next_saturday),
        Fixture("R99-3", 99, "Richmond", "Hawthorn", next_saturday + timedelta(days=1)),
        Fixture("R98-1", 98, "Geelong", "Adelaide", today - timedelta(days=6)),
    ]


def resolve_fixture(
    team_a: Optional[str],
    team_b: Optional[str],
    when_raw: Optional[str],
) -> tuple[Optional[Fixture], Optional[str]]:
    """Resolve 'this week' / 'next round' style phrases + two teams to a fixture."""
    if not team_a or not team_b:
        return None, "need both teams resolved before a fixture can be found"

    fixtures = _get_fixtures()
    teams = {team_a, team_b}

    when_raw = (when_raw or "").lower()
    upcoming_only = any(p in when_raw for p in ["this week", "next round", "upcoming", "coming up", ""])

    matches = [
        f for f in fixtures
        if {f.home, f.away} == teams and (not upcoming_only or f.kickoff >= date.today() - timedelta(days=1))
    ]
    if not matches:
        return None, f"no scheduled fixture found between {team_a} and {team_b}"

    matches.sort(key=lambda f: f.kickoff)
    return matches[0], None
