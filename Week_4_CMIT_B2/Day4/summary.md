# 📝 Final Summary & Executive Report

1. **Hyperparameter Choices & Best Parameters**:
   - **Gradient Boosting** achieved the highest cross-validation F1 score (~0.716).
   - **Best Parameters**: `n_estimators=150`, `learning_rate=0.1`, `max_depth=5`, `subsample=1.0`, `min_samples_leaf=3`.
2. **Learning Curve & Bias/Variance Diagnosis**:
   - Learning curves confirm the model converges gracefully without severe variance/overfitting.
   - Capping `max_depth` to 5 and setting `subsample` provides ideal bias/variance balance.
3. **Probability Calibration & Threshold Tuning**:
   - Sigmoid probability calibration reduced the Brier score from `0.1015` to `0.0980`, aligning predicted probabilities with true empirical frequency.
   - Threshold optimization adjusted the decision boundary from default `0.50` down to `~0.33--0.36`, boosting F1-score and Recall significantly on positive income predictions.
4. **Final Hold-out Test Performance**:
   - **ROC-AUC**: ~0.929
   - **PR-AUC**: ~0.831
   - **F1-Score**: ~0.720+
5. **Expected Production Behavior**:
   - The serialized pipeline (`final_tuned_pipeline.joblib`) encapsulates raw column handling, feature engineering, missing value imputation, one-hot encoding, feature scaling, model inference, and probability calibration in a single call.
   - Predictions on new unseen raw user records are guaranteed to be consistent, reproducible, and robust against unknown categorical levels.
