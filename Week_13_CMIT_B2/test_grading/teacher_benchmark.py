"""
Teacher vs Autograder Benchmark Evaluation
Evaluates all 50 submissions, benchmarks autograder scores against Human Teacher 1 and Teacher 2,
calculates statistical agreement metrics (Pearson r, MAE, RMSE), and generates comparison plots.
"""

import json
import math
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from test_grading.test_runner import CodeTestRunner
from test_grading.submissions_dataset import SUBMISSIONS_DATASET

def run_benchmark():
    runner = CodeTestRunner()
    results = []

    print("=" * 75)
    print("RUNNING DAY 4 TEST-BASED GRADING & TEACHER BENCHMARK (50 SUBMISSIONS)")
    print("=" * 75)

    auto_scores = []
    t1_scores = []
    t2_scores = []
    avg_teacher_scores = []

    for sub in SUBMISSIONS_DATASET:
        sub_id = sub["id"]
        cat = sub["category"]
        t1 = float(sub["teacher_1_score"])
        t2 = float(sub["teacher_2_score"])
        t_avg = (t1 + t2) / 2.0

        res = runner.grade_submission(sub["code"])
        auto_score = res["autograder_score"]

        auto_scores.append(auto_score)
        t1_scores.append(t1)
        t2_scores.append(t2)
        avg_teacher_scores.append(t_avg)

        results.append({
            "id": sub_id,
            "student_id": sub["student_id"],
            "category": cat,
            "autograder_score": auto_score,
            "teacher_1_score": t1,
            "teacher_2_score": t2,
            "average_teacher_score": round(t_avg, 2),
            "score_diff": round(auto_score - t_avg, 2),
            "verdict": res["verdict"],
            "efficiency_time_sec": res.get("efficiency_time_sec", 0.0),
            "failed_test": res.get("failed_test"),
            "failed_reason": res.get("failed_reason")
        })

    # Statistical Metrics Computation
    auto_np = np.array(auto_scores)
    t_avg_np = np.array(avg_teacher_scores)
    t1_np = np.array(t1_scores)
    t2_np = np.array(t2_scores)

    # Pearson correlation
    corr_matrix = np.corrcoef(auto_np, t_avg_np)
    r_val = float(corr_matrix[0, 1])

    # Human-to-human correlation
    human_corr = float(np.corrcoef(t1_np, t2_np)[0, 1])

    # MAE and RMSE
    mae = float(np.mean(np.abs(auto_np - t_avg_np)))
    rmse = float(np.sqrt(np.mean((auto_np - t_avg_np) ** 2)))

    # Exact agreement and close agreement
    diffs = np.abs(auto_np - t_avg_np)
    agree_exact = float(np.mean(diffs == 0.0) * 100)
    agree_within_5 = float(np.mean(diffs <= 5.0) * 100)
    agree_within_10 = float(np.mean(diffs <= 10.0) * 100)

    # Category summaries
    cat_summary = {}
    for r in results:
        c = r["category"]
        if c not in cat_summary:
            cat_summary[c] = {"auto": [], "teacher": []}
        cat_summary[c]["auto"].append(r["autograder_score"])
        cat_summary[c]["teacher"].append(r["average_teacher_score"])

    category_stats = {}
    for c, data in cat_summary.items():
        category_stats[c] = {
            "count": len(data["auto"]),
            "avg_autograder": round(float(np.mean(data["auto"])), 2),
            "avg_teacher": round(float(np.mean(data["teacher"])), 2),
            "mae": round(float(np.mean(np.abs(np.array(data["auto"]) - np.array(data["teacher"])))), 2)
        }

    print(f"Total Submissions Evaluated: {len(results)}")
    print(f"Autograder vs Teacher Pearson r : {r_val:.4f} (Teacher1 vs Teacher2: {human_corr:.4f})")
    print(f"Mean Absolute Error (MAE)       : {mae:.2f} points")
    print(f"Root Mean Squared Error (RMSE)  : {rmse:.2f} points")
    print(f"Agreement within +/- 5 points   : {agree_within_5:.1f}%")
    print(f"Agreement within +/- 10 points  : {agree_within_10:.1f}%")
    print("=" * 75)

    summary = {
        "total_submissions": len(results),
        "pearson_correlation_with_teachers": round(r_val, 4),
        "human_grader_inter_rater_r": round(human_corr, 4),
        "mean_absolute_error_points": round(mae, 2),
        "root_mean_squared_error_points": round(rmse, 2),
        "agreement_within_5_pts_pct": round(agree_within_5, 1),
        "agreement_within_10_pts_pct": round(agree_within_10, 1),
        "category_performance": category_stats,
        "submissions_results": results
    }

    # Save JSON report
    os.makedirs("day4_reports", exist_ok=True)
    json_path = os.path.join("day4_reports", "test_grading_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Grading report exported to: {json_path}")

    # Generate Chart
    generate_grading_figure(auto_np, t_avg_np, r_val, mae, category_stats)

    return summary


def generate_grading_figure(auto_scores, teacher_scores, r_val, mae, category_stats):
    os.makedirs("figures", exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Plot 1: Scatter plot with identity line
    ax1.scatter(teacher_scores, auto_scores, color="#2980b9", alpha=0.75, s=65, edgecolors="#1f3a93", zorder=3)
    ax1.plot([0, 105], [0, 105], color="#e74c3c", linestyle="--", linewidth=1.8, label="Ideal Agreement (y = x)")

    # Linear trendline
    m, b = np.polyfit(teacher_scores, auto_scores, 1)
    ax1.plot(teacher_scores, m * teacher_scores + b, color="#27ae60", linewidth=1.5, label=f"Fit Line: y = {m:.2f}x + {b:.2f}")

    ax1.set_xlabel("Average Teacher Score (Human Benchmarks)", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Autograder Score (0 - 100)", fontsize=11, fontweight="bold")
    ax1.set_title(f"Autograder vs Human Teacher Agreement\n(Pearson r = {r_val:.4f}, MAE = {mae:.2f} pts)", fontsize=12, fontweight="bold", pad=12)
    ax1.set_xlim(-5, 105)
    ax1.set_ylim(-5, 105)
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper left")

    # Plot 2: Average Score comparison across categories
    cats = list(category_stats.keys())
    auto_means = [category_stats[c]["avg_autograder"] for c in cats]
    teacher_means = [category_stats[c]["avg_teacher"] for c in cats]

    y_pos = np.arange(len(cats))
    height = 0.35

    ax2.barh(y_pos - height/2, auto_means, height, label="Autograder", color="#3498db", edgecolor="#2980b9")
    ax2.barh(y_pos + height/2, teacher_means, height, label="Human Teachers", color="#e67e22", edgecolor="#d35400")

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(cats, fontsize=9, fontweight="bold")
    ax2.invert_yaxis()  # Labels read top-to-bottom
    ax2.set_xlabel("Mean Score (Points)", fontsize=11, fontweight="bold")
    ax2.set_title("Scoring Alignment across Defect & Quality Categories", fontsize=12, fontweight="bold", pad=12)
    ax2.set_xlim(0, 110)
    ax2.grid(True, linestyle=":", alpha=0.5, axis="x")
    ax2.legend(loc="lower right")

    plt.suptitle("Ilm Academy Code Autograding Calibration & Verification", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()

    out_path = os.path.join("figures", "grader_teacher_comparison.png")
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Chart generated at: {out_path}")


if __name__ == "__main__":
    run_benchmark()
