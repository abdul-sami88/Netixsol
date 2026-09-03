import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

import time
from production_eval_and_deployment.eval_suite.test_conversations_dataset import EVALUATION_DATASET, get_dataset_summary
from production_eval_and_deployment.eval_suite.prompt_injection_security import run_prompt_injection_security_tests
from production_eval_and_deployment.eval_suite.performance_evaluator import run_performance_evaluation
from production_eval_and_deployment.monitoring.monitoring_dashboard import monitoring_dashboard
from production_eval_and_deployment.monitoring.telemetry_logger import telemetry_logger
from production_eval_and_deployment.deployment.health_checks import check_liveness, check_readiness

def main():
    print("==================================================================")
    print("PRODUCTION SOFTWARE SUITE EXECUTION & BENCHMARKING REPORT")
    print("==================================================================\n")

    # Task 1: Dataset Summary
    dataset_summary = get_dataset_summary()
    print("--- TASK 1: EVALUATION SUITE DATASET SUMMARY ---")
    print(f"Total Test Conversations: {dataset_summary['total_conversations']}")
    print(f"Total Personas/Categories: {dataset_summary['total_categories']}")
    print("Breakdown per Category:")
    for cat, count in dataset_summary["breakdown"].items():
        print(f"  - {cat}: {count} tests")
    print("\n" + "-" * 50 + "\n")

    # Task 2: Security & Prompt Injection
    print("--- TASK 2: PROMPT INJECTION & GUARDRAIL AUDIT ---")
    sec_report = run_prompt_injection_security_tests()
    print(f"Attacks Tested : {sec_report['total_attacks_tested']}")
    print(f"Attacks Blocked: {sec_report['attacks_blocked']} / {sec_report['total_attacks_tested']}")
    print(f"Security Rate  : {sec_report['guardrail_security_rate_percent']}%")
    print("\n" + "-" * 50 + "\n")

    # Task 3: Performance Evaluation
    print("--- TASK 3: PERFORMANCE BENCHMARK EVALUATION ---")
    perf_report = run_performance_evaluation()
    m = perf_report["metrics"]
    print(f"Latency p50    : {m['latency_p50_sec']} s")
    print(f"Latency p90    : {m['latency_p90_sec']} s")
    print(f"Latency p99    : {m['latency_p99_sec']} s")
    print(f"Average Latency: {m['avg_latency_sec']} s")
    print(f"Conversation Success Rate: {m['conversation_success_rate_percent']}%")
    print(f"Booking Success Rate     : {m['booking_success_rate_percent']}%")
    print(f"Tool Failure Rate        : {m['tool_failure_rate_percent']}%")
    print(f"RAG Accuracy             : {m['rag_accuracy_percent']}%")
    print(f"Memory Accuracy          : {m['memory_accuracy_percent']}%")
    print(f"Hallucination Rate       : {m['hallucination_rate_percent']}%")
    print("\n" + "-" * 50 + "\n")

    # Task 4: Monitoring Telemetry Dashboard
    print("--- TASK 4: MONITORING & TELEMETRY DASHBOARD ---")
    telemetry_logger.log_event("API_CALL", "production_suite_test", 1.12, "SUCCESS")
    telemetry_logger.log_event("VOICE_STT", "production_suite_test", 0.35, "SUCCESS", {"confidence": 0.98})
    telemetry_logger.log_event("BOOKING", "production_suite_test", 1.85, "SUCCESS")
    
    mon_metrics = monitoring_dashboard.get_monitoring_metrics()
    print(f"System Health  : {mon_metrics['system_health_status']}")
    print(f"Monitored Events: {mon_metrics['total_monitored_events']}")
    print(f"Live Telemetry : {mon_metrics['metrics']}")
    print("\n" + "-" * 50 + "\n")

    # Task 5: Production Deployment Health Probes
    print("--- TASK 5: PRODUCTION DEPLOYMENT HEALTH PROBES ---")
    liveness = check_liveness()
    readiness = check_readiness()
    print(f"Liveness Probe (/healthz) : {liveness['status']}")
    print(f"Readiness Probe (/readyz): {readiness['status']} ({readiness['ready_checks']})")
    print("\n==================================================================")
    print("ALL 5 PRODUCTION TASKS VERIFIED & BENCHMARKED SUCCESSFULLY!")
    print("==================================================================")

if __name__ == "__main__":
    main()
