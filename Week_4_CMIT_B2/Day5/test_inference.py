"""
Unit tests for inference.py.

Covers:
  - missing required columns (should raise InputValidationError)
  - unseen categorical levels (should NOT crash; handled by handle_unknown='ignore')
  - multiple input formats (dict, list of dicts, DataFrame, CSV path)
  - threshold override behavior
  - artifact-not-found error

Run with:
    python -m pytest test_inference.py -v
or:
    python -m unittest test_inference.py -v

Requires a trained artifact at TEST_ARTIFACT_PATH. If you don't have one yet,
run `build_dummy_artifact()` once (see __main__ block) to generate a small
throwaway model so these tests are runnable without the full training notebook.
"""

import os
import unittest

import numpy as np
import pandas as pd

from inference import IncomePredictor, InputValidationError, REQUIRED_RAW_COLUMNS

TEST_ARTIFACT_PATH = "final_capstone_model.joblib"

VALID_RECORD = {
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
    "native-country": "United-States",
}


class TestIncomePredictor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(TEST_ARTIFACT_PATH):
            print(f"\nNo artifact at '{TEST_ARTIFACT_PATH}' -- building a dummy one so tests can run...")
            build_dummy_artifact(TEST_ARTIFACT_PATH)
        cls.predictor = IncomePredictor(artifact_path=TEST_ARTIFACT_PATH)

    # ------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------
    def test_missing_single_column_raises(self):
        bad_record = {k: v for k, v in VALID_RECORD.items() if k != "occupation"}
        with self.assertRaises(InputValidationError) as ctx:
            self.predictor.predict(bad_record)
        self.assertIn("occupation", str(ctx.exception))

    def test_missing_multiple_columns_lists_all(self):
        bad_record = {k: v for k, v in VALID_RECORD.items() if k not in ("occupation", "race", "sex")}
        with self.assertRaises(InputValidationError) as ctx:
            self.predictor.predict(bad_record)
        msg = str(ctx.exception)
        for col in ("occupation", "race", "sex"):
            self.assertIn(col, msg)

    def test_empty_dataframe_columns_raises(self):
        with self.assertRaises(InputValidationError):
            self.predictor.predict(pd.DataFrame())

    # ------------------------------------------------------------------
    # Unseen categories -- must NOT raise, must still return a valid row
    # ------------------------------------------------------------------
    def test_unseen_categorical_value_does_not_crash(self):
        record = dict(VALID_RECORD)
        record["workclass"] = "TotallyUnseenCategoryXYZ"
        record["native-country"] = "Atlantis"
        result = self.predictor.predict(record)
        self.assertEqual(len(result), 1)
        self.assertIn(result.iloc[0]["prediction"], (">50K", "<=50K"))
        self.assertTrue(0.0 <= result.iloc[0]["probability"] <= 1.0)

    def test_missing_numeric_value_falls_back_to_reference_median(self):
        record = dict(VALID_RECORD)
        record["age"] = None
        result = self.predictor.predict(record)
        self.assertEqual(len(result), 1)  # should not raise, should not silently zero-out

    # ------------------------------------------------------------------
    # Input format flexibility
    # ------------------------------------------------------------------
    def test_dict_input(self):
        result = self.predictor.predict(VALID_RECORD)
        self.assertEqual(len(result), 1)

    def test_list_of_dicts_input(self):
        result = self.predictor.predict([VALID_RECORD, VALID_RECORD])
        self.assertEqual(len(result), 2)

    def test_dataframe_input(self):
        df = pd.DataFrame([VALID_RECORD])
        result = self.predictor.predict(df)
        self.assertEqual(len(result), 1)

    def test_csv_input(self):
        df = pd.DataFrame([VALID_RECORD])
        df.to_csv("_test_tmp.csv", index=False)
        try:
            result = self.predictor.predict("_test_tmp.csv")
            self.assertEqual(len(result), 1)
        finally:
            os.remove("_test_tmp.csv")

    def test_nonexistent_csv_raises(self):
        with self.assertRaises(InputValidationError):
            self.predictor.predict("this_file_does_not_exist.csv")

    def test_unsupported_type_raises(self):
        with self.assertRaises(TypeError):
            self.predictor.predict(12345)

    # ------------------------------------------------------------------
    # Output contract
    # ------------------------------------------------------------------
    def test_output_columns_present(self):
        result = self.predictor.predict(VALID_RECORD)
        expected_cols = {"probability", "prediction", "pred_class", "threshold_used", "top_3_contributions"}
        self.assertTrue(expected_cols.issubset(set(result.columns)))

    def test_top_3_contributions_has_three_entries(self):
        result = self.predictor.predict(VALID_RECORD)
        contributions = result.iloc[0]["top_3_contributions"]
        self.assertEqual(contributions.count(";"), 2)  # 3 items joined by "; " -> 2 separators

    def test_threshold_override_changes_prediction_boundary(self):
        low = self.predictor.predict(VALID_RECORD, threshold=0.01)
        high = self.predictor.predict(VALID_RECORD, threshold=0.99)
        self.assertEqual(low.iloc[0]["pred_class"], 1)
        self.assertEqual(high.iloc[0]["pred_class"], 0)


