# AFL Data Foundations — Data Dictionary & Target Definitions

## Source Tables

| Table | Grain | Rows | Primary Key | Join keys |
| --- | --- | --- | --- | --- |
| `merged_players.csv` | Player-season-team | ~25,070 | `(player_id, year, team, is_finals)` | `player_id`, `year`, `team` |
| `afl_players_round_by_round_stats_raw.csv` | Player-game | ~274,079 | See **Known Data Issue** below | `team`, `year`, `round`, `match_date` |
| `team_matches_home_away_raw.csv` | Team-match (2 rows/match) | ~15,808 | `(team, year, round, match_date, home_away)` | `team`, `year`, `round`, `match_date` |

**Reliable match key:** `(year, round, match_date)` alone is not unique — a full round plays
out over only 3-4 calendar days, so unrelated games share dates. Use
`match_id = year + round + sorted(team, opponent)` instead.

**Known data issue — `rounds_stats_df.player_id` is not a real player key.** The raw file's
`id` column is a unique **per-row game-record id** (274,079 unique values for 274,079 rows),
not a persistent player identity — every naive `groupby('player_id')` on this table returns
single-row groups. The notebook's fix cell (1) checks whether the raw file actually ships a
separate genuine `player_id`, and if not, (2) reconstructs one via `reconstructed_player_key`
= sequence-continuity of `career_game_count` within `(team, jersey_num)`. All downstream
player-level features use whichever key turns out reliable — see the notebook's fix cell and
Task 4.6 for the exact caveat.

## Structural Changes to Flag

- **Fitzroy + Brisbane Bears → Brisbane Lions** (1997 merger)
- **Footscray → Western Bulldogs** (1997 rename)
- **South Melbourne → Sydney Swans** (1982 relocation)
- **Gold Coast (2011) / GWS Giants (2012)** — expansion teams, shorter history
- Interchange-cap and substitute-rule changes (notably ~2011) affect rotation-heavy stats
  (`percentage_of_game_played`, `career_game_count`) — treat as not fully comparable pre/post

## Prediction Targets

| Target | Definition | Formula | Level | Framing |
| --- | --- | --- | --- | --- |
| `match_result` | Match outcome, home team's perspective | `Win` if `home_score>away_score`, `Loss` if `<`, `Draw` if `==` | Match | **Classification** (primary) |
| `match_margin` | Points margin, home minus away | `home_score - away_score` | Match | Regression (secondary/auxiliary) |
| `top_disposal_getter` | **Single** highest-disposal player in a round | `argmax(disposals)` within `(year, round)` | Player-game | Round-leader |
| `top_goal_kicker` | **Single** highest-goal player in a round | `argmax(goals)` within `(year, round)` | Player-game | Round-leader |
| `is_top5_disposals` / `is_top5_goals` | Binary: finished in that round's top 5 for the stat | `rank(stat, ascending=False) <= 5` within `(year, round)` | Player-game | **Top-N** (used for per-player probability models — far more learnable than round-leader) |
| `is_top5_{stat}_in_position` | Same top-5 logic, ranked within `position_proxy` instead of league-wide | `rank(stat, ascending=False) <= 5` within `(year, round, position_proxy)` | Player-game | Top-N, role-normalized |
| `fantasy_points_leader` | Highest fantasy score in a round | `argmax(fantasy_points)` within `(year, round)` — source column, formula below | Player-game | Round-leader |
| `brownlow_leader` | Season official best-afield vote leader | `argmax(sum(brownlow_votes))` within `year` | Player-season | Season-leader |

**Why classification for match winner, not pure regression on margin:** the assistant and
predictor both need a decision, margins are heavy-tailed and dominated by blowouts under MSE,
and draws are rare but real. Margin regression is kept as a secondary target for
confidence/closeness signal, not as the primary metric.

**Why three "top player" framings, not one:** round-leader answers "who was THE best" (one
winner); top-5 answers "will this player finish near the top" (a far more learnable,
lower-variance target for per-player models, since top-5-of-~400 is much less extreme than
rank-1); top-5-in-position corrects for the fact that raw stats aren't comparable across
roles (a ruck's 3 goals ≠ a forward's 3 goals).

### Fantasy composite score — exact, verified formula

`fantasy_points` in the source data matches the **official AFL Fantasy Classic** scoring
system (verified against AFL.com.au's published scoring table):

FP = 3×Kicks + 2×Handballs + 3×Marks + 4×Tackles
     + 1×FreeKicksFor − 3×FreeKicksAgainst + 1×HitOuts + 6×Goals + 1×Behinds

We use the source column directly rather than recomputing it — this formula is documented so
the number is auditable, not because we're re-deriving it ourselves.

## Key Feature Groups (full detail + leakage-risk column in notebook Task 4.6)

| Feature | Window | Leakage guard |
| --- | --- | --- |
| `team_win_streak`, `team_form_last{3,5}_score_avg`, `team_form_last5_win_rate` | Rolling 3/5 games | `.shift(1)` before rolling |
| `days_rest` (team & player) | Since previous match/game | Diff against prior row only |
| `season_wins_so_far`, `ladder_position` | Expanding, within-season | `.shift(1)` before expanding |
| `h2h_home_team_win_rate` | Expanding, per team-pair | `.shift(1)` before expanding |
| `team_venue_win_rate`, `team_venue_games_played` | Expanding, per team-venue pair | `.shift(1)` before expanding; small-sample risk at rarely-visited grounds |
| `player_form_last5_{disposals,goals,fantasy_points}_avg`, `player_days_rest` | Rolling 5 games | `.shift(1)` before rolling; grouped on `PLAYER_KEY` (real or reconstructed — see caveat above) |

**Not included (documented gap, not an oversight):** weather. No source table carries it;
enriching would require joining `(venue, match_date)` against a historical weather API plus a
venue-coordinates reference table that doesn't currently exist.

## Train / Holdout Split

Strict **time-based split by season** (`time_based_split()` in the notebook) — train on
earlier seasons, hold out the most recent season(s). A random split would leak both feature
information (rolling stats built from "future" games relative to a randomly-placed test row)
and distributional information (rule/roster changes across eras) into training.

## Realistic Accuracy Ceiling

Public benchmarks (bookmaker odds, Elo-style models) land match-winner accuracy around
**65-70%** across a season; AFL has real irreducible randomness (injuries, umpiring, weather,
one-off brilliance) no pre-match feature set can fully capture. Holdout accuracy well above
that band (e.g. 90%+) should be treated as a probable **leakage signal** — audit for
same-match features, mis-shifted rolling windows, or non-time-based splits before reporting
it as a result.
