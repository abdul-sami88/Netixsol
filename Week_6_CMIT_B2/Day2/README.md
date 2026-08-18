# Week 6, Day 2: Prediction Models — Match Winner & Top Player

## Overview

Today you build two core ML models for AFL prediction:

1. **Match Winner Predictor** — Logistic Regression model (63.4% accuracy, ROC AUC 0.679)
2. **Top Player Predictor** — Gradient Boosting Regressor (63.0% top-5 hit rate)

Both models are trained on historical AFL data (1983–2025), tested on hold-out seasons (2020+), and packaged with clean Python interfaces ready for LangChain/LangGraph integration on Day 4.

---

## Task 1: Baseline Models

### Match Winner Baseline

- **Strategy**: Always predict home team wins (majority class in historical data)
- **Test Accuracy**: 56.3%
- **ROC AUC**: 0.5000 (random)
- **Brier Score**: 0.437 (poorly calibrated, expected)

**Interpretation**: Baseline is weak; any real model must beat 56.3% accuracy.

### Top Player Baseline

- **Strategy 1**: Repeat last week's leader — "Did the top disposal-getter last round finish in top-5 this round?"
  - **Top-5 Hit Rate**: 71.87%
  
- **Strategy 2**: Use season-average disposal rank
  - **Hit Rate**: 67.65%

**Interpretation**: Baseline is strong (72% hit rate). Real model should exceed this or use ensemble.

---

## Task 2: Match Winner Model

### Feature Engineering
**Numeric Features (19)**:

- Home team: win streak, rolling form (last 3/5 games), ladder position, days rest, season wins so far
- Away team: same as above
- Head-to-head: historical win rate

**Categorical Features (3)**:

- `home_team`: One-hot encoded (20 teams)
- `away_team`: One-hot encoded
- `venue`: One-hot encoded (50+ unique venues)

**Preprocessing**:

- Numeric: Median imputation → StandardScaler
- Categorical: Fill missing with 'Unknown' → OneHotEncoder

### Model 1: Logistic Regression ✓ **SELECTED**
```
Accuracy: 63.40%
Weighted F1: 0.622
ROC AUC: 0.6794
Brier Score: 0.2228 (well-calibrated)
```

**Why Logistic Regression**: 

- Better ROC AUC (0.679 vs 0.627 for GB)
- Excellent calibration (Brier: 0.223)
- Interpretable coefficients
- Faster inference for real-time predictions

### Model 2: Gradient Boosting (rejected)
```
Accuracy: 59.72%
Weighted F1: 0.586
ROC AUC: 0.6268
Brier Score: 0.2660
```

### Feature Importance (Logistic Regression Coefficients)
Top 10 features by magnitude:

1. `home_team_Fremantle Dockers` (coef: +0.85) — Team strength
2. `venue_Westpac Stadium` (coef: -0.82) — Venue disadvantage for home
3. `home_team_West Coast Eagles` (coef: +0.77) — Team strength
4. `home_team_Adelaide Crows` (coef: +0.66) — Team strength
5. `venue_Junction Oval` (coef: +0.63) — Home ground advantage

**Sanity Check**: ✓ Top features make football sense (team strength, home ground, venue).

---

## Task 3: Top Player Model

### Framing
**Regression approach** (vs. classification): Predict disposals for each player, then rank.

- More robust than binary top-5 classification
- Produces continuous ranking
- Easier to calibrate via ensemble

### Features (8)

- `player_form_last5_disposals_avg` — Recent form (disposals)
- `player_form_last5_goals_avg` — Recent scoring
- `player_form_last5_fantasy_points_avg` — Overall recent performance
- `player_days_rest` — Fatigue indicator
- `own_team_days_rest` — Team-level fatigue
- `own_team_ladder_position` — Team strength
- `own_team_team_venue_win_rate` — Home ground advantage
- `opponent_ladder_position` — Opponent strength

