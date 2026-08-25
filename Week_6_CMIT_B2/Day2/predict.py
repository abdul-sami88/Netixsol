"""
predict.py — AFL Match Winner & Top Player Predictor
======================================================

This module provides clean, production-ready interfaces for:
1. Predicting match winners with probabilities
2. Predicting top disposal-getter for a match

Models trained on AFL data (1983-2025), tested on 2020+ seasons.

Usage:
------
    from predict import predict_match_winner, predict_top_player
    
    # Match prediction
    result = predict_match_winner('Melbourne Demons', 'Richmond Tigers')
    print(f"{result['winner']} with {result['probability']:.2%} confidence")
    
    # Top player prediction
    top = predict_top_player('Melbourne Demons')
    print(f"Predicted top: Player ID {top['player_id']}")

Models & Performance:
---------------------
Match Winner (Logistic Regression):
  - Test Accuracy: 63.4%
  - ROC AUC: 0.679
  - Brier Score: 0.223 (well-calibrated)
  - Baseline: 56.3% (always predict home win)

Top Player (Gradient Boosting Regressor):
  - Top-5 Hit Rate: 63.0%
  - MAE: 4.42 disposals
  - Baseline: 71.9% (last week's leader repeats)

Data Artifacts:
---------------
artifacts/
  ├── match_winner_pipeline.joblib      Trained LR model
  ├── top_player_pipeline.joblib        Trained GB regressor
  ├── numeric_features.joblib           Feature names (numeric)
  ├── categorical_features.joblib       Feature names (categorical)
  ├── player_numeric_features.joblib    Player feature names
  ├── valid_teams.joblib               Valid team names
  └── date_range.joblib                Training data date range

Team/player "current state" features (win streak, recent form, ladder
position, venue history, head-to-head record, player rolling averages) are
read directly from afl_match_features_v2.csv / afl_player_features_v2.csv
(the same files ai_chat_afl.py uses for retrieval) via ai_chat_afl's own
cached readers -- taking each team's/player's most recent row. These files
already have every feature the models were trained on, correctly computed
with no leakage (see AFL_Data_Foundations_Complete.ipynb, Task 4). An
earlier version of this module read a separate, much more limited
`latest_team_state.parquet` / `latest_player_state.parquet` snapshot (only
3 of 9 team features, 1 of 8 player features) which silently starved the
models of most of their trained signal -- this version fixes that by using
the full feature tables directly as the single source of truth, instead of
a lossy intermediate export.
"""

import os
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# ============================================================================
# CONFIGURATION & ARTIFACT LOADING
# ============================================================================

_DIR = Path(__file__).parent.absolute()
_ARTIFACTS = _DIR / "artifacts"

# Validate artifacts exist
if not _ARTIFACTS.exists():
    raise FileNotFoundError(
        f"Artifacts directory not found at {_ARTIFACTS}. "
        f"Run Day 2 notebook to generate models."
    )

# Load all artifacts
try:
    _match_model = joblib.load(_ARTIFACTS / "match_winner_pipeline.joblib")
    _player_model = joblib.load(_ARTIFACTS / "top_player_pipeline.joblib")
    _numeric_features = joblib.load(_ARTIFACTS / "numeric_features.joblib")
    _categorical_features = joblib.load(_ARTIFACTS / "categorical_features.joblib")
    _player_numeric_features = joblib.load(_ARTIFACTS / "player_numeric_features.joblib")
    _valid_teams = joblib.load(_ARTIFACTS / "valid_teams.joblib")
    _data_min_date, _data_max_date = joblib.load(_ARTIFACTS / "date_range.joblib")

except FileNotFoundError as e:
    raise RuntimeError(f"Failed to load model artifacts: {e}")

# Full feature tables -- the actual source of truth for "current team/player
# state", reusing ai_chat_afl's cached readers so there's one copy of this
# data in memory, not two. Optional: if ai_chat_afl / its CSVs aren't
# available in a given environment, fall back to the legacy parquet
# snapshots (if present) rather than hard-crashing the whole module.
_USE_FULL_FEATURE_TABLES = False
try:
    from ai_chat_afl import _read_match_features, _read_player_features
    _match_features_df = _read_match_features()
    _player_features_df = _read_player_features()
    _USE_FULL_FEATURE_TABLES = True
