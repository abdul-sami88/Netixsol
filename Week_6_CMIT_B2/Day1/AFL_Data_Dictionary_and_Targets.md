# AFL Data Foundations — Data Dictionary & Target Definitions

## Source Tables

| Table | Grain | Rows | Primary Key | Join keys to other tables |
| --- | --- | --- | --- | --- |
| `merged_players.csv` | Player-season-team-game type | ~25,070 | `(player_id, year, team, is_finals)` | `player_id`, `year`, `team` |
| `afl_players_round_by_round_stats_raw.csv` | Player-game (one row per player per game) | ~274,079 | `id` (renamed `player_id`... see note) or `(player_id, year, round, match_date)` | `team`, `year`, `round`, `match_date` |
| `team_matches_home_away_raw.csv` | Team-match perspective (2 rows per match: home + away) | ~15,808 | `id`, or `(team, year, round, match_date, home_away)` | `team`, `year`, `round`, `match_date` |

**Note:** the round-by-round file's original `id` column was renamed `player_id` during
cleaning — this is actually a unique **game-record** id, not a stable player identifier
across games (a real cross-game `player_id` exists too; verify which is which before joins).

**Reliable match key:** `(year, round, match_date)` alone is *not* unique — a full round
plays out over only 3-4 calendar days, so several unrelated games share the same date.
Use `match_id = year + round + sorted(team, opponent)` instead (built in the notebook).

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
| `top_disposal_getter` | Highest-disposal player in a game | `argmax(disposals)` within `(year, round)`; `disposals = kicks + handballs` | Player-game | Ranking |
| `top_goal_kicker` | Highest-goal player in a game | `argmax(goals)` within `(year, round)` | Player-game | Ranking |
| `fantasy_points_leader` | Highest fantasy score in a game | Uses source `fantasy_points` column (≈ `3·Kicks + 2·Handballs + 1·Mark + 6·Goal + 1·Behind + 4·Tackle + 5·FKf − 3·FKa + 1·Hitout`; formula documented for transparency, not re-derived) | Player-game | Ranking |
| `brownlow_leader` | Season official best-afield vote leader | `argmax(sum(brownlow_votes))` within `year` | Player-season | Ranking |

**Why classification for match winner, not pure regression on margin:** the assistant and
predictor both need a decision ("who wins"), margins are heavy-tailed and dominated by
blowouts under MSE, and draws are rare but real. Margin regression is retained as a
secondary target for confidence/closeness signal, not as the primary metric.

## Key Feature Groups (Task 4, full detail in notebook)

| Feature | Window | Leakage guard |
| --- | --- | --- |
| `team_win_streak`, `team_form_last{3,5}_score_avg`, `team_form_last5_win_rate` | Rolling 3/5 games | `.shift(1)` before rolling — current match excluded |
| `days_rest` (team & player) | Since previous match/game | Diff against prior row only |
| `season_wins_so_far`, `ladder_position` | Expanding, within-season | `.shift(1)` before expanding |
| `h2h_home_team_win_rate` | Expanding, per team-pair | `.shift(1)` before expanding |
| `player_form_last5_{disposals,goals,fantasy_points}_avg` | Rolling 5 games | `.shift(1)` before rolling |

## Train / Holdout Split

Strict **time-based split by season** (`time_based_split()` in the notebook) — train on
earlier seasons, hold out the most recent season(s). A random split would leak both
feature information (rolling stats built from "future" games relative to a randomly-placed
test row) and distributional information (rule/roster changes across eras) into training.

## Realistic Accuracy Ceiling

Public benchmarks (bookmaker odds, Elo-style models) land match-winner accuracy around
**65-70%** across a season; AFL has real irreducible randomness (injuries, umpiring,
weather, one-off brilliance) that no pre-match feature set can fully capture. Holdout
accuracy well above that band (e.g. 90%+) should be treated as a probable **leakage signal**
— audit for same-match features, mis-shifted rolling windows, or random (non-time-based)
splits before reporting it as a result.
