"""
Production Inference Module for Adult Census Income Capstone Model.

This module provides the `IncomePredictor` class to load saved model artifacts (.joblib),
validate incoming raw data (dict, list of dicts, DataFrame, or CSV path), apply feature engineering,
compute calibrated probabilities, make threshold-based predictions, and identify the top-3
contributing features for each prediction.

Feature-contribution method
----------------------------
Contributions are computed via single-feature occlusion (leave-one-out perturbation):
for each raw input feature, we replace that feature's value with a reference baseline
(population median for numeric columns, population mode for categorical columns) and
re-score the pipeline. The drop in predicted probability tells us how much that feature
pushed the prediction up or down relative to a "typical" record. This is a lightweight,
model-agnostic proxy for Shapley-value explanations -- it is NOT a substitute for true
SHAP values, but unlike a hardcoded weight table it is actually derived from the trained
model's real behavior on the real input.
"""

import os
import joblib
import numpy as np
import pandas as pd

# Expected raw input columns for Adult Census Income dataset
REQUIRED_RAW_COLUMNS = [
    "age", "workclass", "education", "education-num", "marital-status",
    "occupation", "relationship", "race", "sex", "capital-gain",
    "capital-loss", "hours-per-week", "native-country"
]

NUMERIC_COLUMNS = ["age", "education-num", "capital-gain", "capital-loss", "hours-per-week"]
CATEGORICAL_COLUMNS = ["workclass", "education", "marital-status", "occupation",
                        "relationship", "race", "sex", "native-country"]

# Population-level reference baselines (medians/modes) used for occlusion-based
# feature contributions when the artifact does not ship its own reference stats.
# These were computed from the Adult Census Income training split (Week 4 Day 4/5).
# If you retrain on different data, pass `reference_stats` to IncomePredictor to override.
DEFAULT_REFERENCE_STATS = {
    "age": 37,
    "education-num": 10,
    "capital-gain": 0,
    "capital-loss": 0,
    "hours-per-week": 40,
    "workclass": "Private",
    "education": "HS-grad",
    "marital-status": "Married-civ-spouse",
    "occupation": "Prof-specialty",
    "relationship": "Husband",
    "race": "White",
    "sex": "Male",
    "native-country": "United-States",
}

AGE_BINS = [0, 25, 35, 45, 55, 65, 100]
AGE_LABELS = ["<=25", "26-35", "36-45", "46-55", "56-65", "65+"]
HOURS_BINS = [0, 20, 35, 40, 50, 100]
HOURS_LABELS = ["part_time_le20", "reduced_21_35", "standard_36_40", "over_41_50", "heavy_50plus"]