except Exception as _feature_table_error:
    _match_features_df = None
    _player_features_df = None
    # Legacy fallback -- only used if the rich feature CSVs genuinely aren't
    # reachable. Produces much weaker predictions (see module docstring).
    try:
        _latest_team_state = pd.read_parquet(_ARTIFACTS / "latest_team_state.parquet")
        _latest_player_state = pd.read_parquet(_ARTIFACTS / "latest_player_state.parquet")
        _match_history = pd.read_parquet(_ARTIFACTS / "match_history.parquet")
    except FileNotFoundError:
        _latest_team_state = _latest_player_state = _match_history = None

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _validate_team(team_name: str) -> None:
    """Validate team name against known AFL teams."""
    if team_name not in _valid_teams:
        raise ValueError(
            f"Unknown team: '{team_name}'. "
            f"Valid teams: {', '.join(sorted(_valid_teams))}"
        )

def _get_team_features(team: str) -> Dict:
    """Get the latest known rolling-form state for a team.

    Primary path (_USE_FULL_FEATURE_TABLES): read directly from
    afl_match_features_v2.csv -- find this team's most recent match (as
    either home or away) and pull off ALL 9 of their own-side trained
    features (win_streak, both score averages, form win rate, days_rest,
    season_wins, ladder_position, venue_win_rate, venue_games_played),
    correctly using whichever home_/away_ prefix applies to the side they
    were actually on. This is the fix for the original bug where only 3 of
    these 9 were ever populated (see module docstring).

    Fallback path: the legacy latest_team_state.parquet snapshot, which
    only ever carried 3 of these 9 fields -- kept only so the module
    doesn't hard-crash if the full feature CSVs aren't reachable in a given
    environment; predictions will be materially weaker on this path.
    """
    if _USE_FULL_FEATURE_TABLES:
        df = _match_features_df
        rows = df[(df['home_team'] == team) | (df['away_team'] == team)]
        if rows.empty:
            return _default_team_features()
        row = rows.sort_values('match_date').iloc[-1]
        is_home = row['home_team'] == team
        prefix = 'home_' if is_home else 'away_'
        return {
            'win_streak': row.get(f'{prefix}team_win_streak', np.nan),
            'form_last5_score_avg': row.get(f'{prefix}team_form_last5_score_avg', np.nan),
            'form_last3_score_avg': row.get(f'{prefix}team_form_last3_score_avg', np.nan),
            'form_last5_win_rate': row.get(f'{prefix}team_form_last5_win_rate', 0.5),
            'days_rest': row.get(f'{prefix}days_rest', np.nan),
            'season_wins': row.get(f'{prefix}season_wins_so_far', 0.0),
            'ladder_position': row.get(f'{prefix}ladder_position', 10.0),
            'venue_win_rate': row.get(f'{prefix}team_venue_win_rate', np.nan),
            'venue_games_played': row.get(f'{prefix}team_venue_games_played', np.nan),
            'last_date': row.get('match_date', None),
        }

    # --- legacy fallback (team-as-column/index robustness fix retained) ---
    df = _latest_team_state
    row = None
    if df is not None:
        if 'team' in df.columns:
            matches = df[df['team'] == team]
            if not matches.empty:
                if 'match_date' in matches.columns:
                    matches = matches.sort_values('match_date')
                row = matches.iloc[-1]
        elif team in df.index:
            row = df.loc[team]
            if isinstance(row, pd.DataFrame):
                row = row.sort_values('match_date').iloc[-1] if 'match_date' in row.columns else row.iloc[-1]

    if row is None:
        return _default_team_features()

    return {
        'win_streak': np.nan, 'form_last5_score_avg': np.nan, 'form_last3_score_avg': np.nan,
        'form_last5_win_rate': row.get('home_team_form_last5_win_rate', 0.5),
        'days_rest': np.nan,
        'season_wins': row.get('home_season_wins_so_far', 0.0),
        'ladder_position': row.get('home_ladder_position', 10.0),
        'venue_win_rate': np.nan, 'venue_games_played': np.nan,
        'last_date': row.get('match_date', None),
    }


