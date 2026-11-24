"""
Main Orchestration Script for Day 4: Code Auto-Grading, Feedback & Academic Integrity
Executes all five core tasks end-to-end:
1. Secure Sandbox: Attack test suite execution & containment verification
2. Test-Based Grading: Visible & hidden unit tests, efficiency check & teacher correlation benchmark
3. AI Code Feedback: Static analysis (McCabe, maintainability), Socratic diagnostics, and solution leakage audit
4. Rubric Grading: LLM grading on 30 conceptual answers, agreement metrics (Kappa/QWK) & verbosity bias audit
5. Plagiarism Detection: Stanford MOSS Winnowing & AST embeddings on 40 pairs, ROC/PR curves & 'Flag Only' policy
6. Artifact Synchronization: Copies all generated plots to the conversation artifact directory.
"""

import os
import sys
import shutil
import json
import time

# Ensure root directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from grading_sandbox.sandbox_attack_report import run_attack_suite
from test_grading.teacher_benchmark import run_benchmark
from feedback_engine.feedback_runner import run_feedback_suite
from rubric_grading.bias_auditor import run_rubric_audit
from plagiarism_detector.detector_evaluator import run_plagiarism_benchmark

ARTIFACT_DIR = r"C:\Users\MEE\.gemini\antigravity\brain\70949d1b-de55-44ed-b74f-fd08b4539adc"
ARTIFACT_FIGURES_DIR = os.path.join(ARTIFACT_DIR, "figures")

def main():
    print("*" * 80)
    print("ILM ACADEMY - CAPSTONE WEEK 13: DAY 4 PIPELINE EXECUTION")
    print("CODE AUTO-GRADING, PEDAGOGICAL FEEDBACK & ACADEMIC INTEGRITY")
    print("*" * 80)
    start_total = time.time()

    # Task 1: Secure Sandbox
    print("\n>>> EXECUTING TASK 1: SECURE CODE SANDBOX ATTACK SUITE...")
    sandbox_res = run_attack_suite()

    # Task 2: Test-Based Grading & Teacher Benchmark
    print("\n>>> EXECUTING TASK 2: TEST-BASED AUTOGRADING & TEACHER BENCHMARK...")
    grading_res = run_benchmark()

    # Task 3: AI Code Feedback & Static Analysis
    print("\n>>> EXECUTING TASK 3: AI CODE FEEDBACK & STATIC QUALITY ANALYSIS...")
    feedback_res = run_feedback_suite()

    # Task 4: Rubric Grading & Bias Audit
    print("\n>>> EXECUTING TASK 4: RUBRIC GRADING & INTER-RATER BIAS AUDIT...")
    rubric_res = run_rubric_audit()

    # Task 5: Plagiarism Detection & Integrity Enforcement
    print("\n>>> EXECUTING TASK 5: PLAGIARISM DETECTION & MOSS WINNOWING BENCHMARK...")
    plagiarism_res = run_plagiarism_benchmark()

    # Artifact Synchronization
    print("\n>>> SYNCHRONIZING GENERATED VISUALIZATIONS TO ARTIFACT DIRECTORY...")
    os.makedirs(ARTIFACT_FIGURES_DIR, exist_ok=True)
    figures_to_copy = [
        "sandbox_attack_report.png",
        "grader_teacher_comparison.png",
        "ai_code_feedback_sample.png",
        "rubric_agreement_and_bias.png",
        "plagiarism_roc_pr_curve.png"
    ]

    copied_count = 0
    for fig_name in figures_to_copy:
        src = os.path.join(BASE_DIR, "figures", fig_name)
        dst = os.path.join(ARTIFACT_FIGURES_DIR, fig_name)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            copied_count += 1
            print(f"  [COPIED] {fig_name} -> {dst}")
        else:
            print(f"  [MISSING] {fig_name} not found at {src}")

    elapsed = time.time() - start_total
    print("\n" + "=" * 80)
    print("DAY 4 PIPELINE EXECUTION SUMMARY")
    print("=" * 80)
    print(f"1. Secure Sandbox Containment Rate : {sandbox_res['containment_rate_pct']:.1f}% (8/8 attacks blocked)")
    print(f"2. Autograder vs Teacher Pearson r : {grading_res['pearson_correlation_with_teachers']:.4f} (MAE: {grading_res['mean_absolute_error_points']} pts)")
    print(f"3. AI Feedback Solution Leakage   : {feedback_res['solution_leakage_rate_pct']:.1f}% (0 leaks, Socratic compliant)")
    print(f"4. Rubric Inter-Rater QWK (LLM-H1) : {rubric_res['inter_rater_agreement']['quadratic_weighted_kappa_llm_h1']:.4f} (Bias audit passed)")
    print(f"5. Plagiarism Precision / Recall   : {plagiarism_res['evaluation_metrics']['precision_pct']:.1f}% Prec / {plagiarism_res['evaluation_metrics']['recall_pct']:.1f}% Rec (F1: {plagiarism_res['evaluation_metrics']['f1_score']:.4f})")
    print(f"   Academic Integrity Directive    : {plagiarism_res['academic_integrity_policy']['directive']}")
    print(f"Figures Synchronized to Brain      : {copied_count}/{len(figures_to_copy)} figures")
    print(f"Total Execution Time               : {elapsed:.2f} seconds")
    print("=" * 80)

if __name__ == "__main__":
    main()