def engineer_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Apply feature engineering to raw input DataFrame."""
    new_df = frame.copy()
    new_df["age_bucket"] = pd.cut(new_df["age"], bins=AGE_BINS, labels=AGE_LABELS, right=True).astype(str)
    new_df["hours_bucket"] = pd.cut(new_df["hours-per-week"], bins=HOURS_BINS, labels=HOURS_LABELS, right=True).astype(str)
    new_df["has_capital_gain"] = (new_df["capital-gain"] > 0).astype(int)
    new_df["has_capital_loss"] = (new_df["capital-loss"] > 0).astype(int)
    new_df["higher_education"] = (new_df["education-num"] >= 13).astype(int)
    new_df["log_capital_gain"] = np.log1p(new_df["capital-gain"])
    new_df["edu_hours_interaction"] = new_df["education-num"] * new_df["hours-per-week"]
    new_df["net_capital"] = new_df["capital-gain"] - new_df["capital-loss"]
    return new_df


class InputValidationError(ValueError):
    """Raised when raw input fails schema validation."""


class IncomePredictor:
    """Production Inference Engine for Income Level Classification."""

    def __init__(self, artifact_path: str = "final_capstone_model.joblib", reference_stats: dict = None):
        """Load serialized model pipeline and metadata.

        Parameters
        ----------
        artifact_path : str
            Path to the joblib artifact produced by the training notebook.
        reference_stats : dict, optional
            Override for the population median/mode baselines used in occlusion-based
            feature contributions. Falls back to DEFAULT_REFERENCE_STATS.
        """
        if not os.path.exists(artifact_path):
            raise FileNotFoundError(f"Model artifact not found at '{artifact_path}'. Please run pipeline training first.")

        self.artifact = joblib.load(artifact_path)

        # Unpack artifact components
        if isinstance(self.artifact, dict) and "pipeline" in self.artifact:
            self.pipeline = self.artifact["pipeline"]
            self.optimal_threshold = self.artifact.get("optimal_threshold", 0.50)
            self.model_name = self.artifact.get("best_model_name", "Ensemble Pipeline")
            self.feature_cols = self.artifact.get("feature_cols", REQUIRED_RAW_COLUMNS)
        else:
            self.pipeline = self.artifact
            self.optimal_threshold = 0.50
            self.model_name = "Trained Model"
            self.feature_cols = REQUIRED_RAW_COLUMNS

        self.reference_stats = {**DEFAULT_REFERENCE_STATS, **(reference_stats or {})}

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def validate_input(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Validate input DataFrame for required raw columns and coerce dtypes.

        Raises
        ------
        InputValidationError
            If any required raw column is missing.
        """
        missing = [col for col in REQUIRED_RAW_COLUMNS if col not in raw_df.columns]
        if missing:
            raise InputValidationError(
                f"Missing required raw column(s): {missing}. Input must contain all of: {REQUIRED_RAW_COLUMNS}"
            )

        raw_df = raw_df.copy()

        # Ensure numerical types; invalid/missing values fall back to the reference median
        # rather than a magic constant, so a bad numeric field degrades gracefully instead
        # of silently biasing toward zero.
        for col in NUMERIC_COLUMNS:
            raw_df[col] = pd.to_numeric(raw_df[col], errors="coerce")
            raw_df[col] = raw_df[col].fillna(self.reference_stats[col])

        # Ensure string types for categorical columns. Unseen categories are NOT rewritten
        # here -- they're passed through as-is and handled downstream by the pipeline's
        # OneHotEncoder(handle_unknown='ignore'), which is the correct place to absorb them.
        for col in CATEGORICAL_COLUMNS:
            raw_df[col] = raw_df[col].astype(str)
            raw_df.loc[raw_df[col].isin(["nan", "None", ""]), col] = "Unknown"

        return raw_df

    # ------------------------------------------------------------------
    # Feature contributions (occlusion-based)
    # ------------------------------------------------------------------
    def _top_contributions(self, row_df: pd.DataFrame, base_prob: float, top_n: int = 3) -> str:
        """Compute top-N feature contributions for a single validated row via occlusion."""
        deltas = []
        for col in REQUIRED_RAW_COLUMNS:
            baseline_val = self.reference_stats.get(col)
            if baseline_val is None:
                continue
            perturbed = row_df.copy()
            perturbed.iloc[0, perturbed.columns.get_loc(col)] = baseline_val
            perturbed_prob = self.pipeline.predict_proba(perturbed)[:, 1][0]
            delta = float(base_prob - perturbed_prob)
            deltas.append((col, delta))

        deltas.sort(key=lambda x: abs(x[1]), reverse=True)
        top = deltas[:top_n]
        return "; ".join(f"{name} ({'+' if val >= 0 else ''}{val:.3f})" for name, val in top)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def predict(self, raw_input, threshold: float = None) -> pd.DataFrame:
        """
        Run end-to-end inference on raw input.

        Parameters
        ----------
        raw_input : dict, list of dicts, pd.DataFrame, or CSV filepath str
        threshold : float, optional (default uses optimal threshold from saved artifact)

        Returns
        -------
        pd.DataFrame containing:
            - probability: float [0, 1]
            - prediction: str ('>50K' or '<=50K')
            - pred_class: int (1 or 0)
            - threshold_used: float
            - top_3_contributions: str (feature: probability delta vs. baseline, descending |impact|)
        """
        if threshold is None:
            threshold = self.optimal_threshold

        df_raw = self._coerce_to_dataframe(raw_input)
        df_raw.columns = [str(c).lower().replace(" ", "-") for c in df_raw.columns]
        df_validated = self.validate_input(df_raw)

        probs = self.pipeline.predict_proba(df_validated)[:, 1]
        preds_binary = (probs >= threshold).astype(int)
        preds_label = np.where(preds_binary == 1, ">50K", "<=50K")

        results = []
        for idx in range(len(df_validated)):
            row_df = df_validated.iloc[[idx]].reset_index(drop=True)
            top_3_str = self._top_contributions(row_df, base_prob=probs[idx])
            results.append({
                "probability": float(np.round(probs[idx], 4)),
                "prediction": preds_label[idx],
                "pred_class": int(preds_binary[idx]),
                "threshold_used": float(np.round(threshold, 2)),
                "top_3_contributions": top_3_str,
            })

        return pd.DataFrame(results)

    @staticmethod
    def _coerce_to_dataframe(raw_input) -> pd.DataFrame:
        """Parse dict / list-of-dicts / DataFrame / CSV path into a DataFrame."""
        if isinstance(raw_input, str):
            if raw_input.endswith(".csv") and os.path.exists(raw_input):
                return pd.read_csv(raw_input)
            raise InputValidationError(f"Invalid file path or non-CSV file: {raw_input}")
        elif isinstance(raw_input, dict):
            return pd.DataFrame([raw_input])
        elif isinstance(raw_input, list):
            return pd.DataFrame(raw_input)
        elif isinstance(raw_input, pd.DataFrame):
            return raw_input.copy()
        else:
            raise TypeError(
                f"Unsupported input type: {type(raw_input)}. Expected dict, list of dicts, DataFrame, or CSV path."
            )


def predict_income(raw_input, artifact_path: str = "final_capstone_model.joblib", threshold: float = None) -> pd.DataFrame:
    """Convenience functional wrapper for inference."""
    predictor = IncomePredictor(artifact_path=artifact_path)
    return predictor.predict(raw_input, threshold=threshold)


if __name__ == "__main__":
    sample_input = {
        "age": 45,
        "workclass": "Private",
        "education": "Bachelors",
        "education-num": 13,
        "marital-status": "Married-civ-spouse",
        "occupation": "Exec-managerial",
        "relationship": "Husband",
        "race": "White",
        "sex": "Male",
        "capital-gain": 7298,
        "capital-loss": 0,
        "hours-per-week": 50,
        "native-country": "United-States"
    }
    print("Testing IncomePredictor locally...")
    if os.path.exists("final_capstone_model.joblib"):
        res = predict_income(sample_input)
        print(res.to_dict(orient="records"))
    else:
        print("Model file 'final_capstone_model.joblib' not found. Run training notebook first.")