def _default_team_features() -> Dict:
    return {
        'win_streak': np.nan, 'form_last5_score_avg': np.nan, 'form_last3_score_avg': np.nan,
        'form_last5_win_rate': 0.5, 'days_rest': np.nan, 'season_wins': 0.0,
        'ladder_position': 10.0, 'venue_win_rate': np.nan, 'venue_games_played': np.nan,
        'last_date': None,
    }


def _team_result(row, team: str) -> str:
    """Return 'Win'/'Loss'/'Draw' from `team`'s own perspective for one
    match row (match_result is recorded from the home team's perspective,
    so flip it if `team` was the away side)."""
    if row['home_team'] == team:
        return row['match_result']
    flip = {'Win': 'Loss', 'Loss': 'Win', 'Draw': 'Draw'}
    return flip.get(row['match_result'], row['match_result'])


def _h2h_win_rate(team_a: str, team_b: str) -> Optional[float]:
    """team_a's historical win rate against team_b specifically. Uses the
    full match feature table (all historical meetings) when available,
    falling back to the legacy match_history snapshot otherwise."""
    df = _match_features_df if _USE_FULL_FEATURE_TABLES else _match_history
    if df is None:
        return None
    mask = ((df['home_team'] == team_a) & (df['away_team'] == team_b)) | \
           ((df['home_team'] == team_b) & (df['away_team'] == team_a))
    meetings = df[mask]
    if meetings.empty:
        return None
    wins = sum(1 for _, row in meetings.iterrows() if _team_result(row, team_a) == 'Win')
    return wins / len(meetings)

# ============================================================================
# PUBLIC API: MATCH WINNER PREDICTION
# ============================================================================

