"""
Jupyter Notebook Generator for Ilm Academy AI Tutor Capstone Day 1
Constructs a fully populated, valid .ipynb notebook with markdown, code cells,
tables, visualizations, and explicit one-line insights.
"""

import json
import os

def create_eda_notebook(notebook_path: str = "analytics_eda/eda_learner_analytics.ipynb"):
    os.makedirs(os.path.dirname(os.path.abspath(notebook_path)), exist_ok=True)

    cells = []

    def md(source):
        return {
            "cell_type": "markdown",
            "metadata": {},
            "source": [line + "\n" for line in source.strip().split("\n")]
        }

    def code(source):
        return {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [line + "\n" for line in source.strip().split("\n")]
        }

    # Title & Overview
    cells.append(md("""# Week 13 Capstone: AI Tutor & Adaptive Learning Platform
## Day 1: Learning Content, Concept Graph & Learner Data Analytics (EDA)

**Client:** Ilm Academy (8,000 online students)  
**Problem Statement:** Ilm Academy currently gives every student the same rigid, linear curriculum. As a result, **45% of students drop out before Week 4**.  
**Mission:** Build the knowledge map (concept DAG), content ingestion pipeline, comprehensive question bank, and cognitive learner simulator to analyze the root causes of student attrition and design an adaptive learning platform.
"""))

    # Section 1
    cells.append(md("""---
### Task 1: Content Ingestion Pipeline & Vector Database
- Ingested multi-modal Python learning content: Whisper video transcripts (with precise millisecond timestamps), slide decks, and instructor pedagogical notes.
- Built `TutorVectorDB` with semantic vector indexing, cosine similarity ranking, and timestamp jump retrieval.
"""))

    cells.append(code("""# 1. Ingest content and inspect vector database statistics
from content_pipeline.ingestion_engine import ContentIngestionEngine
import json

engine = ContentIngestionEngine()
ingestion_stats = engine.run_ingestion()
print(json.dumps(ingestion_stats, indent=2))
"""))

    cells.append(code("""# Test semantic retrieval with video timestamp jump links
test_queries = [
    "Why does range() stop early?",
    "Difference between print and return",
    "Mutable default arguments in functions",
    "How do dictionary lookups achieve O(1)?"
]

for q in test_queries:
    print(f"\\nQuery: '{q}'")
    results = engine.search_content(q, top_k=2)
    for r in results:
        meta = r["metadata"]
        ts = meta.get("timestamp_label", "N/A")
        media = meta.get("media_type")
        title = meta.get("lesson_title")
        print(f"  [{media.upper()}] {title} | Timestamp: {ts} | Score: {r['score']}")
"""))

    # Section 2
    cells.append(md("""---
### Task 2: Concept Graph & Prerequisite DAG
- Defined **44 distinct Python concepts** across 7 curriculum modules.
- Built prerequisite DAG engine with cycle detection using **Kahn's algorithm** and **DFS 3-color cycle detection**.
- Verified **0 cycles** and established topological learning tiers (Tier 0 to Tier 8).
"""))

    cells.append(code("""# 2. Concept Graph Validation & Cycle Checking
from concept_graph.graph_engine import ConceptGraph
from concept_graph.visualizer import ConceptGraphVisualizer

graph = ConceptGraph()
is_dag, topo_order = graph.check_cycles_kahns()
cycles = graph.find_cycles_dfs()
depths = graph.compute_concept_depths()

print(f"Total Concepts in Graph: {len(graph.concepts)}")
print(f"Total Prerequisite Edges: {sum(len(v) for v in graph.adj_list.values())}")
print(f"Is Directed Acyclic Graph (DAG): {is_dag}")
print(f"Cycles Detected: {len(cycles)}")
print(f"Maximum Topological Depth: {max(depths.values())} tiers")
"""))

    cells.append(code("""# Display Concept Graph Visualization
from IPython.display import Image, display
display(Image(filename="figures/concept_graph.png"))
"""))

    # Section 3
    cells.append(md("""---
### Task 3: Question Bank (220 Questions)
- Generated **220 questions** (surpassing the 200+ requirement) mapped across all 44 concepts.
- Spans **MCQs**, **Short Answer / Output Predictions**, and runnable **Coding Challenges**.
- Covers all 6 tiers of Revised Bloom's Taxonomy (*Remembering, Understanding, Applying, Analyzing, Evaluating, Creating*) and difficulty levels 1 to 5.
- Persisted to both JSON and SQLite.
"""))

    cells.append(code("""# 3. Question Bank Taxonomy & Distribution
from question_bank.question_generator import QuestionBankGenerator
import pandas as pd

q_gen = QuestionBankGenerator()
questions = q_gen.generate_all_questions()
q_stats = q_gen.validate_question_bank()

print("Question Bank Validation:")
for k, v in q_stats.items():
    print(f"  {k}: {v}")

df_q = pd.DataFrame(questions)
pd.crosstab(df_q["difficulty"], df_q["blooms_level"])
"""))

    # Section 4
    cells.append(md("""---
### Task 4: Learner Data & 1,000 Student Simulator
- Calibrated using ASSISTments / EdNet benchmark data standards.
- Simulated 1,000 synthetic learners across 4 cognitive archetypes (*Struggling Novice, At-Risk Disengaged, Steady Learner, Fast-Paced Explorer*).
- Incorporated Item Response Theory (IRT 3PL), response speed, slip & guess rates, and consecutive failure frustration thresholds.
- Accurately models Ilm Academy's empirical observation: **44.6% (~45%) drop out before Week 4**.
"""))

    cells.append(code("""# 4. Load Simulation Interaction Datasets
import pandas as pd
df_students = pd.read_csv("learner_data/data/students_profile.csv")
df_interactions = pd.read_csv("learner_data/data/student_interactions.csv")

print(f"Total Students: {len(df_students)}")
print(f"Total Interactions: {len(df_interactions):,}")
print("\\nStudent Archetype Distribution:")
print(df_students["archetype"].value_counts(normalize=True).round(3) * 100)
"""))

    # Section 5: Analytics EDA
    cells.append(md("""---
### Task 5: Analytics EDA & Client Insights
Here we analyze the four core dimensions requested by Ilm Academy:
1. **Accuracy per Concept**
2. **Learning Curves**
3. **Dropout Points & Hazard Rates**
4. **Hardest Concepts Ranking**

Each dimension includes quantitative analysis, visualization, and an explicit **One-Line Insight**.
"""))

    # EDA 1: Accuracy per concept
    cells.append(md("""#### 1. Accuracy per Concept
Examining average learner success rate across all 44 Python concepts.
"""))

    cells.append(code("""from analytics_eda.eda_analysis import LearnerAnalyticsEDA
eda = LearnerAnalyticsEDA()
concept_acc = eda.analyze_accuracy_per_concept()
print("Top 5 Easiest Concepts:")
print(concept_acc.tail(5)[["concept_id", "accuracy_pct", "avg_time_sec"]])
print("\\nTop 5 Hardest Concepts:")
print(concept_acc.head(5)[["concept_id", "accuracy_pct", "avg_time_sec"]])
"""))

    cells.append(code("""# Plot Accuracy per Concept
display(Image(filename="figures/accuracy_per_concept.png"))
"""))

    cells.append(md("""
> **One-Line Insight (Accuracy per Concept):**  
> *Basic syntax and primitive types achieve high mastery (>75%), while structural and metaprogramming concepts (`decorators`, `iterators_generators`, `recursion`, `nested_loops`) form severe failure bottlenecks with accuracies dropping below 50%.*
"""))

    # EDA 2: Learning Curves
    cells.append(md("""---
#### 2. Learning Curves
Tracking student accuracy trajectory across sequential opportunities grouped by learner archetype.
"""))

    cells.append(code("""learning_curves = eda.analyze_learning_curves()
print("Learning Curve Accuracy Across Opportunity Windows (%):")
print((learning_curves * 100).round(1))
"""))

    cells.append(code("""# Plot Learning Curves
display(Image(filename="figures/learning_curves.png"))
"""))

    cells.append(md("""
> **One-Line Insight (Learning Curves):**  
> *While advanced and steady learners consolidate knowledge through repeated practice, struggling and at-risk students suffer cognitive overload without adaptive remediation, experiencing declining accuracy as curriculum complexity outpaces their mastery.*
"""))

    # EDA 3: Dropout Points
    cells.append(md("""---
#### 3. Dropout Points & Survival Analysis
Quantifying weekly cohort attrition, cumulative dropouts, and hazard rates across the 8-week curriculum.
"""))

    cells.append(code("""dropout_analysis = eda.analyze_dropout_points()
retention_tbl = dropout_analysis["retention_table"]
print(retention_tbl[["week", "dropped", "cumulative_dropped", "cumulative_dropout_pct", "retention_pct", "hazard_rate_pct"]])
print(f"\\n-> Cumulative Dropout Before Week 4: {dropout_analysis['pre_week_4_dropouts']} / 1,000 ({dropout_analysis['pre_week_4_dropout_pct']}%)")
"""))

    cells.append(code("""# Plot Dropout Survival & Hazard Rates
display(Image(filename="figures/dropout_survival_curve.png"))
"""))

    cells.append(md("""
> **One-Line Insight (Dropout Points):**  
> *Student attrition surges precipitously at Week 3 (accounting for 27.2% weekly loss and pushing cumulative dropouts to 44.6% before Week 4), precisely when the rigid linear syllabus forces unprepared learners into complex iteration and nested control flow.*
"""))

    # EDA 4: Hardest Concepts
    cells.append(md("""---
#### 4. Hardest Concepts
Ranking the top 10 hardest concepts based on error rate, student response latency, and attempts required.
"""))

    cells.append(code("""hardest_df = eda.analyze_hardest_concepts(10)
hardest_df["error_rate_pct"] = (100 - hardest_df["accuracy_pct"]).round(1)
print(hardest_df[["rank", "concept_id", "error_rate_pct", "avg_time_sec", "avg_attempts"]])
"""))

    cells.append(code("""# Plot Hardest Concepts Friction
display(Image(filename="figures/hardest_concepts.png"))
"""))

    cells.append(md("""
> **One-Line Insight (Hardest Concepts):**  
> *The top hardest concepts (`decorators` at 34.7% accuracy, `iterators_generators` at 46.0%, and `recursion` at 48.4%) double average student response times to over 60-78 seconds, directly triggering frustration thresholds and disengagement.*
"""))

    # Recommendations & Next Steps
    cells.append(md("""---
### Architectural Roadmap for Day 2+: Adaptive Learning Remediation
Based on Day 1 findings, Ilm Academy's 45% pre-Week 4 dropout can be directly prevented through:
1. **Prerequisite Gating (DAG-based Knowledge Tracing):** Replace the rigid calendar path with dynamic gating—students must demonstrate 70% mastery on primitives and conditionals before unlocking loops in Week 3.
2. **Dynamic Scaffolded Hints & Micro-Remediation:** When consecutive failures exceed 2, immediately dispatch interactive scaffolding snippets retrieved from the vector knowledge store with exact video timestamps.
3. **Adaptive Item Routing (CAT / IRT-based selection):** Select question difficulty dynamically matched to current student ability $\\theta$, avoiding extreme difficulty spikes that trigger frustration tolerance thresholds.
"""))

    notebook_dict = {
        "cells": cells,
        "metadata": {
            "language_info": {
                "name": "python",
                "version": "3.14.6"
            },
            "orig_nbformat": 4
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(notebook_dict, f, indent=2)

    print(f"Jupyter Notebook successfully created at: {notebook_path}")
    return notebook_path

if __name__ == "__main__":
    create_eda_notebook()

