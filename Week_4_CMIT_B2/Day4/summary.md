# 📝 Final Summary & Executive Report

1. **Hyperparameter Choices & Best Parameters**:
   - **Gradient Boosting** achieved the highest cross-validation F1 score (0.7074).
   - **Best Parameters**: `n_estimators=100`, `learning_rate=0.1`, `max_depth=5`, `subsample=0.8`, `min_samples_leaf=3`.
2. **Learning Curve & Bias/Variance Diagnosis**:
   - Learning curves confirm the model converges gracefully without severe variance/overfitting.
   - Capping `max_depth` to 5 and setting `subsample=0.8` provides the ideal bias/variance balance.
3. **Probability Calibration & Threshold Tuning**:
   - Sigmoid probability calibration reduced the Brier score from `0.08712` to `0.06062`, aligning predicted probabilities with true empirical frequency.
   - Threshold optimization adjusted the decision boundary from default `0.50` down to `0.38`, boosting F1-score and Recall on positive income predictions.
4. **Final Hold-out Test Performance**:
   - **ROC-AUC**: 0.9161
   - **PR-AUC**: 0.809
   - **F1-Score**: 0.7082
5. **Expected Production Behavior**:
   - The serialized pipeline (`final_tuned_pipeline.joblib`) encapsulates raw column handling, feature engineering, missing value imputation, one-hot encoding, feature scaling, model inference, and probability calibration in a single call.
   - Predictions on new unseen raw user records are guaranteed to be consistent, reproducible, and robust against unknown categorical levels.
   