def predict_match_winner(
    home_team: str,
    away_team: str,
    verbose: bool = False
) -> Dict[str, any]:
    """
    Predict AFL match winner and win probability.
    
    Args:
        home_team (str): Home team name (exact match required)
        away_team (str): Away team name (exact match required)
        verbose (bool): Print debug info
    
    Returns:
        dict with keys:
            - 'winner': Predicted outcome ('Win'/'Loss'/'Draw')
            - 'probability': P(home team wins) in [0, 1]
            - 'confidence': 'high'/'medium'/'low' based on probability
            - 'home_team': Input home team
            - 'away_team': Input away team
            - 'model_name': 'Logistic Regression'
    
    Raises:
        ValueError: If team names invalid or missing features
    
    Examples:
        >>> result = predict_match_winner('Melbourne Demons', 'Richmond Tigers')
        >>> print(f"Prediction: {result['winner']} with {result['probability']:.1%} confidence")
        Prediction: Win with 52.3% confidence
    
    Notes:
        - Uses latest known team state (rolling form, ladder position)
        - Features are 3-5 days stale by end of season (before next round)
        - Probability is well-calibrated (Brier: 0.223) for reliable confidence
        - Venue is set to 'Unknown' if not provided (uses default calibration)
    """
    # Validate inputs
    _validate_team(home_team)
    _validate_team(away_team)
    
    if verbose:
        print(f"[predict_match_winner] Predicting: {home_team} vs {away_team}")
    
    # Build feature vector from latest team state
    feature_dict = {}
    
    # Add numeric features -- ALL 9 per side now come from _get_team_features
    # (sourced from the full afl_match_features_v2.csv when available), not
    # just the 3 the original code populated.
    home_features = _get_team_features(home_team)
    away_features = _get_team_features(away_team)
    h2h = _h2h_win_rate(home_team, away_team)

    _FEATURE_KEY_MAP = {
        'win_streak': 'win_streak',
        'form_last5_score_avg': 'form_last5_score_avg',
        'form_last3_score_avg': 'form_last3_score_avg',
        'form_last5_win_rate': 'form_last5_win_rate',
        'days_rest': 'days_rest',
        'season_wins_so_far': 'season_wins',
        'ladder_position': 'ladder_position',
        'venue_win_rate': 'venue_win_rate',
        'venue_games_played': 'venue_games_played',
    }

    # Any field genuinely unavailable even from the full feature table (e.g.
    # a brand-new team with no match history yet) comes through as NaN from
    # _get_team_features/_default_team_features, and the pipeline's own
    # trained median imputer fills it -- an in-distribution neutral value,
    # never a hardcoded out-of-distribution constant.
    for feat in _numeric_features:
        if feat == 'h2h_home_team_win_rate':
            feature_dict[feat] = h2h if h2h is not None else np.nan
            continue
        for suffix, src_key in _FEATURE_KEY_MAP.items():
            if feat == f'home_team_{suffix}' or feat == f'home_{suffix}':
                feature_dict[feat] = home_features[src_key]
                break
            if feat == f'away_team_{suffix}' or feat == f'away_{suffix}':
                feature_dict[feat] = away_features[src_key]
                break
        else:
            feature_dict[feat] = np.nan
    
    # Add categorical features
    feature_dict['home_team'] = home_team
    feature_dict['away_team'] = away_team
    feature_dict['venue'] = 'Unknown'  # Default: unknown venue
    
    # Create DataFrame and predict
    X_pred = pd.DataFrame([feature_dict])
    
    try:
        y_pred_class = _match_model.predict(X_pred)[0]
        y_pred_proba = _match_model.predict_proba(X_pred)[0]
        
        # Get Win probability
        classes = _match_model.named_steps['classifier'].classes_
        win_idx = list(classes).index('Win')
        win_prob = float(y_pred_proba[win_idx])
        loss_idx = list(classes).index('Loss')
        loss_prob = float(y_pred_proba[loss_idx])
        draw_idx = list(classes).index('Draw')
        draw_prob = float(y_pred_proba[draw_idx])

        # Determine confidence -- based on the WINNING side's probability,
        # not win_prob specifically. win_prob is always P(home team wins);
        # a confidently-predicted AWAY win has a LOW win_prob (e.g. 0.17),
        # which is just as confident a prediction as a high win_prob, just
        # for the other team. Bucketing on win_prob alone mislabeled
        # confident away-team predictions as "low confidence".
        if y_pred_class == 'Win':
            _outcome_prob_for_confidence = win_prob
        elif y_pred_class == 'Loss':
            _outcome_prob_for_confidence = loss_prob
        else:
            _outcome_prob_for_confidence = draw_prob

        if _outcome_prob_for_confidence > 0.65:
            confidence = 'high'
        elif _outcome_prob_for_confidence > 0.55:
            confidence = 'medium'
        else:
            confidence = 'low'

        # Map prediction outcome to team name
        if y_pred_class == 'Win':
            winner_name = home_team
            winner_probability = win_prob
        elif y_pred_class == 'Loss':
            winner_name = away_team
            winner_probability = loss_prob
        else:  # 'Draw'
            winner_name = 'Draw'
            winner_probability = draw_prob
            
        result = {
            'winner': winner_name,  # ← Now returns team name
            'prediction_outcome': y_pred_class,
            'probability': win_prob,  # kept for backward compat -- ALWAYS P(home team wins), regardless of who 'winner' is
            'winner_probability': winner_probability,  # NEW -- the probability of the actually-predicted outcome (correct number to display next to 'winner')
            'home_win_probability': win_prob,
            'away_win_probability': loss_prob,
            'draw_probability': draw_prob,
            'confidence': confidence,
            'home_team': home_team,
            'away_team': away_team,
            'model_name': 'Logistic Regression',
            'data_date': str(home_features['last_date'][:10] if home_features['last_date'] else 'unknown')
        }
        
        if verbose:
            print(f"  → Prediction: {y_pred_class} (p={win_prob:.3f}, confidence={confidence})")
        
        return result
        
    except Exception as e:
        raise RuntimeError(f"Prediction failed for {home_team} vs {away_team}: {e}")


# ============================================================================
# PUBLIC API: TOP PLAYER PREDICTION
# ============================================================================

