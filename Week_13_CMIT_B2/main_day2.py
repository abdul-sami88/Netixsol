"""
Master Orchestration Script - Week 13 Capstone: AI Tutor & Adaptive Learning Platform
Day 2: Knowledge Tracing & Adaptive Learning Engine

Orchestrates and verifies:
1. Knowledge Tracing: Baseline vs BKT vs PFA vs DKT/SAKT (Student-level split on AUC, Acc, RMSE)
2. Mastery & IRT: Mastery matrix, 1PL/2PL item parameters, Bad Questions audit & ICC curves
3. Adaptive Recommendation: DAG Prereqs, ZPD (60-80%), Thompson Sampling, Spaced Repetition, Cohort Sim
4. Personalized Paths: Custom roadmaps for Ali (loop-strong/function-weak) and Sara (fast/careless) with UrduLish coaching
5. Dropout Early-Warning: LightGBM model, PR-AUC, SHAP explanations, risk-tiered intervention policies
"""

import sys
import os
import json
import time
import pandas as pd

def print_header(title: str):
    print("\n" + "=" * 75)
    print(f" {title.upper()} ")
    print("=" * 75)

def main():
    start_time = time.time()
    print_header("Week 13 Capstone: AI Tutor - Day 2 Execution Pipeline")

    # -------------------------------------------------------------
    # TASK 1: Knowledge Tracing Benchmark
    # -------------------------------------------------------------
    print_header("Task 1: Knowledge Tracing Model Benchmark (Student-Level Split)")
    from knowledge_tracing.model_comparator import KTModelComparator
    comparator = KTModelComparator()
    kt_results = comparator.run_benchmark()
    p_kt = comparator.plot_comparison("figures/knowledge_tracing_model_comparison.png")

    print("\nModel Benchmark Comparison Table:")
    print(kt_results.to_string(index=False))
    print(f"\nGenerated Comparison Visualization: {p_kt}")

    # -------------------------------------------------------------
    # TASK 2: Mastery Estimation & IRT Psychometrics
    # -------------------------------------------------------------
    print_header("Task 2: Mastery Estimation & 1PL / 2PL IRT (Bad Questions Audit)")
    from mastery_irt.irt_engine import IRTEngine
    from mastery_irt.mastery_tracker import MasteryTracker
    from mastery_irt.bad_question_detector import BadQuestionDetector
    from question_bank.question_generator import QuestionBankGenerator

    df_int = pd.read_csv("learner_data/data/student_interactions.csv")

    # Fit IRT
    print("Fitting 1PL (Rasch) and 2PL IRT Models over 32,382 interactions...")
    irt_engine = IRTEngine().fit(df_int)
    irt_params_df = irt_engine.get_item_parameters_df()

    # Load questions
    q_bank = QuestionBankGenerator().generate_all_questions()

    # Audit Bad Questions
    print("\nAuditing Question Bank for Psychometric Flaws (Discrimination, Floor/Ceiling, Misfits)...")
    detector = BadQuestionDetector(irt_params_df, q_bank)
    flagged_df = detector.audit_questions()

    print(f"Total Questions Audited: {len(irt_params_df)}")
    print(f"Questions Flagged for Quality Review: {len(flagged_df)}")
    if not flagged_df.empty:
        print("\nSample Flagged 'Bad Questions':")
        cols_show = ["question_id", "concept_id", "severity", "discrimination_a", "difficulty_b", "point_biserial", "primary_defect"]
        print(flagged_df[cols_show].head(5).to_string(index=False))

    # Plot ICC
    good_item = irt_params_df.sort_values(by="a_2pl", ascending=False)["question_id"].iloc[0]
    bad_item = flagged_df["question_id"].iloc[0] if not flagged_df.empty else "Q001"
    icc_fig = detector.plot_icc_comparison(good_item, bad_item, "figures/item_characteristic_curves.png")
    print(f"Generated Item Characteristic Curves (ICC): {icc_fig}")

    # Mastery Profiles
    tracker = MasteryTracker(df_int)
    ali = tracker.construct_ali_profile()
    sara = tracker.construct_sara_profile()

    print("\nDiagnostic Personas Profiled:")
    print(f"  - Ali: {ali['description']} (Loop Mastery: 85-92% vs Function Mastery: 26-42%)")
    print(f"  - Sara: {sara['description']} (Speed: 0.65x, Slip Rate: 22%)")

    # -------------------------------------------------------------
    # TASK 3: Adaptive Recommendation Engine & Curriculum Simulation
    # -------------------------------------------------------------
    print_header("Task 3: Adaptive Recommendation Engine (ZPD, Thompson Sampling, Spaced Repetition)")
    from adaptive_engine.prerequisite_checker import PrerequisiteChecker
    from adaptive_engine.zpd_selector import ZPDSelector
    from adaptive_engine.thompson_sampler import ThompsonSamplingBandit
    from adaptive_engine.spaced_repetition import SpacedRepetitionScheduler
    from adaptive_engine.curriculum_simulator import CurriculumSimulator

    # 1. Prerequisite check for Ali
    checker = PrerequisiteChecker()
    can_ali_do_nested, missing_nested = checker.is_concept_eligible("nested_loops", ali["mastery_scores"])
    can_ali_do_scope, missing_scope = checker.is_concept_eligible("variable_scope", ali["mastery_scores"])
    print(f"Prerequisite Check - Ali on 'nested_loops': Unlocked? {can_ali_do_nested} (Missing: {missing_nested})")
    print(f"Prerequisite Check - Ali on 'variable_scope': Unlocked? {can_ali_do_scope} (Missing: {missing_scope})")

    # 2. ZPD Item Selection
    zpd = ZPDSelector()
    sample_candidate_questions = [q for q in q_bank if q["concept_id"] in ["functions_def", "for_loops", "recursion"]][:5]
    irt_lookup = {row["question_id"]: row for row in irt_params_df.to_dict(orient="records")}
    zpd_ranked = zpd.filter_and_rank_items(sample_candidate_questions, student_theta=0.1, irt_lookup=irt_lookup)
    print("\nZPD Candidate Ranking (Targeting 60-80% predicted success):")
    for r in zpd_ranked[:3]:
        print(f"  - Item {r['question_id']} ({r['concept_id']}): Pred P={r['predicted_p']}, ZPD Score={r['zpd_score']}, In ZPD={r['in_zpd']}")

    # 3. Thompson Sampling Decision
    bandit = ThompsonSamplingBandit()
    eligible = ["functions_def", "return_statement", "arguments_parameters"]
    zpd_scores = {c: 0.85 for c in eligible}
    decision = bandit.sample_concept("STU_ALI", eligible, ali["mastery_scores"], zpd_scores)
    print(f"\nThompson Sampling Selected Next Concept for Ali: '{decision['selected_concept']}' (Priority: {decision['priority']})")

    # 4. Spaced Repetition
    rep_scheduler = SpacedRepetitionScheduler()
    rep_scheduler.record_practice("STU_ALI", "while_loops", is_correct=True, current_session=1)
    ret_now = rep_scheduler.get_retention("STU_ALI", "while_loops", current_session=6)
    print(f"Spaced Repetition: Ali retention on 'while_loops' after 5 sessions: {ret_now*100:.1f}%")

    # 5. Cohort Simulation: Fixed vs Adaptive
    print("\nRunning Cohort Simulation: Fixed Linear Curriculum vs. Adaptive Engine (N=500 each)...")
    sim = CurriculumSimulator(num_students_per_cohort=500, seed=42)
    sim_stats = sim.run_comparison()
    sim_fig = sim.plot_comparison("figures/curriculum_comparison.png")

    f_res = sim_stats["fixed_curriculum"]
    a_res = sim_stats["adaptive_engine"]
    gains = sim_stats["relative_gains"]

    print(f"  Fixed Curriculum:   Pre-W4 Dropout = {f_res['pre_w4_dropout_rate_pct']}%, Avg Mastery = {f_res['mean_concepts_mastered']}/44 concepts")
    print(f"  Adaptive Engine:    Pre-W4 Dropout = {a_res['pre_w4_dropout_rate_pct']}%, Avg Mastery = {a_res['mean_concepts_mastered']}/44 concepts")
    print(f"  Impact: Dropout reduced by {gains['dropout_reduction_pct']}%, Mastery increased by +{gains['mastery_increase_pct']}%!")
    print(f"Saved Curriculum Comparison Chart: {sim_fig}")

    # -------------------------------------------------------------
    # TASK 4: Personalized Learning Paths & UrduLish Coaching
    # -------------------------------------------------------------
    print_header("Task 4: Personalized Learning Paths & UrduLish Coaching")
    from adaptive_engine.learning_path_generator import LearningPathGenerator
    path_gen = LearningPathGenerator()

    ali_path = path_gen.generate_personalized_path(ali, max_steps=4)
    sara_path = path_gen.generate_personalized_path(sara, max_steps=4)

    print(f"\n--- Personalized Path: ALI (Est. Time: {ali_path['total_estimated_time_mins']} mins / {ali_path['total_estimated_time_hours']} hrs) ---")
    for s in ali_path["learning_path_steps"]:
        print(f"  Step {s['step']} [{s['type']}]: {s['concept_name']} ({s['estimated_minutes']}m) -> {s['rationale']}")
    print(f"\nUrduLish Motivational Coach for Ali:\n\"{ali_path['urdulish_motivational_message']}\"")

    print(f"\n--- Personalized Path: SARA (Est. Time: {sara_path['total_estimated_time_mins']} mins / {sara_path['total_estimated_time_hours']} hrs) ---")
    for s in sara_path["learning_path_steps"]:
        print(f"  Step {s['step']} [{s['type']}]: {s['concept_name']} ({s['estimated_minutes']}m) -> {s['rationale']}")
    print(f"\nUrduLish Motivational Coach for Sara:\n\"{sara_path['urdulish_motivational_message']}\"")

    # -------------------------------------------------------------
    # TASK 5: Dropout Early-Warning Model (LightGBM, PR-AUC, SHAP)
    # -------------------------------------------------------------
    print_header("Task 5: Dropout Early-Warning Model (LightGBM, PR-AUC, SHAP)")
    from dropout_early_warning.dropout_model import DropoutPredictor
    from dropout_early_warning.shap_explainer import DropoutSHAPExplainer
    from dropout_early_warning.intervention_policy import InterventionPolicy

    predictor = DropoutPredictor(test_size=0.20, random_state=42)
    dp_metrics = predictor.train_and_evaluate()
    pr_fig = predictor.plot_pr_and_roc_curves("figures/dropout_pr_curve.png")

    print("Dropout Early-Warning Model Performance (Evaluated on Weeks 1 & 2):")
    print(f"  - PR-AUC:               {dp_metrics['PR_AUC']:.4f} (Baseline positive rate: {dp_metrics['Baseline_Positive_Rate']:.4f})")
    print(f"  - ROC-AUC:              {dp_metrics['ROC_AUC']:.4f}")
    print(f"  - Precision (At-Risk):  {dp_metrics['Precision_At_Risk']:.4f}")
    print(f"  - Recall (At-Risk):     {dp_metrics['Recall_At_Risk']:.4f}")
    print(f"  - F1-Score:             {dp_metrics['F1_Score']:.4f}")
    print(f"Saved PR & Risk Distribution Curves to: {pr_fig}")

    # SHAP Explanations
    print("\nComputing Global SHAP Feature Importances...")
    shap_engine = DropoutSHAPExplainer(predictor)
    shap_df = shap_engine.compute_global_importance()
    shap_fig = shap_engine.plot_shap_summary("figures/dropout_shap_importance.png")

    print("Top 5 Drivers of Early Course Dropout:")
    for _, row in shap_df.tail(5).iloc[::-1].iterrows():
        print(f"  {row['display_name']:<42}: Mean |SHAP| = {row['shap_importance']:.4f}")
    print(f"Saved SHAP Summary Chart to: {shap_fig}")

    # Individual Student Local Explanation
    at_risk_sample = predictor.X_test[predictor.y_test == 1].iloc[0]
    local_exp = shap_engine.explain_individual_student(at_risk_sample)
    print(f"\nLocal Explanation for At-Risk Student (Risk: {local_exp['predicted_risk_probability']*100:.1f}%):")
    for d in local_exp["top_risk_drivers"]:
        print(f"  - {d['display_name']} = {d['value']} (SHAP Impact: +{d['shap_contribution']:.3f})")

    # Risk-tiered Action Policies
    print("\nPrescriptive Actions by Risk Level:")
    policy_report = InterventionPolicy.generate_policy_report()
    for pol in policy_report:
        print(f"\n[{pol['risk_tier']} RISK - {pol['probability_range']}]: {pol['status_label']}")
        for act in pol["prescribed_actions"]:
            print(f"   * {act}")

    elapsed = round(time.time() - start_time, 2)
    print_header(f"Day 2 Pipeline Execution Complete in {elapsed}s")

if __name__ == "__main__":
    main()
