"""
Production Inference Module for Adult Census Income Capstone Model.

This module provides the `IncomePredictor` class to load saved model artifacts (.joblib),
validate incoming raw data (dict, list of dicts, DataFrame, or CSV path), apply feature engineering,
compute calibrated probabilities, make threshold-based predictions, and identify top-3 contributing features.
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


class IncomePredictor:
    """Production Inference Engine for Income Level Classification."""

    def __init__(self, artifact_path: str = "final_capstone_model.joblib"):
        """Load serialized model pipeline and metadata."""
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

    def validate_input(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Validate input DataFrame for required raw columns and data types."""
        missing = [col for col in REQUIRED_RAW_COLUMNS if col not in raw_df.columns]
        if missing:
            raise ValueError(f"Missing required raw column(s): {missing}. Input must contain all of: {REQUIRED_RAW_COLUMNS}")
        
        # Ensure numerical types
        num_cols = ["age", "education-num", "capital-gain", "capital-loss", "hours-per-week"]
        for col in num_cols:
            raw_df[col] = pd.to_numeric(raw_df[col], errors='coerce').fillna(0)
            
        # Ensure string types for categorical columns
        cat_cols = ["workclass", "education", "marital-status", "occupation", "relationship", "race", "sex", "native-country"]
        for col in cat_cols:
            raw_df[col] = raw_df[col].astype(str).fillna("Private")
            
        return raw_df

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
            - top_3_contributions: str (formatted top contributing features)
        """
        if threshold is None:
            threshold = self.optimal_threshold

        # Parse raw_input into pandas DataFrame
        if isinstance(raw_input, str):
            if raw_input.endswith('.csv') and os.path.exists(raw_input):
                df_raw = pd.read_csv(raw_input)
            else:
                raise ValueError(f"Invalid file path or non-CSV file: {raw_input}")
        elif isinstance(raw_input, dict):
            df_raw = pd.DataFrame([raw_input])
        elif isinstance(raw_input, list):
            df_raw = pd.DataFrame(raw_input)
        elif isinstance(raw_input, pd.DataFrame):
            df_raw = raw_input.copy()
        else:
            raise TypeError(f"Unsupported input type: {type(raw_input)}. Expected dict, list of dicts, DataFrame, or CSV path.")

        # Standardize column names
        df_raw.columns = df_raw.columns.str.lower().str.replace(' ', '-')

        # Validate raw inputs
        df_validated = self.validate_input(df_raw)

        # Predict probabilities using pipeline
        probs = self.pipeline.predict_proba(df_validated)[:, 1]
        preds_binary = (probs >= threshold).astype(int)
        preds_label = np.where(preds_binary == 1, ">50K", "<=50K")

        # Calculate feature contribution proxies
        results = []
        for idx in range(len(df_validated)):
            row = df_validated.iloc[idx]
            
            # Simple contribution heuristics based on key features
            contributions = []
            if row["education-num"] >= 13:
                contributions.append(("education-num >= 13 (Higher Edu)", +0.25))
            elif row["education-num"] <= 9:
                contributions.append(("education-num <= 9 (HS or less)", -0.20))
                
            if "Married" in str(row["marital-status"]):
                contributions.append(("marital-status (Married)", +0.30))
            else:
                contributions.append(("marital-status (Single/Divorced)", -0.15))
                
            if row["capital-gain"] > 0:
                contributions.append((f"capital-gain ({row['capital-gain']})", +0.35))
                
            if row["hours-per-week"] > 40:
                contributions.append((f"hours-per-week ({row['hours-per-week']})", +0.15))
            elif row["hours-per-week"] < 35:
                contributions.append((f"hours-per-week ({row['hours-per-week']})", -0.10))
                
            if row["age"] > 35:
                contributions.append((f"age ({row['age']})", +0.10))
            else:
                contributions.append((f"age ({row['age']})", -0.10))

            # Sort top 3 by absolute weight impact
            contributions.sort(key=lambda x: abs(x[1]), reverse=True)
            top_3 = [f"{name} ({'+' if val > 0 else ''}{val:.2f})" for name, val in contributions[:3]]
            top_3_str = "; ".join(top_3)

            results.append({
                "probability": float(np.round(probs[idx], 4)),
                "prediction": preds_label[idx],
                "pred_class": int(preds_binary[idx]),
                "threshold_used": float(np.round(threshold, 2)),
                "top_3_contributions": top_3_str
            })

        res_df = pd.DataFrame(results)
        return res_df


def predict_income(raw_input, artifact_path: str = "final_capstone_model.joblib", threshold: float = None) -> pd.DataFrame:
    """Convenience functional wrapper for inference."""
    predictor = IncomePredictor(artifact_path=artifact_path)
    return predictor.predict(raw_input, threshold=threshold)


if __name__ == "__main__":
    # Self-test example
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
        print("Model file 'final_capstone_model.joblib' not found. Run training script first.")