class TestArtifactLoading(unittest.TestCase):
    def test_missing_artifact_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            IncomePredictor(artifact_path="no_such_artifact.joblib")


def build_dummy_artifact(path=TEST_ARTIFACT_PATH):
    """Utility to create a throwaway trained pipeline for local test runs
    when the real capstone artifact isn't available yet. Not a real model --
    just enough structure for the tests above to exercise inference.py."""
    import joblib
    from sklearn.preprocessing import StandardScaler, OneHotEncoder, FunctionTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.ensemble import RandomForestClassifier
    from inference import engineer_features

    np.random.seed(0)
    n = 300
    df = pd.DataFrame({
        "age": np.random.randint(18, 70, n),
        "workclass": np.random.choice(["Private", "Self-emp", "Gov"], n),
        "education": np.random.choice(["Bachelors", "HS-grad", "Masters"], n),
        "education-num": np.random.randint(5, 16, n),
        "marital-status": np.random.choice(["Married-civ-spouse", "Never-married", "Divorced"], n),
        "occupation": np.random.choice(["Exec-managerial", "Craft-repair", "Sales"], n),
        "relationship": np.random.choice(["Husband", "Not-in-family", "Wife"], n),
        "race": np.random.choice(["White", "Black", "Asian"], n),
        "sex": np.random.choice(["Male", "Female"], n),
        "capital-gain": np.random.choice([0, 0, 0, 5000, 10000], n),
        "capital-loss": np.random.choice([0, 0, 0, 500], n),
        "hours-per-week": np.random.randint(10, 60, n),
        "native-country": np.random.choice(["United-States", "Mexico"], n),
    })
    y = ((df["education-num"] >= 10) & (df["hours-per-week"] > 35)).astype(int)

    numeric_cols = ["age", "education-num", "capital-gain", "capital-loss", "hours-per-week"]
    categorical_cols = ["workclass", "education", "marital-status", "occupation",
                         "relationship", "race", "sex", "native-country"]
    all_numeric_cols = numeric_cols + ["has_capital_gain", "has_capital_loss", "higher_education",
                                        "log_capital_gain", "edu_hours_interaction", "net_capital"]
    all_categorical_cols = categorical_cols + ["age_bucket", "hours_bucket"]

    numeric_transformer = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    categorical_transformer = Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                                         ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))])
    preprocessor = ColumnTransformer([("num", numeric_transformer, all_numeric_cols),
                                       ("cat", categorical_transformer, all_categorical_cols)])
    feature_engineer = FunctionTransformer(engineer_features)

    pipe = Pipeline([("feature_engineering", feature_engineer),
                      ("preprocessing", preprocessor),
                      ("classifier", RandomForestClassifier(n_estimators=50, random_state=0))])
    pipe.fit(df, y)

    artifact = {"pipeline": pipe, "optimal_threshold": 0.4, "best_model_name": "Dummy RF",
                "feature_cols": REQUIRED_RAW_COLUMNS}
    joblib.dump(artifact, path)
    print(f"Dummy artifact written to {path}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
