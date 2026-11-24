# Week 13 Capstone: AI Tutor & Adaptive Learning Platform
## Day 1: Learning Content, Concept Graph & Learner Data

### Client Overview: Ilm Academy
**Cohort:** 8,000 online Python students  
**Core Problem:** Ilm Academy provides a single, uniform linear path to every student. By Week 4, **45% of all enrolled students drop out**.  
**Day 1 Goal:** Map the learning domain (content ingestion pipeline + prerequisite concept DAG), establish a standardized question bank (200+ questions), calibrate student cognitive simulation (1,000 students), and execute exploratory data analytics (EDA) to diagnose the root causes of student churn.

---

## Deliverables Summary

| Deliverable | Location | Description |
| :--- | :--- | :--- |
| **Content Pipeline** | `content_pipeline/` | Whisper video transcription parser (millisecond timestamps), slide deck & notes extractor, and semantic `TutorVectorDB`. |
| **Concept Graph** | `concept_graph/` | 44 Python concepts, prerequisite DAG, Kahn's algorithm & DFS 3-color cycle detection (0 cycles), static & interactive visualizers. |
| **Question Bank** | `question_bank/` | 220 questions (MCQ, Short Answer, Coding), tagged with concept, difficulty (1-5), and Bloom's level. Exported to JSON & SQLite. |
| **Learner Data Simulator** | `learner_data/` | ASSISTments benchmark integration, 1,000-student simulator (IRT 3PL, speed, slip, guess, frustration) reproducing the 44.6% (~45%) pre-Week 4 dropout. |
| **Analytics EDA Notebook** | `analytics_eda/eda_learner_analytics.ipynb` | Comprehensive Jupyter Notebook with executed metrics, figures, and explicit One-Line Insights for all findings. |

---

## 4 Core EDA Findings & Explicit One-Line Insights

1. **Accuracy per Concept:**
   > *"Basic syntax and primitive types achieve high mastery (>75%), while structural and metaprogramming concepts (`decorators`, `iterators_generators`, `recursion`, `nested_loops`) form severe failure bottlenecks with accuracies dropping below 50%."*

2. **Learning Curves:**
   > *"While advanced and steady learners consolidate knowledge through repeated practice, struggling and at-risk students suffer cognitive overload without adaptive remediation, experiencing declining accuracy as curriculum complexity outpaces their mastery."*

3. **Dropout Points & Hazard Rates:**
   > *"Student attrition surges precipitously at Week 3 (accounting for 27.2% weekly loss and pushing cumulative dropouts to 44.6% before Week 4), precisely when the rigid linear syllabus forces unprepared learners into complex iteration and nested control flow."*

4. **Hardest Concepts Ranking:**
   > *"The top hardest concepts (`decorators` at 34.7% accuracy, `iterators_generators` at 46.0%, and `recursion` at 48.4%) double average student response times to over 60-78 seconds, directly triggering frustration thresholds and disengagement."*

---

## Quickstart & Execution

To run the complete end-to-end verification and pipeline:
```bash
python main.py
```

To run individual modules:
```bash
# Task 1: Ingest lesson content into vector database
python -m content_pipeline.ingestion_engine

# Task 2: Validate concept DAG and generate visualizations
python -c "from concept_graph.graph_engine import ConceptGraph; g = ConceptGraph(); print('Is DAG:', g.check_cycles_kahns()[0])"

# Task 3: Generate and validate 220+ question bank
python -c "from question_bank.question_generator import QuestionBankGenerator; gen = QuestionBankGenerator(); print(gen.validate_question_bank())"

# Task 4: Run 1,000 student simulator
python -m learner_data.simulation_runner

# Task 5: Generate analytics plots and Jupyter Notebook
python -m analytics_eda.generate_notebook
```