def predict_top_player(
    team: str,
    return_top_n: int = 5,
    verbose: bool = False,
    opponent: Optional[str] = None
) -> Dict[str, any]:
    """
    Predict top disposal-getter for a team in their next match.
    
    Args:
        team (str): Team name (exact match required)
        return_top_n (int): Return top N predicted players (default: 5)
        verbose (bool): Print debug info
        opponent (str, optional): Opponent team name, if known -- lets
            opponent_ladder_position be filled in for real instead of NaN.
    
    Returns:
        dict with keys:
            - 'team': Input team name
            - 'top_player_id': Predicted top player ID
            - 'predicted_disposals': Predicted disposals for top player
            - 'top_n_player_ids': List of top N predicted player IDs
            - 'top_n_predictions': List of (player_id, predicted_disposals) tuples
            - 'model_name': 'Gradient Boosting Regressor'
            - 'hit_rate_note': Note about model performance vs baseline
    
    Raises:
        ValueError: If team name invalid or no players found
    
    Examples:
        >>> top = predict_top_player('Melbourne Demons', return_top_n=3)
        >>> print(f"Top player predicted: ID {top['top_player_id']}")
        Top player predicted: ID 45123
    
    Notes:
        - Model achieves 63% top-5 hit rate vs 72% baseline (last week's leader)
        - Predictions based on all 8 trained player features, read directly
          from afl_player_features_v2.csv (the same file ai_chat_afl.py uses
          for retrieval) when available -- player recent form (disposals,
          goals, fantasy points), player/team days rest, team ladder
          position, and team venue win rate. Only opponent_ladder_position
          remains unknown unless `opponent` is passed, since it depends on
          a specific upcoming fixture rather than historical state.
        - For more robust top-performer identification, consider ensemble
          with simpler "last week's top player" baseline
    """
    # Validate input
    _validate_team(team)
    if opponent is not None:
        _validate_team(opponent)
    
    if verbose:
        print(f"[predict_top_player] Predicting top disposal-getter for {team}")

    # Team-level context computed once (shared by every player on the roster)
    own_team_state = _get_team_features(team)
    opponent_ladder_position = _get_team_features(opponent)['ladder_position'] if opponent else np.nan

    if _USE_FULL_FEATURE_TABLES:
        # Primary path: afl_player_features_v2.csv already has ALL 8 trained
        # player features correctly computed (see AFL_Data_Foundations_
        # Complete.ipynb, Task 4.4) -- take each player's most recent row.
        df = _player_features_df
        player_key = 'player_id' if 'player_id' in df.columns else df.index.name or 'player_id'
        team_rows = df[df['team'] == team]
        if team_rows.empty:
            raise ValueError(f"No player data found for team: {team}")
        latest_per_player = (
            team_rows.sort_values('match_date').groupby(player_key, as_index=False).tail(1)
        )
        team_players = latest_per_player.set_index(player_key)
    else:
        # Legacy fallback -- latest_player_state.parquet only ever carried
        # 1 of 8 trained player features (see module docstring).
        team_players = _latest_player_state[_latest_player_state['team'] == team]

    if len(team_players) == 0:
        raise ValueError(f"No player data found for team: {team}")
    
    # Create feature vectors for each player
    feature_rows = []
    player_ids = []
    
    for player_id, row in team_players.iterrows():
        # Build feature dict -- real values from the feature table where
        # available, NaN (not 0.0) where genuinely unavailable, so the
        # pipeline's own trained median imputer fills a sensible default
        # instead of an out-of-distribution constant.
        feat_dict = {}
        for feat in _player_numeric_features:
            if feat == 'player_days_rest' and not _USE_FULL_FEATURE_TABLES:
                # afl_player_features_v2.csv already has a real
                # player_days_rest column; only the legacy path needs to
                # derive it from a raw match_date.
                match_date = row.get('match_date') if 'match_date' in row.index else None
                if pd.notna(match_date):
                    days = (pd.Timestamp.now().normalize() - pd.to_datetime(match_date)).days
                    feat_dict[feat] = float(days) if 0 <= days <= 30 else np.nan
                else:
                    feat_dict[feat] = np.nan
            elif feat == 'own_team_days_rest' and not _USE_FULL_FEATURE_TABLES:
                feat_dict[feat] = own_team_state['days_rest']
            elif feat == 'own_team_ladder_position' and not _USE_FULL_FEATURE_TABLES:
                feat_dict[feat] = own_team_state['ladder_position']
            elif feat == 'opponent_ladder_position' and opponent is not None:
                # Explicit opponent always wins, even on the primary path,
                # since the feature table's own opponent_ladder_position
                # reflects a past match's opponent, not the one being asked
                # about now.
                feat_dict[feat] = opponent_ladder_position
            elif feat in row.index and pd.notna(row[feat]):
                feat_dict[feat] = float(row[feat])
            else:
                # Genuinely unavailable (e.g. opponent_ladder_position with
                # no opponent given, or a field missing on the legacy
                # fallback path). NaN -> trained median imputer.
                feat_dict[feat] = np.nan
        
        feature_rows.append(feat_dict)
        player_ids.append(player_id)
    
    X_pred = pd.DataFrame(feature_rows)
    
    try:
        # Predict disposals for each player
        y_pred = _player_model.predict(X_pred)
        
        # Get rankings
        rankings = list(zip(player_ids, y_pred))
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        top_player_id = rankings[0][0]
        top_disposals = rankings[0][1]
        
        # Return top N
        top_n_list = rankings[:return_top_n]
        
        result = {
            'team': team,
            'top_player_id': int(top_player_id),
            'predicted_disposals': float(top_disposals),
            'top_n_player_ids': [int(pid) for pid, _ in top_n_list],
            'top_n_predictions': [(int(pid), float(disp)) for pid, disp in top_n_list],
            'model_name': 'Gradient Boosting Regressor',
            'hit_rate_note': 'Model: 63.0% vs Baseline: 71.9% (last week leader repeats)',
            'num_players_on_roster': len(player_ids)
        }
        
        if verbose:
            print(f"  → Top player: ID {top_player_id}, predicted {top_disposals:.1f} disposals")
            print(f"  → Note: Baseline (repeat last week's leader) achieves 71.9% hit rate")
            print(f"  →       This model achieves 63.0% (room for improvement via ensemble)")
        
        return result
        
    except Exception as e:
        raise RuntimeError(f"Prediction failed for {team}: {e}")


