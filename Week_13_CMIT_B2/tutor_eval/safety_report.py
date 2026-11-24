"""
Tutor Safety Evaluation Report & Visualization
Generates the publication-grade radar / multi-metric safety evaluation chart and JSON report.
"""

from typing import Dict, Any
import os
import json
import matplotlib.pyplot as plt
from tutor_eval.evaluator import TutorEvaluator

class SafetyReportGenerator:
    """
    Renders safety report artifacts and figures for the Socratic AI Tutor evaluation.
    """

    @staticmethod
    def generate_report(output_json: str = "day3_reports/tutor_safety_evaluation.json", output_fig: str = "figures/tutor_safety_evaluation.png") -> Dict[str, Any]:
        os.makedirs(os.path.dirname(os.path.abspath(output_json)), exist_ok=True)
        os.makedirs(os.path.dirname(os.path.abspath(output_fig)), exist_ok=True)

        evaluator = TutorEvaluator()
        metrics = evaluator.run_full_suite()

        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

        # Plot 4-panel evaluation metrics
        fig, axes = plt.subplots(1, 4, figsize=(16, 4.5), dpi=150)

        # 1. Answer Leakage (Target 0%)
        axes[0].bar(["Answer Leakage"], [metrics["answer_leakage_rate_pct"]], color="#10b981", width=0.4)
        axes[0].set_ylim(0, 10)
        axes[0].set_ylabel("Leakage Rate %", fontsize=10)
        axes[0].set_title("Answer Leakage (Target: 0%)", fontsize=11, weight="bold")
        axes[0].grid(axis="y", linestyle="--", alpha=0.5)
        axes[0].text(0, metrics["answer_leakage_rate_pct"] + 0.3, f"{metrics['answer_leakage_rate_pct']:.1f}%", ha="center", weight="bold")

        # 2. Jailbreak Defense (Target 100%)
        axes[1].bar(["Jailbreak Defense"], [metrics["jailbreak_defense_rate_pct"]], color="#0284c7", width=0.4)
        axes[1].set_ylim(0, 115)
        axes[1].set_ylabel("Defense Rate %", fontsize=10)
        axes[1].set_title("Jailbreak Defense (10 Attacks)", fontsize=11, weight="bold")
        axes[1].grid(axis="y", linestyle="--", alpha=0.5)
        axes[1].text(0, metrics["jailbreak_defense_rate_pct"] + 2, f"{metrics['jailbreak_defense_rate_pct']:.1f}%", ha="center", weight="bold")

        # 3. Pedagogy Score (out of 5.0)
        axes[2].bar(["Pedagogy Score"], [metrics["mean_pedagogy_score"]], color="#8b5cf6", width=0.4)
        axes[2].set_ylim(0, 5.5)
        axes[2].set_ylabel("Score (1-5)", fontsize=10)
        axes[2].set_title("Socratic Pedagogy", fontsize=11, weight="bold")
        axes[2].grid(axis="y", linestyle="--", alpha=0.5)
        axes[2].text(0, metrics["mean_pedagogy_score"] + 0.1, f"{metrics['mean_pedagogy_score']:.2f} / 5.0", ha="center", weight="bold")

        # 4. Tone Score (out of 5.0)
        axes[3].bar(["Late-Night Tone"], [metrics["mean_tone_score"]], color="#f59e0b", width=0.4)
        axes[3].set_ylim(0, 5.5)
        axes[3].set_ylabel("Score (1-5)", fontsize=10)
        axes[3].set_title("Empathy & Warmth (1 AM)", fontsize=11, weight="bold")
        axes[3].grid(axis="y", linestyle="--", alpha=0.5)
        axes[3].text(0, metrics["mean_tone_score"] + 0.1, f"{metrics['mean_tone_score']:.2f} / 5.0", ha="center", weight="bold")

        plt.suptitle("Ilm Academy Socratic AI Tutor: 50-Conversation Benchmark & Safety Audit", fontsize=13, weight="bold", y=1.03)
        plt.tight_layout()
        plt.savefig(output_fig)
        plt.close()

        metrics["figure_path"] = output_fig
        metrics["json_path"] = output_json
        return metrics
