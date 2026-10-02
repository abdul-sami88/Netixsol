"""
test_day5_capstone.py
=====================
Capstone Automated Verification Suite:
1. Drift Monitoring & Alert Threshold Evaluation
2. Retraining Pipeline, Champion-vs-Challenger Holdout Benchmark & Rollback
3. Production Database Inference Auditing
4. Enhanced Health Check and MLOps API Endpoints
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to path
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

from serving_api import app, ModelArtifacts
import database as db
from drift_monitoring import ModelDriftMonitor, calculate_psi, calculate_ks_test
from retraining_pipeline import ModelVersionManager

client = TestClient(app)


def test_enhanced_health_check():
    """Verify health check includes database status, model version, and drift monitoring."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True
    assert "active_model_version" in data
    assert "latest_drift_status" in data


def test_statistical_psi_and_ks_utilities():
    """Verify PSI and KS drift calculation mathematics."""
    import numpy as np
    np.random.seed(42)
    base = np.random.normal(100, 15, 1000)
    # Similar distribution -> low PSI
    prod_stable = np.random.normal(100, 15, 1000)
    psi_stable, _ = calculate_psi(base, prod_stable)
    assert psi_stable < 0.10, f"Expected stable PSI < 0.10, got {psi_stable}"

    # Shifted distribution (+25%) -> high PSI
    prod_drifted = np.random.normal(135, 15, 1000)
    psi_drifted, _ = calculate_psi(base, prod_drifted)
    assert psi_drifted > 0.25, f"Expected drifted PSI > 0.25, got {psi_drifted}"

    # KS test
    ks_stat, ks_pval = calculate_ks_test(base, prod_drifted)
    assert ks_pval < 0.01, f"Expected significant KS p-value < 0.01, got {ks_pval}"


def test_inference_auditing_to_database():
    """Verify inference calls are logged in SQLite database."""
    prop_payload = {
        "plot_size_marla": 10.0,
        "covered_area_sqft": 2400.0,
        "bedrooms": 3,
        "bathrooms": 4,
        "age_years": 2.0,
        "city": "Lahore",
        "location": "DHA Phase 5",
        "property_type": "House"
    }
    resp = client.post("/predict/price", json=prop_payload)
    assert resp.status_code == 200

    # Check audit log endpoint
    audit_resp = client.get("/audit/inferences?limit=10")
    assert audit_resp.status_code == 200
    records = audit_resp.json()
    assert len(records) > 0
    latest = records[0]
    assert latest["endpoint"] in ["/predict/price", "/predict/lead-score"]
    assert "inputs" in latest
    assert "latency_ms" in latest


def test_drift_status_endpoint():
    """Verify GET /monitoring/drift returns valid report structure."""
    response = client.get("/monitoring/drift")
    assert response.status_code == 200
    data = response.json()
    assert "overall_status" in data or "status" in data


def test_rollback_engine_safety():
    """Verify snapshot creation and rollback restoration logic."""
    # Ensure rollback directory exists and executes without crashing
    snapshot_path = ModelVersionManager.create_snapshot(tag="ci_test")
    assert os.path.exists(snapshot_path)
    
    # Test execute rollback
    success = ModelVersionManager.execute_rollback()
    assert success is True
