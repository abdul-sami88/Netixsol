"""
Forecasting Models Suite for ShopKaro Demand Intelligence
Implements Task 2:
1. Baseline Models: Naive and Seasonal Naive (7-day lag)
2. Statistical Time-Series Models: ARIMA / SARIMAX and Holt-Winters ETS (statsmodels)
3. Prophet with Custom Pakistani Festival Holidays & Islamic Calendar Regressors
4. LightGBM Global Regressor with Lag, Rolling, Calendar, and Festival Features
5. Neural Multi-Horizon Forecasting Baseline (PyTorch MLP / N-BEATS style)
"""

import os
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings("ignore")

# Statistical models
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# Prophet
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

# LightGBM
import lightgbm as lgb

# PyTorch Neural
import torch
import torch.nn as nn


# ---------------------------------------------------------------------------
# 1. BASELINE MODELS (Naive & Seasonal Naive)
# ---------------------------------------------------------------------------
class NaiveForecaster:
    """Carries the last observed value forward: y_{t+h} = y_t."""
    def __init__(self):
        self.last_value = None

    def fit(self, y: np.ndarray):
        self.last_value = float(y[-1]) if len(y) > 0 else 0.0
        return self

    def predict(self, horizon: int) -> np.ndarray:
        return np.full(horizon, max(0.0, self.last_value))


class SeasonalNaiveForecaster:
    """Repeats the last observed seasonal cycle: y_{t+h} = y_{t+h-season_length}."""
    def __init__(self, season_length: int = 7):
        self.season_length = season_length
        self.last_cycle = None

    def fit(self, y: np.ndarray):
        if len(y) >= self.season_length:
            self.last_cycle = y[-self.season_length:].copy()
        else:
            self.last_cycle = np.full(self.season_length, np.mean(y) if len(y) > 0 else 0.0)
        return self

    def predict(self, horizon: int) -> np.ndarray:
        repeats = int(np.ceil(horizon / self.season_length))
        preds = np.tile(self.last_cycle, repeats)[:horizon]
        return np.maximum(0.0, preds)


# ---------------------------------------------------------------------------
# 2. STATISTICAL MODELS (ARIMA & ETS)
# ---------------------------------------------------------------------------
class ARIMAForecaster:
    """Auto-Regressive Integrated Moving Average with optional weekly seasonality."""
    def __init__(self, order: Tuple[int, int, int] = (1, 1, 1), 
                 seasonal_order: Tuple[int, int, int, int] = (1, 0, 1, 7)):
        self.order = order
        self.seasonal_order = seasonal_order
        self.fitted_model = None
        self.last_val = 0.0

    def fit(self, y: np.ndarray):
        self.last_val = float(y[-1]) if len(y) > 0 else 0.0
        try:
            model = ARIMA(y, order=self.order, seasonal_order=self.seasonal_order)
            self.fitted_model = model.fit()
        except Exception:
            try:
                # Fallback to simple ARIMA(1, 1, 0)
                model = ARIMA(y, order=(1, 1, 0))
                self.fitted_model = model.fit()
            except Exception:
                self.fitted_model = None
        return self

    def predict(self, horizon: int) -> np.ndarray:
        if self.fitted_model is not None:
            try:
                preds = self.fitted_model.forecast(steps=horizon)
                return np.maximum(0.0, np.array(preds))
            except Exception:
                pass
        return np.full(horizon, max(0.0, self.last_val))


class ETSForecaster:
    """Holt-Winters Exponential Smoothing (Additive Trend & 7-day Additive Seasonality)."""
    def __init__(self, seasonal_periods: int = 7):
        self.seasonal_periods = seasonal_periods
        self.fitted_model = None
        self.last_val = 0.0

    def fit(self, y: np.ndarray):
        self.last_val = float(y[-1]) if len(y) > 0 else 0.0
        # ETS requires positive or non-negative series
        y_adj = np.maximum(1e-4, y.astype(float))
        try:
            model = ExponentialSmoothing(
                y_adj,
                trend="add",
                seasonal="add" if len(y) >= 2 * self.seasonal_periods else None,
                seasonal_periods=self.seasonal_periods if len(y) >= 2 * self.seasonal_periods else None,
                initialization_method="estimated"
            )
            self.fitted_model = model.fit(optimized=True)
        except Exception:
            self.fitted_model = None
        return self

    def predict(self, horizon: int) -> np.ndarray:
        if self.fitted_model is not None:
            try:
                preds = self.fitted_model.forecast(horizon)
                return np.maximum(0.0, np.array(preds))
            except Exception:
                pass
        return np.full(horizon, max(0.0, self.last_val))


