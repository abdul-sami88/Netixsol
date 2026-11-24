"""
Sandbox Attack Evaluation Runner & Reporter
Executes all attack payloads, verifies containment (AST interception vs timeout vs runtime error),
and generates visualization and structured JSON report.
"""

import json
import os
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from grading_sandbox.secure_sandbox import SecureCodeSandbox
from grading_sandbox.attack_test_suite import ATTACK_PAYLOADS

def run_attack_suite() -> dict:
    sandbox = SecureCodeSandbox(timeout_sec=2.0)
    results = []
    contained_count = 0

    print("=" * 70)
    print("RUNNING DAY 4 SECURE SANDBOX ATTACK VERIFICATION SUITE")
    print("=" * 70)

    for atk in ATTACK_PAYLOADS:
        atk_id = atk["attack_id"]
        name = atk["name"]
        cat = atk["category"]
        code = atk["code"]

        res = sandbox.execute_code(code)
        is_contained = res.get("is_contained", False) and res.get("verdict") in [
            "SECURITY_VIOLATION", "TIME_LIMIT_EXCEEDED", "RUNTIME_ERROR"
        ]

        if is_contained:
            contained_count += 1
            status_symbol = "[CONTAINED]"
        else:
            status_symbol = "[FAILED]"

        print(f"{status_symbol} {atk_id}: {name} ({cat})")
        print(f"   Verdict: {res['verdict']} | Exec Time: {res['execution_time_sec']}s")
        if res.get("violations"):
            print(f"   Interception Reason: {res['violations'][0]}")
        elif res.get("stderr"):
            print(f"   Interception Reason: {res['stderr'][:80]}...")

        results.append({
            "attack_id": atk_id,
            "name": name,
            "category": cat,
            "expected_defense": atk["expected_defense"],
            "verdict": res["verdict"],
            "execution_time_sec": res["execution_time_sec"],
            "is_contained": is_contained,
            "details": res.get("violations") or [res.get("stderr", "")]
        })

    total = len(ATTACK_PAYLOADS)
    containment_rate = (contained_count / total) * 100.0

    print("-" * 70)
    print(f"SUMMARY: {contained_count}/{total} Attacks Contained ({containment_rate:.1f}%)")
    print("=" * 70)

    summary = {
        "total_attacks_tested": total,
        "attacks_contained": contained_count,
        "containment_rate_pct": containment_rate,
        "sandbox_policy": {
            "wall_clock_timeout_sec": 2.0,
            "environment_isolation": "Sanitized Minimal Subprocess (-I mode)",
            "network_egress": "Disabled",
            "ast_security_screening": "Active (banned modules, builtins, dunder attributes)"
        },
        "attack_results": results
    }

    # Save JSON report
    os.makedirs("day4_reports", exist_ok=True)
    json_path = os.path.join("day4_reports", "sandbox_attack_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Report exported to: {json_path}")

    # Generate Chart
    generate_attack_figure(results, containment_rate)

    return summary


def generate_attack_figure(results: list, containment_rate: float):
    os.makedirs("figures", exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw={'width_ratios': [1.3, 1]})

    # Bar chart of response times by attack
    names = [r["name"] for r in results]
    times = [r["execution_time_sec"] for r in results]
    colors = ["#2ecc71" if r["verdict"] == "SECURITY_VIOLATION" else "#f39c12" if r["verdict"] == "TIME_LIMIT_EXCEEDED" else "#3498db" for r in results]

    bars = ax1.barh(names[::-1], times[::-1], color=colors[::-1], edgecolor="#2c3e50", height=0.6)
    ax1.set_xlabel("Containment / Execution Time (seconds)", fontsize=11, fontweight="bold")
    ax1.set_title("Attack Containment Latency by Vector", fontsize=12, fontweight="bold", pad=12)
    ax1.axvline(2.0, color="#e74c3c", linestyle="--", linewidth=1.5, label="Timeout Threshold (2.0s)")
    ax1.set_xlim(0, 2.5)
    ax1.legend(loc="lower right")

    # Add labels on bars
    for bar in bars:
        w = bar.get_width()
        ax1.text(w + 0.05, bar.get_y() + bar.get_height()/2, f"{w:.2f}s", va="center", fontsize=9, fontweight="bold")

    # Defense Mechanism Distribution Pie Chart
    mechanisms = {}
    for r in results:
        v = r["verdict"]
        label = "AST Pre-Screening" if v == "SECURITY_VIOLATION" else "Subprocess CPU Timeout" if v == "TIME_LIMIT_EXCEEDED" else "Runtime Trap"
        mechanisms[label] = mechanisms.get(label, 0) + 1

    pie_labels = list(mechanisms.keys())
    pie_counts = list(mechanisms.values())
    pie_colors = ["#2ecc71", "#f39c12", "#3498db"][:len(pie_labels)]

    ax2.pie(
        pie_counts,
        labels=pie_labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=pie_colors,
        wedgeprops=dict(width=0.4, edgecolor='white', linewidth=2),
        textprops=dict(fontsize=10, fontweight="bold")
    )
    ax2.set_title(f"Defense Layer Breakdown\n(Overall Containment: {containment_rate:.0f}%)", fontsize=12, fontweight="bold", pad=12)

    plt.suptitle("Ilm Academy Code Sandbox Attack Containment Benchmark", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()

    out_path = os.path.join("figures", "sandbox_attack_report.png")
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Chart generated at: {out_path}")


if __name__ == "__main__":
    run_attack_suite()
