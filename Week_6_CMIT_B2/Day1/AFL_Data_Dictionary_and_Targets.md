# AFL Data Foundations — Data Dictionary & Target Definitions

## Source Tables

| Table | Grain | Rows | Unique Keys | Join keys |
| --- | --- | --- | --- | --- |
| `merged_players.csv` | Player-season-team-gametype | 25,070 | ~2,843 players, ~40 years, 20 teams | `player_id`, `year`, `team`, `is_finals` |
| `afl_players_round_by_round_stats_raw.csv` | Player-game | 274,079 | One per player per game | `player_id`, `team`, `year`, `round`, `match_date` |
| `team_matches_home_away_raw.csv` | Team-match (2 rows/match) | 15,808 | 7,904 unique matches × 2 | `team`, `year`, `round`, `match_date`, `home_away` |

**Data span:** 1983 to 2025 (~42 seasons)  
**Canonical team list:** 20 teams (verified across all 3 tables)  

---

## Known Data Issues (and How the Notebook Fixes Them)

### Issue 1: Player ID collision in `rounds_stats_df`

**Problem:** Raw file ships both:

- `id` column (unique per row, 274,079 unique values) — this is a game-record id, not a player identifier
- `player_id` column (real persistent player key) — this is what we want

**Fix applied (Cell 3):** The notebook detects both columns, renames the game-record `id` → `game_record_id`, and uses the genuine `player_id` for all downstream grouping.

**Result:** Player-level rolling features (player form, last-5 averages) have **98.9% coverage** because `player_id` is reliable.

---

### Issue 2: Match key is NOT unique on `(year, round, match_date)` alone

**Problem:** A full AFL round plays out over 3-4 calendar days. Multiple unrelated games share the same date.

**Solution:** Use `match_id = (year, round, sorted(team, opponent))` instead. The notebook (Cell 16) builds a canonical `matches_df` with this key and validates it: **7,904 unique match IDs** (7,932 in feature table due to minimal data cleaning rows).

---

## Structural Changes to Flag

| Event | In dataset? | Years affected | Notes |
| ------- | ----------- | --- | --- |
| **Fitzroy lions** (original club) | ❌ No | — | Merged with Brisbane Bears in 1997; only post-merger "Brisbane Lions" exists in data |
| **Brisbane Bears** | ✅ Yes | 1987–1996 | Pre-merger form; ceased independent existence after 1996 |
| **Brisbane Lions** (post-merger) | ✅ Yes | 1997+ | The merged entity |
| **South Melbourne** | ❌ No | — | Relocated to Sydney in 1982; only "Sydney Swans" in data |
| **Footscray** | ❌ No | — | Renamed to Western Bulldogs in 1997; only "Western Bulldogs" in data |
| **Gold Coast Suns** (expansion) | ✅ Yes | 2011+ | Shorter history; fewer seasons of data |
| **GWS Giants** (expansion) | ✅ Yes | 2012+ | Shorter history; fewer seasons of data |

**Rule changes to flag:**

- **Interchange cap and substitute rule** (~2011 onwards) — affects rotation-heavy stats like `percentage_of_game_played` and `career_game_count`. Pre/post-2011 rosters and player-load patterns are not directly comparable.
- **Score review introduction** — minor impact on game flow but doesn't affect traditional stat collection.

---

## Prediction Targets

| Target | Definition | Formula | Level | Framing | Notes |
| --- | --- | --- | --- | --- | --- |
| `match_result` | Match outcome (home team perspective) | `'Win'` if `home_score > away_score`, `'Loss'` if `<`, `'Draw'` if `==` | Match | **Classification** (primary) | ~59% Win, ~40% Loss, ~1% Draw (class imbalance minor) |
| `match_margin` | Points margin (home − away) | `home_score - away_score` | Match | Regression (secondary) | Auxiliary target; used for confidence/closeness signals |
| `top_disposal_getter` | Single highest-disposal player in a round | `argmax(disposals)` within `(year, round)` | Player-game | Round-leader | Extreme class imbalance; ~1 winner per round |
| `top_goal_kicker` | Single highest-goal player in a round | `argmax(goals)` within `(year, round)` | Player-game | Round-leader | Similar extreme imbalance |
| `is_top5_disposals` | Binary: finished in that round's top 5 | `rank(disposals, desc) <= 5` within `(year, round)` | Player-game | **Top-N** (recommended) | Learnable target; top-5-of-~400 is much less extreme |
| `is_top5_goals` | Binary: finished in that round's top 5 | `rank(goals, desc) <= 5` within `(year, round)` | Player-game | **Top-N** (recommended) | — |
| `is_top5_{stat}_in_position` | Top-5 within position role (not league-wide) | `rank(stat, desc) <= 5` within `(year, round, position_proxy)` | Player-game | Top-N, role-normalized | Corrects for stat non-comparability across positions |
| `fantasy_points_leader` | Highest fantasy score in a round | `argmax(fantasy_points)` within `(year, round)` | Player-game | Round-leader | Uses verified AFL Fantasy Classic formula (below) |
| `brownlow_leader` | Season official best-afield vote leader | `argmax(sum(brownlow_votes))` within `year` | Player-season | Season-leader | Official AFL award; rare target |