# ============================================================================
# BATCH PREDICTION (for LLM integration)
# ============================================================================

def batch_predict_matches(
    matches: List[Tuple[str, str]],
    return_proba: bool = False
) -> List[Dict]:
    """
    Predict outcomes for multiple matches (efficient for batch mode).
    
    Args:
        matches: List of (home_team, away_team) tuples
        return_proba: Include full probability distribution
    
    Returns:
        List of prediction dicts (see predict_match_winner)
    """
    results = []
    for home_team, away_team in matches:
        result = predict_match_winner(home_team, away_team)
        if not return_proba:
            # Remove full probabilities for cleaner output
            pass
        results.append(result)
    return results


# ============================================================================
# DEBUGGING & DIAGNOSTICS
# ============================================================================

def get_model_info() -> Dict[str, any]:
    """
    Return information about loaded models and data.
    
    Returns:
        dict with model names, features, data ranges, etc.
    """
    return {
        'match_model': 'Logistic Regression (sklearn)',
        'match_model_accuracy': 0.634,
        'match_model_roc_auc': 0.679,
        'player_model': 'Gradient Boosting Regressor (sklearn)',
        'player_model_top5_hit_rate': 0.630,
        'data_date_range': (str(_data_min_date), str(_data_max_date)),
        'num_valid_teams': len(_valid_teams),
        'num_match_features': len(_numeric_features) + len(_categorical_features),
        'num_player_features': len(_player_numeric_features),
        'artifacts_path': str(_ARTIFACTS),
        'latest_team_data_date': str(_latest_team_state['match_date'].max()),
        'latest_player_data_date': str(_latest_player_state['match_date'].max()),
    }


def list_valid_teams() -> List[str]:
    """Return list of valid team names."""
    return sorted(_valid_teams)


if __name__ == '__main__':
    # Demo usage
    print("=" * 70)
    print("AFL PREDICTION MODEL DEMO")
    print("=" * 70)
    
    print("\n1. Model Information:")
    info = get_model_info()
    for key, val in info.items():
        print(f"   {key}: {val}")
    
    print("\n2. Valid Teams:")
    teams = list_valid_teams()
    print(f"   {', '.join(teams[:5])} ... ({len(teams)} total)")
    
    print("\n3. Match Winner Prediction:")
    try:
        result = predict_match_winner('Melbourne Demons', 'Richmond Tigers', verbose=True)
        print(f"   Result: {result['winner']} with {result['probability']:.2%} confidence")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n4. Top Player Prediction:")
    try:
        result = predict_top_player('Melbourne Demons', return_top_n=3, verbose=True)
        print(f"   Top 3 players: {result['top_n_player_ids']}")
    except Exception as e:
        print(f"   Error: {e}")