# ---------------------------------------------------------------------------
# 3. PROPHET WITH CUSTOM PAKISTANI FESTIVAL HOLIDAYS
# ---------------------------------------------------------------------------
def build_pakistan_festival_holidays(calendar_df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates Prophet-compatible holiday dataframe including moving Islamic dates
    (Eid ul-Fitr, Eid ul-Adha, Ramadan) and fixed national/commercial events (11.11, Azadi Day).
    """
    festivals = calendar_df[calendar_df["is_festival"]].copy()
    if festivals.empty:
        return pd.DataFrame(columns=["holiday", "ds", "lower_window", "upper_window"])
        
    records = []
    for fest_name, group in festivals.groupby("festival_name"):
        ds_dates = group["date"].astype(str).tolist()
        for d in ds_dates:
            records.append({
                "holiday": fest_name,
                "ds": d,
                "lower_window": -2, # Demand surge 2 days prior
                "upper_window": 1   # Demand lingering 1 day after
            })
    return pd.DataFrame(records)


class ProphetForecaster:
    """
    Facebook Prophet model configured for Pakistani retail:
    - Weekly & Yearly Fourier seasonality
    - Moving Islamic festival holidays (Eid, Ramadan) + commercial mega sales (11.11)
    """
    def __init__(self, holidays_df: Optional[pd.DataFrame] = None):
        self.holidays_df = holidays_df
        self.model = None
        self.last_val = 0.0

    def fit(self, df_train: pd.DataFrame):
        """df_train must contain 'ds' (datetime/date) and 'y' (target)."""
        self.last_val = float(df_train["y"].iloc[-1]) if not df_train.empty else 0.0
        if not PROPHET_AVAILABLE:
            return self

        try:
            m = Prophet(
                holidays=self.holidays_df,
                weekly_seasonality=True,
                yearly_seasonality=True,
                daily_seasonality=False,
                changepoint_prior_scale=0.08,
                seasonality_prior_scale=10.0,
                holidays_prior_scale=15.0
            )
            # Suppress console logging
            import logging
            logging.getLogger("prophet").setLevel(logging.ERROR)
            logging.getLogger("cmdstanpy").setLevel(logging.ERROR)
            
            m.fit(df_train[["ds", "y"]])
            self.model = m
        except Exception:
            self.model = None
        return self

    def predict(self, future_dates: pd.DatetimeIndex) -> np.ndarray:
        if self.model is not None:
            try:
                df_future = pd.DataFrame({"ds": future_dates})
                forecast = self.model.predict(df_future)
                return np.maximum(0.0, forecast["yhat"].values)
            except Exception:
                pass
        return np.full(len(future_dates), max(0.0, self.last_val))


# ---------------------------------------------------------------------------
# 4. LIGHTGBM GLOBAL AUTOREGRESSIVE REGRESSOR
# ---------------------------------------------------------------------------
def create_lag_and_rolling_features(df: pd.DataFrame, group_col: str = "category", target_col: str = "units_sold") -> pd.DataFrame:
    """
    Builds rich feature matrix for global GBDT forecasting:
    - Lags: 1, 2, 7, 14, 21, 28 days
    - Rolling window aggregates: 7, 14, 28 days (mean, std, min, max)
    - Calendar features: day_of_week, day_of_month, month, is_weekend, day_of_year
    - Festival indicators & multiplier
    """
    df = df.sort_values([group_col, "date"]).copy()
    
    # Calendar features
    df["day_of_week"] = df["date"].dt.dayofweek
    df["day_of_month"] = df["date"].dt.day
    df["month"] = df["date"].dt.month
    df["is_weekend_int"] = df["is_weekend"].astype(int)
    df["day_of_year"] = df["date"].dt.dayofyear
    df["is_festival_int"] = df["is_festival"].astype(int)
    
    # Cyclical day of week and month encodings (sin/cos)
    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7.0)
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7.0)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12.0)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12.0)
    
    # Lags within each group
    for lag in [1, 2, 7, 14, 21, 28]:
        df[f"lag_{lag}"] = df.groupby(group_col)[target_col].shift(lag)
        
    # Rolling statistics (computed with shift 1 to prevent target leakage!)
    for w in [7, 14, 28]:
        grouped_shifted = df.groupby(group_col)[target_col].shift(1)
        df[f"rolling_mean_{w}"] = grouped_shifted.rolling(window=w, min_periods=1).mean()
        df[f"rolling_std_{w}"] = grouped_shifted.rolling(window=w, min_periods=1).std().fillna(0)
        df[f"rolling_max_{w}"] = grouped_shifted.rolling(window=w, min_periods=1).max()
        df[f"rolling_min_{w}"] = grouped_shifted.rolling(window=w, min_periods=1).min()
        
    # Categorical encoding for group
    df[f"{group_col}_cat"] = df[group_col].astype("category").cat.codes
    return df


class LightGBMGlobalForecaster:
    """
    Global LightGBM autoregressive model trained across all series simultaneously.
    Captures cross-series patterns, festival demand multipliers, and non-linear interactions.
    """
    def __init__(self, objective: str = "regression", alpha: float = 0.5):
        self.objective = objective
        self.alpha = alpha
        self.model = None
        self.feature_cols = []
        self.group_col = "category"

    def fit(self, train_features_df: pd.DataFrame, feature_cols: List[str], target_col: str = "units_sold"):
        self.feature_cols = feature_cols
        clean_df = train_features_df.dropna(subset=self.feature_cols + [target_col])
        
        X = clean_df[self.feature_cols]
        y = clean_df[target_col]
        
        params = {
            "objective": self.objective,
            "metric": "mae",
            "boosting_type": "gbdt",
            "n_estimators": 150,
            "learning_rate": 0.05,
            "num_leaves": 31,
            "min_child_samples": 10,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "random_state": 42,
            "verbosity": -1
        }
        if self.objective == "quantile":
            params["alpha"] = self.alpha
            params["metric"] = "quantile"
            
        self.model = lgb.LGBMRegressor(**params)
        self.model.fit(X, y)
        return self

    def predict(self, test_features_df: pd.DataFrame) -> np.ndarray:
        if self.model is None or test_features_df.empty:
            return np.zeros(len(test_features_df))
        X = test_features_df[self.feature_cols].fillna(0)
        preds = self.model.predict(X)
        return np.maximum(0.0, preds)


# ---------------------------------------------------------------------------
# 5. NEURAL MULTI-HORIZON BASELINE (PyTorch MLP)
# ---------------------------------------------------------------------------
class PyTorchMultiHorizonMLP(nn.Module):
    """
    Direct multi-horizon neural forecasting block:
    Maps 28-day historical lookback window -> H-day future demand trajectory.
    """
    def __init__(self, input_dim: int = 28, hidden_dim: int = 64, horizon: int = 14):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, horizon)
        )

    def forward(self, x):
        return self.net(x)


class NeuralForecaster:
    """Wrapper for PyTorch multi-horizon forecasting."""
    def __init__(self, lookback: int = 28, horizon: int = 14, epochs: int = 40):
        self.lookback = lookback
        self.horizon = horizon
        self.epochs = epochs
        self.model = PyTorchMultiHorizonMLP(input_dim=lookback, hidden_dim=64, horizon=horizon)
        self.last_window = None

    def fit(self, y: np.ndarray):
        if len(y) < self.lookback + self.horizon:
            self.last_window = y[-self.lookback:] if len(y) >= self.lookback else np.pad(y, (self.lookback - len(y), 0))
            return self
            
        # Create sliding windows
        X_list, y_list = [], []
        for i in range(len(y) - self.lookback - self.horizon + 1):
            X_list.append(y[i:i + self.lookback])
            y_list.append(y[i + self.lookback:i + self.lookback + self.horizon])
            
        X_t = torch.tensor(np.array(X_list), dtype=torch.float32)
        y_t = torch.tensor(np.array(y_list), dtype=torch.float32)
        
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)
        criterion = nn.L1Loss()
        
        self.model.train()
        for epoch in range(self.epochs):
            optimizer.zero_grad()
            preds = self.model(X_t)
            loss = criterion(preds, y_t)
            loss.backward()
            optimizer.step()
            
        self.last_window = y[-self.lookback:]
        return self

    def predict(self, horizon: int = 14) -> np.ndarray:
        self.model.eval()
        with torch.no_grad():
            x_in = torch.tensor(self.last_window, dtype=torch.float32).unsqueeze(0)
            preds = self.model(x_in).squeeze(0).numpy()
            return np.maximum(0.0, preds[:horizon])

