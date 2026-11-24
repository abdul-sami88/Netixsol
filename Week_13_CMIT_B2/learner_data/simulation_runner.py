"""
Learner Simulation Runner
Executes 1,000 student simulation and benchmark data preparation.
"""

import json
from learner_data.assistments_ednet_loader import BenchmarkDataLoader
from learner_data.student_simulator import StudentSimulator
from question_bank.question_generator import QuestionBankGenerator

def run_full_simulation():
    print("=" * 60)
    print("STEP 1: Generating ASSISTments / EdNet Benchmark Dataset")
    print("=" * 60)
    b_df = BenchmarkDataLoader.generate_synthetic_assistments_benchmark()
    b_metrics = BenchmarkDataLoader.compute_benchmark_metrics(b_df)
    print(f"Loaded {b_metrics['total_benchmark_records']} benchmark interactions.")
    print(f"Benchmark Mean Accuracy: {b_metrics['benchmark_mean_accuracy'] * 100:.1f}%")
    print(f"Benchmark Mean Response Time: {b_metrics['benchmark_mean_time_sec']}s")

    print("\n" + "=" * 60)
    print("STEP 2: Initializing 1,000 Student Cognitive Simulator")
    print("=" * 60)
    q_gen = QuestionBankGenerator()
    questions = q_gen.generate_all_questions()

    simulator = StudentSimulator(num_students=1000, seed=42)
    students = simulator.generate_students()
    print(f"Created {len(students)} synthetic students across 4 archetypes.")

    print("\n" + "=" * 60)
    print("STEP 3: Simulating 8-Week Linear Curriculum Progression")
    print("=" * 60)
    df_students, df_interactions = simulator.simulate_curriculum(questions)
    simulator.save_datasets(df_students, df_interactions)

    # Dropout breakdown
    w1_drop = len(df_students[df_students["dropout_week"] == 1])
    w2_drop = len(df_students[df_students["dropout_week"] == 2])
    w3_drop = len(df_students[df_students["dropout_week"] == 3])
    pre_w4_drop = w1_drop + w2_drop + w3_drop
    total_drop = len(df_students[df_students["is_dropped_out"] == True])
    completed = len(df_students[df_students["is_dropped_out"] == False])

    print("\n--- Cohort Retention & Dropout Metrics ---")
    print(f"Week 1 Dropouts: {w1_drop} ({w1_drop / 10:.1f}%)")
    print(f"Week 2 Dropouts: {w2_drop} ({w2_drop / 10:.1f}%)")
    print(f"Week 3 Dropouts: {w3_drop} ({w3_drop / 10:.1f}%)")
    print(f"-> CUMULATIVE DROPOUT BEFORE WEEK 4: {pre_w4_drop} / 1000 ({pre_w4_drop / 10:.1f}%)")
    print(f"Total Dropped Out (All 8 Weeks): {total_drop} ({total_drop / 10:.1f}%)")
    print(f"Total Completed Course: {completed} ({completed / 10:.1f}%)")
    print(f"Total Learner Interactions Logged: {len(df_interactions):,}")

    return df_students, df_interactions

if __name__ == "__main__":
    run_full_simulation()

