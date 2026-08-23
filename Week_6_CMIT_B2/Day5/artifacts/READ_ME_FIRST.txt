READ ME FIRST
=============

REAL (your actual Day 2 files, used as-is):
  - match_winner_pipeline.joblib
  - top_player_pipeline.joblib

SYNTHETIC (small, schema-matching stand-ins I generated so predict.py's
import-time artifact loading succeeds and the pipeline is testable locally
-- replace all of these with your real Day2/artifacts/ contents):
  - categorical_features.joblib
  - numeric_features.joblib
  - player_numeric_features.joblib
  - valid_teams.joblib
  - date_range.joblib
  - latest_team_state.parquet
  - latest_player_state.parquet
  - match_history.parquet

To go live: copy your real Day2/artifacts/ folder over this entire
directory (the two pipeline .joblib files are already correct -- keeping
your real copies is fine either way, they're identical).