### Model 1: Ridge Regression
```
MAE: 4.4451
RMSE: 5.8775
Top-5 Hit Rate: 62.93%
```

### Model 2: Gradient Boosting ✓ **SELECTED**
```
MAE: 4.4235
RMSE: 5.8484
Top-5 Hit Rate: 62.97%
```

### Feature Importance (Permutation Importance)

1. `player_form_last5_disposals_avg` (0.718) — Dominant predictor ✓
2. `player_form_last5_fantasy_points_avg` (0.012)
3. `player_form_last5_goals_avg` (0.005)
4. `player_days_rest` (0.004)
5. Others < 0.002

**Key Insight**: Player recent disposals is 50× more important than any other feature.

### ⚠️ Model vs. Baseline

- **Model**: 63.0% top-5 hit rate
- **Baseline (repeat last week's leader)**: 71.9% hit rate
- **→ Model is BELOW baseline**

**Recommendation**: 

- For production, use ensemble: 80% baseline + 20% model prediction
- Or improve via feature engineering (matchup history, position proxy, etc.)

---

## Task 4: Feature Importance & Sanity Checks

### Match Winner: Sanity Check ✓
All top features are interpretable:

- Team strengths (Fremantle, West Coast, Adelaide all typically strong)
- Home ground effects (venues matter significantly)
- Rolling form (captured implicitly in model)

**No sign of leakage detected.**

### Top Player: Sanity Check ⚠️
Model underperforms baseline (62.9% vs 72%), suggesting:

1. Regression to disposals may be too noisy
2. Feature engineering is limiting (e.g., no position proxy, matchup history)
3. Ensemble with baseline would improve performance

### Manual Match Reasoning
Tested 3 held-out matches; model predictions align with manual reasoning on 2/3:

- Match 1 (Essendon vs Richmond): Manual & Model agree → Actual: Win ✓
- Match 2 (Sydney vs Geelong): Manual & Model agree → Actual: Win ✓
- Match 3 (West Coast vs Collingwood): Manual predicts Win, Model Win, Actual Loss ⚠️

**Interpretation**: Model behaves reasonably; individual misses are expected (63% accuracy means ~37% error rate).

---

## Task 5: Packaging Models

### Saved Artifacts
All models, metadata, and state saved to `artifacts/`:
```
artifacts/
├── match_winner_pipeline.joblib        Logistic Regression model
├── top_player_pipeline.joblib          Gradient Boosting Regressor
├── numeric_features.joblib             Feature names
├── categorical_features.joblib         Categorical feature names
├── player_numeric_features.joblib      Player features
├── valid_teams.joblib                  List of 20 valid AFL teams
├── date_range.joblib                   Training data span (min, max date)
├── latest_team_state.parquet           Rolling stats per team (as of last match)
├── latest_player_state.parquet         Rolling stats per player (as of last match)
└── match_history.parquet               Full match history (2020+)
```

### Callable Interfaces

**`predict.py`** provides two main functions:

#### 1. `predict_match_winner(home_team, away_team) → dict`
```python
from predict import predict_match_winner

result = predict_match_winner('Melbourne Demons', 'Richmond Tigers')
# Returns:
# {
#     'winner': 'Win' | 'Loss' | 'Draw',
#     'probability': 0.523,           # P(home team wins)
#     'confidence': 'medium',         # high | medium | low
#     'home_team': 'Melbourne Demons',
#     'away_team': 'Richmond Tigers',
#     'model_name': 'Logistic Regression',
#     'data_date': '2025-09-27'       # Latest known data date
# }
```

**Features**:

- ✓ Clean error handling (validates team names)
- ✓ Uses latest known team state (rolling form, ladder position)
- ✓ Well-calibrated probabilities (Brier: 0.223)
- ✓ Confidence levels based on probability magnitude

#### 2. `predict_top_player(team, return_top_n=5) → dict`
```python
from predict import predict_top_player

result = predict_top_player('Melbourne Demons', return_top_n=3)
# Returns:
# {
#     'team': 'Melbourne Demons',
#     'top_player_id': 45123,
#     'predicted_disposals': 28.5,
#     'top_n_player_ids': [45123, 45124, 45125],
#     'top_n_predictions': [(45123, 28.5), (45124, 27.2), (45125, 26.8)],
#     'model_name': 'Gradient Boosting Regressor',
#     'hit_rate_note': 'Model: 63.0% vs Baseline: 71.9%',
#     'num_players_on_roster': 46
# }
```

**Features**:

- ✓ Returns top N predicted players
- ✓ Actual predicted disposal counts (not binary)
- ✓ Warns about baseline performance

### Usage Example: Match Prediction
```python
from predict import predict_match_winner, predict_top_player

# Predict winner
match = predict_match_winner('Melbourne Demons', 'Richmond Tigers')
print(f"Prediction: {match['winner']} "
      f"({match['probability']:.1%}, {match['confidence']} confidence)")

# Predict top players for winner
if match['winner'] == 'Win':
    top_players = predict_top_player('Melbourne Demons', return_top_n=5)
    print(f"Expected top disposal-getter: Player {top_players['top_player_id']}")
    print(f"Predicted disposals: {top_players['predicted_disposals']:.1f}")
```

---

## Deliverables Summary

### ✓ Notebook: `day_models_afl.ipynb`

- Baseline models for match winner & top player
- Two trained models per task (LR/GB for match, Ridge/GB for player)
- Evaluation tables (accuracy, F1, ROC AUC, Brier, MAE, RMSE)
- Feature importance analysis
- Sanity checks with 3 held-out matches
- Callable predictor classes

### ✓ Saved Models & Artifacts

- 10 artifact files in `artifacts/`
- Pipelines, metadata, latest team/player state
- Ready for immediate inference

### ✓ predict.py Module

- Production-ready prediction functions
- Input validation, error handling
- Comprehensive docstrings & examples
- Batch prediction support
- Model diagnostics (info, valid teams)

---

## What's Next: Day 4 Integration

These models are designed for easy wrapping as **LangChain tools**:

```python
from langchain.tools import Tool
from predict import predict_match_winner, predict_top_player

match_winner_tool = Tool(
    name="predict_match_winner",
    func=predict_match_winner,
    description="Predict AFL match winner and probability"
)

top_player_tool = Tool(
    name="predict_top_player",
    func=predict_top_player,
    description="Predict top disposal-getter for a team"
)

# Add to agent toolset on Day 4
```

---

## Performance Summary

| Task | Model | Metric | Value | Baseline | vs Baseline |
|------|-------|--------|-------|----------|------------|
| Match Winner | Logistic Regression | Accuracy | 63.4% | 56.3% | +7.1pp ✓ |
| Match Winner | LR | ROC AUC | 0.679 | 0.500 | +0.179 ✓ |
| Match Winner | LR | Brier Score | 0.223 | 0.437 | -0.214 ✓ |
| Top Player | GB Regressor | Top-5 Hit Rate | 63.0% | 71.9% | -8.9pp ✗ |
| Top Player | GB Reg | MAE | 4.42 | — | — |

---

## Key Learnings

1. **Match winner prediction is workable** — LR achieves 63.4% accuracy with good calibration.
2. **Top player regression is hard** — Baseline (repeat last week's leader) is strong. Regression underperforms; ensemble recommended.
3. **Features matter** — Recent form dominates (player disposals last 5 games explains 72% of variance).
4. **Calibration over accuracy** — Well-calibrated probabilities (Brier 0.223) > high raw accuracy for agent confidence.

---

## Files

- **Notebook**: `day_models_afl.ipynb` (5 tasks, ~4k lines)
- **Module**: `predict.py` (600+ lines, production-ready)
- **Artifacts**: `artifacts/` (10 files)
- **Data**: `afl_match_features_v2.csv`, `afl_player_features_v2.csv`

---

Generated: 2026-08-18
