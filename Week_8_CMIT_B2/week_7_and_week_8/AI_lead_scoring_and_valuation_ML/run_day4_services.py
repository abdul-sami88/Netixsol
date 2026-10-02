"""
run_day4_services.py
====================
Master orchestrator to verify and launch Day 4 services:
1. Verifies saved model artifacts and metadata
2. Runs FastAPI Model Serving tests
3. Runs LangGraph AI Assistant tests
4. Demonstrates how to start FastAPI server (port 8000) and Streamlit dashboard (port 8501)
"""

import os
import sys
import subprocess
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

def main():
    print("=" * 80)
    print(" DAY 4: MODEL SERVING, AI ASSISTANT & STREAMLIT DASHBOARD")
    print("=" * 80)

    # 1. Verify Model Artifacts
    models_dir = os.path.join(ROOT_DIR, "saved_models")
    required_files = [
        "valuation_pipeline.joblib",
        "valuation_champion_model.joblib",
        "valuation_quantile_engine.joblib",
        "valuation_shap_explainer.joblib",
        "leads_pipeline.joblib",
        "leads_champion_model.joblib",
        "leads_shap_explainer.joblib",
        "models_metadata.json"
    ]

    print("\n[STEP 1] Verifying Saved Model Artifacts in saved_models/:")
    for f in required_files:
        fpath = os.path.join(models_dir, f)
        if os.path.exists(fpath):
            size_kb = os.path.getsize(fpath) / 1024.0
            print(f"  ✓ {f} ({size_kb:.1f} KB)")
        else:
            print(f"  ✗ MISSING: {f}")
            sys.exit(1)

    # 2. Run FastAPI Tests
    print("\n[STEP 2] Running FastAPI Endpoint Test Suite (test_serving_api.py)...")
    res_api = subprocess.run([sys.executable, "test_serving_api.py"], cwd=ROOT_DIR)
    if res_api.returncode != 0:
        print("  ✗ FastAPI test suite failed!")
        sys.exit(1)
    print("  ✓ All FastAPI endpoints validated successfully!")

    # 3. Run AI Assistant Tests
    print("\n[STEP 3] Running LangGraph AI Assistant Test Suite (test_ai_assistant.py)...")
    res_ai = subprocess.run([sys.executable, "-u", "test_ai_assistant.py"], cwd=ROOT_DIR)
    if res_ai.returncode != 0:
        print("  ✗ AI Assistant test suite failed!")
        sys.exit(1)
    print("  ✓ All LangGraph tools and UrduLish agent validated successfully!")

    print("\n" + "=" * 80)
    print(" ALL DAY 4 COMPONENTS VERIFIED AND OPERATIONAL!")
    print("=" * 80)
    print("\nTo launch the FastAPI server:")
    print("  .\\.venv\\Scripts\\uvicorn serving_api:app --host 127.0.0.1 --port 8000 --reload")
    print("\nTo launch the Streamlit dashboard:")
    print("  .\\.venv\\Scripts\\streamlit run dashboard.py")
    print("=" * 80)

if __name__ == "__main__":
    main()