**Why classification for match winner, not regression:** The predictor needs a decision (Win/Loss/Draw). Regression on margin is heavy-tailed (blowouts dominate MSE), and draws are rare but real. Margin is kept as secondary target for confidence calibration, not as the primary metric.

**Why three "top player" framings:**

- **Round-leader** answers "who was THE single best player" — one winner, but extreme class imbalance (~1 in 400)
- **Top-5** answers "will this player finish near the top" — far more learnable, lower-variance, enables per-player probability models
- **Top-5-in-position** normalizes for the fact that a ruck's 3 goals is a strong game, while a forward's 3 is weak. Position proxy is stat-based (high hit-outs → ruck, etc.), documented in notebook Task 3.

---

## Fantasy Composite Score Formula

`fantasy_points` in the source data is the **official AFL Fantasy Classic** scoring system (verified against AFL.com.au's published scoring table):

FP = 3×Kicks + 2×Handballs + 3×Marks + 4×Tackles 
     + 1×FreeKicksFor − 3×FreeKicksAgainst + 1×HitOuts + 6×Goals + 1×Behinds

**Note:** We use the source column directly (not recomputing) — the formula is documented here for auditability and cross-reference, not because we're re-deriving it.

---

## Feature Engineering Overview

### Built Feature Tables

| Table | Rows | Columns | Grain | Version | Save format |
|-------|------|---------|-------|---------|-------------|
| `afl_match_features_v2` | 7,932 | 41 | 1 row per match (home-team perspective) | v2 (2026-08-18) | CSV + Parquet |
| `afl_player_features_v2` | 274,403 | 17 | 1 row per player-game | v2 (2026-08-18) | CSV + Parquet |

### Team-level Feature Groups

| Feature Family | Features | Computation | Leakage Guard | Example columns |
| --- | --- | --- | --- | --- |
| **Win streaks** | Home/away team streak | All-time history, shifted | `.shift(1)` before expanding | `home_team_win_streak`, `away_team_win_streak` |
| **Form (rolling)** | Last-3 and last-5 score averages | Rolling window, shifted | `.shift(1)` before rolling | `home_team_form_last3_score_avg`, `home_team_form_last5_score_avg` |
| **Form (win rate)** | Last-5 games win % | Rolling 5 games, shifted | `.shift(1)` before rolling | `home_team_form_last5_win_rate`, `away_team_form_last5_win_rate` |
| **Rest** | Days since previous match | Diff of prior match only | Uses only past `.diff()` | `home_days_rest`, `away_days_rest` |
| **Season progression** | Wins accumulated so far this season | Expanding, reset per year, shifted | `.shift(1)` before expanding | `home_season_wins_so_far`, `away_season_wins_so_far` |
| **Ladder position** | League rank by wins-so-far at match time | Snapshot at (year, round), shifted | `.shift(1)` before snapshot | `home_ladder_position`, `away_ladder_position` |
| **Head-to-head** | Historical W-L record between team pair | Expanding, per team-pair, shifted | `.shift(1)` before expanding | `h2h_home_team_win_rate`, `h2h_home_games_played` |
| **Venue effect** | Team's historical win % at this ground | Expanding, per team-venue, shifted | `.shift(1)` before expanding; **small-sample risk** at rarely-visited grounds | `home_team_venue_win_rate`, `home_team_venue_games_played` |

### Player-level Feature Groups

| Feature | Computation | Leakage Guard | Coverage | Notes |
| --- | --- | --- | --- | --- |
| `player_form_last5_disposals_avg` | Rolling 5-game average, shifted | `.shift(1)` before rolling, grouped on `player_id` | 98.9% | Uses the real `player_id` (not reconstructed) |
| `player_form_last5_goals_avg` | Rolling 5-game average, shifted | `.shift(1)` before rolling | 98.9% | — |
| `player_form_last5_fantasy_points_avg` | Rolling 5-game average, shifted | `.shift(1)` before rolling | 98.9% | — |
| `player_days_rest` | Diff of prior game only | Uses only past `.diff()` | 98.9% | — |
| `own_team_ladder_position`, `own_team_team_venue_win_rate` | Inherited from team features | Inherited shifts | Varies | Player inherits context from own team |
| `opponent_ladder_position` | Opponent's ladder rank at match time | Inherited shifts | Varies | — |

**Not included (documented gap, not an oversight):** Weather. No source table carries it; enriching would require joining `(venue, match_date)` against a historical weather API + a venue-coordinates reference table.

---

## Train / Holdout Split (Implemented in Notebook Task 5)

**Split strategy:** Strict **time-based split by season** using `time_based_split()` function.

```
Train:   1983–2024 (42 seasons, 7,716 matches)
Holdout: 2025      (1 season, 216 matches)
```

**Why not random split?** A random row-level split would leak both:

1. **Feature leakage:** Rolling form features in training could be computed using holdout match dates (future information relative to the randomly-split row)
2. **Distributional leakage:** Training and test sets would mix eras with different rosters, rule changes, and statistical patterns

**Why time-based by season?** Ensures no rolling feature ever computes using information from after the split boundary.

---

## Realistic Accuracy Ceiling & Leakage Red Flags

**Public benchmarks (bookmakers, Elo-style models):** Match-winner accuracy **65-70%** across a full season.

**Why this ceiling?** AFL has genuine irreducible randomness:

- Injury/suspension changes to playing roster (not in pre-match features)
- Umpiring decisions and their variance game-to-game
- Weather effects (not available in dataset)
- One-off individual brilliance and motivation swings
- Draws (rare but real; hard to predict in binary framing)

**Leakage red flags:**

- **Holdout accuracy >> 75%** → audit for same-match features (e.g., accidentally including opponent's stats or match result in your features)
- **Mis-shifted rolling windows** → rolling computed *before* shifting backwards, leaking future information
- **Non-time-based split** → test set includes eras with different rule regimes or team compositions

---

## Data Quality Findings

| Check | Result | Notes |
| ------- | -------- | ------- |
| **Nulls** | Minimal (2 rows in average columns) | Largely clean dataset |
| **Duplicates** | 0 exact row duplicates | After cleaning |
| **Team name consistency** | ✅ All 20 teams match across tables | Verified in Cell 11 |
| **Date range** | 1983–2025 | ~42 seasons |
| **Match IDs** | 7,904 unique (7,932 in feature table) | 2 rows per match (home/away) |
| **Player identity** | `player_id` is reliable | Real player key, not row ID; 98.9% coverage for form features |
| **Interstate travel mappings** | 4% coverage (353 of 7,904 away games) | Venue-state mapping incomplete; use with caution |

---

## Position Proxy (for role-normalized "top-N" targets)

When position data is unavailable, a **stat-based position proxy** is constructed (documented in notebook Task 3.5):

- **High hit-outs** → Ruck-like
- **High rebound-50s** → Defender-like  
- **High inside-50s** → Forward-like
- **Else** → Midfielder-like

**Label:** "Exploratory proxy, not ground-truth." Use for EDA and role-normalized targets; do not rely for position-specific domain insights without validation.

---

## Summary: What's in the Feature Table

**Match-level table** (`afl_match_features_v2.csv` / `.parquet`):

- **7,932 rows** = unique matches (home-team perspective)
- **41 columns** = match identifiers + team form/context features + head-to-head + venue + ladder position + target labels
- **Ready for:** Match-winner prediction model (classification)

**Player-level table** (`afl_player_features_v2.csv` / `.parquet`):

- **274,403 rows** = unique player-game performances
- **17 columns** = player identifiers + player form (last-5) + own-team context + opponent context + target labels
- **98.9% coverage** for player rolling features (due to reliable `player_id`)
- **Ready for:** Per-player "top-5" prediction models (classification), top-player leaderboard models, fantasy points regression

Both tables have been **time-based split** (train 1983–2024, holdout 2025) and are ready for Day 2 model building.