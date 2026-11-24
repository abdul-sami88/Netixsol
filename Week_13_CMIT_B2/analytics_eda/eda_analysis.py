"""
Analytics and EDA Module
Analyzes 1,000 student interactions, computes accuracy per concept, learning curves,
dropout survival analysis, hardest concepts ranking, and generates publication charts.
"""

from typing import Dict, Any, List, Tuple
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class LearnerAnalyticsEDA:
    """
    Performs comprehensive exploratory data analysis on student simulator interactions.
    """

    def __init__(
        self,
        interactions_csv: str = "learner_data/data/student_interactions.csv",
        students_csv: str = "learner_data/data/students_profile.csv",
        figures_dir: str = "figures"
    ):
        self.interactions_csv = interactions_csv
        self.students_csv = students_csv
        self.figures_dir = figures_dir
        os.makedirs(figures_dir, exist_ok=True)

        self.df_interactions = pd.read_csv(interactions_csv)
        self.df_students = pd.read_csv(students_csv)

    def analyze_accuracy_per_concept(self) -> pd.DataFrame:
        """
        Calculates accuracy, interaction count, avg time, and avg attempts per concept.
        """
        concept_stats = self.df_interactions.groupby("concept_id").agg(
            total_attempts=("is_correct", "count"),
            correct_count=("is_correct", "sum"),
            accuracy=("is_correct", "mean"),
            avg_time_sec=("time_taken_seconds", "mean"),
            avg_attempts=("attempt_count", "mean"),
            avg_hints=("hints_used", "mean")
        ).reset_index()

        concept_stats["accuracy_pct"] = (concept_stats["accuracy"] * 100).round(1)
        concept_stats["avg_time_sec"] = concept_stats["avg_time_sec"].round(1)
        concept_stats = concept_stats.sort_values("accuracy", ascending=True).reset_index(drop=True)
        return concept_stats

    def analyze_learning_curves(self) -> pd.DataFrame:
        """
        Calculates accuracy trajectory across sequential attempts grouped by archetype.
        """
        # Create sequence order per student
        df = self.df_interactions.copy()
        df["attempt_sequence"] = df.groupby(["student_id"]).cumcount() + 1

        # Bin attempts into sequential opportunities (e.g. 1-5, 6-10, 11-15, etc.)
        df["opportunity_window"] = pd.cut(
            df["attempt_sequence"],
            bins=[0, 5, 10, 15, 20, 30, 45, 60],
            labels=["1-5", "6-10", "11-15", "16-20", "21-30", "31-45", "46+"]
        )

        learning_curves = df.groupby(["archetype", "opportunity_window"], observed=False)["is_correct"].mean().unstack(level=0)
        return learning_curves

    def analyze_dropout_points(self) -> Dict[str, Any]:
        """
        Analyzes weekly attrition, cumulative dropouts, and hazard rates.
        """
        total_students = len(self.df_students)
        weekly_drops = self.df_students["dropout_week"].value_counts().to_dict()

        retention_data = []
        cumulative_dropped = 0
        active_at_start = total_students

        for w in range(1, 9):
            dropped_this_week = weekly_drops.get(w, 0)
            cumulative_dropped += dropped_this_week
            hazard_rate = dropped_this_week / active_at_start if active_at_start > 0 else 0
            active_at_end = total_students - cumulative_dropped
            retention_rate = active_at_end / total_students

            retention_data.append({
                "week": w,
                "active_start": active_at_start,
                "dropped": dropped_this_week,
                "cumulative_dropped": cumulative_dropped,
                "cumulative_dropout_pct": round(cumulative_dropped / total_students * 100, 1),
                "active_end": active_at_end,
                "retention_pct": round(retention_rate * 100, 1),
                "hazard_rate_pct": round(hazard_rate * 100, 1)
            })
            active_at_start = active_at_end

        df_retention = pd.DataFrame(retention_data)
        pre_w4_drops = df_retention[df_retention["week"] <= 3]["dropped"].sum()

        return {
            "retention_table": df_retention,
            "pre_week_4_dropouts": int(pre_w4_drops),
            "pre_week_4_dropout_pct": round(pre_w4_drops / total_students * 100, 1)
        }

    def analyze_hardest_concepts(self, top_n: int = 10) -> pd.DataFrame:
        """
        Identifies the top hardest concepts based on lowest accuracy and highest friction.
        """
        concept_df = self.analyze_accuracy_per_concept()
        hardest = concept_df.head(top_n).copy()
        hardest["rank"] = range(1, len(hardest) + 1)
        return hardest

    def plot_accuracy_per_concept(self, output_path: str = "figures/accuracy_per_concept.png") -> str:
        """Generates horizontal bar chart of accuracy across all concepts."""
        df = self.analyze_accuracy_per_concept()

        plt.figure(figsize=(14, 16), dpi=150)
        plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

        colors = ['#ef4444' if acc < 0.50 else '#f59e0b' if acc < 0.70 else '#10b981' for acc in df["accuracy"]]

        bars = plt.barh(df["concept_id"], df["accuracy_pct"], color=colors, height=0.65)
        plt.axvline(50, color='#ef4444', linestyle='--', alpha=0.8, label='Critical Failure Threshold (50%)')
        plt.axvline(70, color='#10b981', linestyle='--', alpha=0.8, label='Mastery Benchmark (70%)')

        for bar in bars:
            w = bar.get_width()
            plt.text(w + 1.0, bar.get_y() + bar.get_height() / 2, f"{w:.1f}%", va='center', fontsize=8, color='#334155')

        plt.title("Ilm Academy: Learner Accuracy per Python Concept (N=1,000 Students)", fontsize=14, weight='bold', pad=15)
        plt.xlabel("Average Accuracy (%)", fontsize=11, labelpad=10)
        plt.ylabel("Concept ID", fontsize=11)
        plt.xlim(0, 100)
        plt.legend(loc='lower right', frameon=True)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return output_path

    def plot_learning_curves(self, output_path: str = "figures/learning_curves.png") -> str:
        """Plots longitudinal learning curves by student archetype."""
        df = self.analyze_learning_curves()

        plt.figure(figsize=(11, 6), dpi=150)
        palette = {
            "Fast-Paced Explorer": "#059669",
            "Steady Learner": "#2563eb",
            "Struggling Novice": "#d97706",
            "At-Risk Disengaged": "#dc2626"
        }

        for arch in df.columns:
            plt.plot(df.index, df[arch] * 100, marker='o', linewidth=2.5, label=arch, color=palette.get(arch, '#64748b'))

        plt.title("Longitudinal Learning Curves: Accuracy Trajectory Across Opportunities", fontsize=13, weight='bold', pad=14)
        plt.xlabel("Sequential Opportunity Window (Question Attempts)", fontsize=11, labelpad=10)
        plt.ylabel("Mean Accuracy (%)", fontsize=11, labelpad=10)
        plt.ylim(10, 100)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend(title="Student Archetype", frameon=True, loc='lower right')
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return output_path

    def plot_dropout_survival_curve(self, output_path: str = "figures/dropout_survival_curve.png") -> str:
        """Plots survival curve and hazard rate over weeks."""
        retention = self.analyze_dropout_points()["retention_table"]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=150)

        # Plot 1: Cumulative Retention (Survival)
        ax1.plot(retention["week"], retention["retention_pct"], marker='s', color='#2563eb', lw=2.5, label='Active Cohort %')
        ax1.fill_between(retention["week"], retention["retention_pct"], color='#3b82f6', alpha=0.15)
        ax1.axvline(3, color='#dc2626', linestyle=':', lw=2, label='Week 3 Bottleneck Cliff')
        ax1.scatter([3], [retention.loc[retention["week"]==3, "retention_pct"].values[0]], color='#dc2626', s=90, zorder=5)
        ax1.text(3.1, retention.loc[retention["week"]==3, "retention_pct"].values[0] - 4,
                 f"Pre-W4 Drop: {retention.loc[retention['week']==3, 'cumulative_dropout_pct'].values[0]}%",
                 color='#dc2626', weight='bold')

        ax1.set_title("Student Retention Curve (Kaplan-Meier Survival)", fontsize=12, weight='bold')
        ax1.set_xlabel("Curriculum Week", fontsize=10)
        ax1.set_ylabel("Retention Rate (%)", fontsize=10)
        ax1.set_ylim(20, 105)
        ax1.grid(True, linestyle='--', alpha=0.6)
        ax1.legend(loc='lower left')

        # Plot 2: Weekly Hazard Rate
        ax2.bar(retention["week"], retention["hazard_rate_pct"], color='#ef4444', alpha=0.85, width=0.55)
        ax2.set_title("Weekly Hazard Rate (Dropout Probability)", fontsize=12, weight='bold')
        ax2.set_xlabel("Curriculum Week", fontsize=10)
        ax2.set_ylabel("Hazard Rate (% Active Dropping)", fontsize=10)
        ax2.grid(True, linestyle='--', alpha=0.6)

        for _, row in retention.iterrows():
            ax2.text(row["week"], row["hazard_rate_pct"] + 0.8, f"{row['hazard_rate_pct']:.1f}%",
                     ha='center', fontsize=9, weight='bold', color='#1e293b')

        plt.suptitle("Ilm Academy Attrition Analysis: The Week 3 Dropout Cliff", fontsize=14, weight='bold', y=1.02)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return output_path

    def plot_hardest_concepts(self, output_path: str = "figures/hardest_concepts.png") -> str:
        """Plots Top 10 Hardest Concepts with error rates and response time friction."""
        df_hard = self.analyze_hardest_concepts(top_n=10)
        df_hard["error_rate_pct"] = (100 - df_hard["accuracy_pct"]).round(1)

        fig, ax1 = plt.subplots(figsize=(12, 6), dpi=150)
        ax2 = ax1.twinx()

        x = np.arange(len(df_hard))
        width = 0.35

        rects1 = ax1.bar(x - width/2, df_hard["error_rate_pct"], width, label='Error Rate (%)', color='#e11d48')
        rects2 = ax2.bar(x + width/2, df_hard["avg_time_sec"], width, label='Avg Time (sec)', color='#0284c7')

        ax1.set_ylabel('Error Rate (%)', color='#e11d48', fontsize=11, weight='bold')
        ax2.set_ylabel('Average Response Time (Seconds)', color='#0284c7', fontsize=11, weight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(df_hard["concept_id"], rotation=35, ha='right', fontsize=9.5)

        ax1.set_ylim(0, 80)
        ax2.set_ylim(0, 70)
        ax1.grid(False)
        ax2.grid(False)

        plt.title("Top 10 Hardest Python Concepts: Error Rates & Time Friction", fontsize=13, weight='bold', pad=15)
        fig.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return output_path

    def generate_all_plots(self) -> Dict[str, str]:
        """Generates and saves all 4 primary analytics figures."""
        p1 = self.plot_accuracy_per_concept(os.path.join(self.figures_dir, "accuracy_per_concept.png"))
        p2 = self.plot_learning_curves(os.path.join(self.figures_dir, "learning_curves.png"))
        p3 = self.plot_dropout_survival_curve(os.path.join(self.figures_dir, "dropout_survival_curve.png"))
        p4 = self.plot_hardest_concepts(os.path.join(self.figures_dir, "hardest_concepts.png"))

        return {
            "accuracy_per_concept": p1,
            "learning_curves": p2,
            "dropout_survival_curve": p3,
            "hardest_concepts": p4
        }

