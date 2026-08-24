"""

USAGE
-----
    python3 player_stats_query.py
        -> interactive prompt, type queries directly


    python3 player_stats_query.py -q "Compare disposals between Sam Walsh and Lachie Neale in 2024"
        -> answer one query and exit (useful for scripting/testing)
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Optional

import pandas as pd

# ---------------------------------------------------------------------------
# Stat-name aliasing: maps things people actually type -> real column names.
# Sorted longest-alias-first at match time so "inside 50s" beats "inside".
# ---------------------------------------------------------------------------
STAT_ALIASES: dict[str, str] = {
    "tackles": "tackles", "tackle": "tackles",
    "disposals": "disposals", "disposal": "disposals",
    "kicks": "kicks", "kick": "kicks",
    "handballs": "handballs", "handball": "handballs",
    "marks": "marks", "mark": "marks",
    "goals": "goals", "goal": "goals",
    "behinds": "behinds", "behind": "behinds",
    "hitouts": "hit_outs", "hit outs": "hit_outs", "hit-outs": "hit_outs", "hitout": "hit_outs",
    "clearances": "clearances", "clearance": "clearances",
    "inside 50s": "inside_50s", "inside 50": "inside_50s", "i50s": "inside_50s", "i50": "inside_50s",
    "rebound 50s": "rebound_50s", "rebound 50": "rebound_50s",
    "contested possessions": "contested_possessions", "contested possession": "contested_possessions",
    "uncontested possessions": "uncontested_possessions", "uncontested possession": "uncontested_possessions",
    "contested marks": "contested_marks",
    "marks inside 50": "marks_inside_50",
    "one percenters": "one_percenters", "one-percenters": "one_percenters",
    "bounces": "bounces", "bounce": "bounces",
    "goal assists": "goal_assists", "goal assist": "goal_assists",
    "clangers": "clangers", "clanger": "clangers",
    "free kicks for": "free_kicks_for", "free kick for": "free_kicks_for",
    "free kicks against": "free_kicks_against", "free kick against": "free_kicks_against",
    "brownlow votes": "brownlow_votes", "brownlow vote": "brownlow_votes",
    "fantasy points": "total_fantasy_points", "fantasy point": "total_fantasy_points",
    "score": "total_score", "scores": "total_score",
    "games": "games_played", "games played": "games_played", "game": "games_played",
}
# longest alias first so multi-word aliases win over single-word substrings
_STAT_ALIASES_SORTED = sorted(STAT_ALIASES.items(), key=lambda kv: -len(kv[0]))


class QueryError(ValueError):
    """Raised when a query can't be understood or answered -- caller should
    surface this to the user rather than guessing."""


# ---------------------------------------------------------------------------
# Data loading + player resolution
# ---------------------------------------------------------------------------

def load_data(path: str | Path = "merged_players.csv") -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Put your real merged_players.csv next to this "
            f"script, or pass --data /path/to/merged_players.csv"
        )
    df = pd.read_csv(path)
    required = {"player_name", "year", "games_played"}
    missing = required - set(df.columns)
    if missing:
        raise QueryError(f"merged_players.csv is missing expected columns: {missing}")
    return df


def resolve_player(query_name: str, df: pd.DataFrame) -> str:
    """Resolve free-text to an exact player_name in the data. Never guesses
    between two plausible matches -- raises QueryError instead, same
    fail-closed philosophy as the team resolver in the LangGraph project."""
    names = df["player_name"].dropna().unique().tolist()
    q = query_name.strip().casefold()

    exact = [n for n in names if n.casefold() == q]
    if exact:
        return exact[0]

    contains = [n for n in names if q in n.casefold()]
    if len(contains) == 1:
        return contains[0]
    if len(contains) > 1:
        raise QueryError(f"'{query_name}' matches multiple players: {', '.join(contains)}. Be more specific.")

    # last-name-only fallback
    last_name_hits = [n for n in names if n.casefold().split()[-1] == q.split()[-1]]
    if len(last_name_hits) == 1:
        return last_name_hits[0]

    raise QueryError(f"No player matching '{query_name}' found in the data.")


def resolve_stat(text: str) -> str:
    text_cf = text.casefold()
    for alias, col in _STAT_ALIASES_SORTED:
        if alias in text_cf:
            return col
    raise QueryError(
        f"Couldn't figure out which stat you mean from: '{text}'. "
        f"Known stats: {sorted(set(STAT_ALIASES.values()))}"
    )


def extract_years(text: str) -> list[int]:
    return sorted({int(m) for m in re.findall(r"\b(?:19|20)\d{2}\b", text)})


# ---------------------------------------------------------------------------
# Stat computation
# ---------------------------------------------------------------------------

def total_stat(df: pd.DataFrame, player: str, stat_col: str, years: list[int]) -> float:
    """Sum stat_col across all matching rows (handles is_finals split rows
    and multiple years) for one player."""
    rows = df[(df["player_name"] == player) & (df["year"].isin(years))]
    if rows.empty:
        raise QueryError(f"No data found for {player} in {years}.")
    return float(rows[stat_col].fillna(0).sum())


def per_game_stat(df: pd.DataFrame, player: str, stat_col: str, year: int) -> float:
    """Games-weighted per-game average: sum(stat) / sum(games_played), not a
    naive average of any precomputed avg_* columns -- correct even when a
    player has separate regular-season/finals rows with different games_played."""
    rows = df[(df["player_name"] == player) & (df["year"] == year)]
    if rows.empty:
        raise QueryError(f"No data found for {player} in {year}.")
    total_games = float(rows["games_played"].fillna(0).sum())
    if total_games == 0:
        raise QueryError(f"{player} has 0 recorded games in {year}, can't compute a per-game rate.")
    return float(rows[stat_col].fillna(0).sum()) / total_games


# ---------------------------------------------------------------------------
# Natural-language query parsing + dispatch
# ---------------------------------------------------------------------------

def _split_two_players(text: str, df: pd.DataFrame) -> tuple[str, str]:
    """Find two player mentions in free text, split on ' and ' / ' or ' / ' vs ' / ','."""
    # drop trailing " in 2024" / " for 2024"
    fragment = re.split(r"\b(?:in|for)\s+(?:19|20)\d{2}\b", text)[0]
    # strip stat words (e.g. "disposals", "kicks per game") so they don't
    # end up glued onto the first player name
    for alias, _ in _STAT_ALIASES_SORTED:
        fragment = re.sub(re.escape(alias), "", fragment, flags=re.I)
    # strip leading/filler question phrasing that isn't part of a name
    fragment = re.sub(
        r"\b(compare|between|who had more|who has more|who'?s got more|per[\s-]game)\b",
        "", fragment, flags=re.I,
    )
    fragment = fragment.replace("—", " ").replace("–", " ").replace("-", " ").replace("?", " ")

    parts = re.split(r"\s+(?:and|or|vs\.?|v\.?)\s+|,", fragment, flags=re.I)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) < 2:
        raise QueryError(f"Couldn't find two player names to compare in: '{text}'")
    candidates = parts[-2:]  # the two most recent segments are the names
    player_a = resolve_player(candidates[0], df)
    player_b = resolve_player(candidates[1], df)
    return player_a, player_b


def answer_query(text: str, df: pd.DataFrame) -> str:
    years = extract_years(text)
    is_compare = bool(re.search(r"\bcompare\b|\bvs\.?\b| v\.? | or \b|who had more|who has more", text, re.I))
    is_per_game = "per game" in text.lower() or "per-game" in text.lower()

    stat_col = resolve_stat(text)

    if is_compare:
        if not years:
            raise QueryError("No year found in the query -- comparisons need a year, e.g. 'in 2024'.")
        if len(years) > 1:
            raise QueryError("Comparisons currently support one year at a time.")
        year = years[0]
        player_a, player_b = _split_two_players(text, df)

        if is_per_game:
            val_a = per_game_stat(df, player_a, stat_col, year)
            val_b = per_game_stat(df, player_b, stat_col, year)
            unit = f"{stat_col.replace('_', ' ')} per game"
        else:
            val_a = total_stat(df, player_a, stat_col, [year])
            val_b = total_stat(df, player_b, stat_col, [year])
            unit = f"total {stat_col.replace('_', ' ')}"

        leader = player_a if val_a > val_b else (player_b if val_b > val_a else None)
        lines = [
            f"{year} {unit}:",
            f"  {player_a}: {val_a:.1f}" if is_per_game else f"  {player_a}: {val_a:.0f}",
            f"  {player_b}: {val_b:.1f}" if is_per_game else f"  {player_b}: {val_b:.0f}",
        ]
        if leader:
            lines.append(f"-> {leader} had more.")
        else:
            lines.append("-> Tied.")
        return "\n".join(lines)

    # single-player total across one or more years
    if not years:
        raise QueryError("No year found in the query, e.g. 'across 2022 and 2023'.")

    # player name = whatever's left after removing stat words, years, and connector words
    name_fragment = text
    for alias, _ in _STAT_ALIASES_SORTED:
        name_fragment = re.sub(re.escape(alias), "", name_fragment, flags=re.I)
    name_fragment = re.sub(r"\b(?:19|20)\d{2}\b", "", name_fragment)
    name_fragment = re.sub(
        r"how many|total|did|get|across|combined|in|and|\?|per game|per-game",
        "", name_fragment, flags=re.I,
    )
    player_name = name_fragment.strip()
    if not player_name:
        raise QueryError(f"Couldn't find a player name in: '{text}'")
    player = resolve_player(player_name, df)

    if is_per_game:
        if len(years) > 1:
            raise QueryError("Per-game rate currently supports one year at a time.")
        val = per_game_stat(df, player, stat_col, years[0])
        return f"{player} averaged {val:.1f} {stat_col.replace('_', ' ')} per game in {years[0]}."

    val = total_stat(df, player, stat_col, years)
    years_text = " and ".join(str(y) for y in years) if len(years) > 1 else str(years[0])
    return f"{player} had {val:.0f} total {stat_col.replace('_', ' ')} across {years_text}."


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Query AFL player season stats in natural language")
    parser.add_argument("--data", default="merged_players.csv", help="path to merged_players.csv")
    parser.add_argument("-q", "--query", default=None, help="answer one query and exit")
    args = parser.parse_args()

    try:
        df = load_data(args.data)
    except (FileNotFoundError, QueryError) as exc:
        print(f"[error] {exc}")
        return

    if args.query:
        try:
            print(answer_query(args.query, df))
        except QueryError as exc:
            print(f"[couldn't answer] {exc}")
        return

    print(f"Loaded {args.data} ({len(df)} rows, {df['player_name'].nunique()} players). "
          f"Type a query, or 'exit' to quit.\n")
    while True:
        try:
            q = input("> ").strip()
        except EOFError:
            print()
            break
        if not q:
            continue
        if q.lower() in ("exit", "quit"):
            break
        try:
            print(answer_query(q, df))
        except QueryError as exc:
            print(f"[couldn't answer] {exc}")
        print()


if __name__ == "__main__":
    main()
