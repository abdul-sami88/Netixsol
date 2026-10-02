"""
test_serving_api.py
===================
Comprehensive test suite for FastAPI model serving endpoints (Task 1).
Validates:
1. Health and model info endpoints
2. Price prediction endpoint with range and verdict
3. Lead scoring endpoint with Hot/Warm/Cold tier
4. Pydantic validation: rejection of negative size, negative budget, and unknown cities
5. SHAP explainability endpoints for property and lead
6. Batch CSV prediction endpoint
"""

import os
import sys
import io
import json
from fastapi.testclient import TestClient

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from serving_api import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "models_loaded" in data


def test_model_info():
    response = client.get("/model/info")
    assert response.status_code == 200
    data = response.json()
    assert "property_valuation" in data
    assert "lead_scoring" in data
    assert data["property_valuation"]["metrics"]["MAE_PKR"] > 0
    assert data["lead_scoring"]["metrics"]["ROC_AUC"] > 0.80


def test_predict_price_valid():
    payload = {
        "plot_size_marla": 20.0,
        "covered_area_sqft": 4500.0,
        "bedrooms": 5,
        "bathrooms": 6,
        "age_years": 3.0,
        "city": "Lahore",
        "location": "DHA Phase 6",
        "property_type": "House",
        "is_corner": 1,
        "is_park_facing": 0,
        "is_main_boulevard": 1,
        "listed_price_pkr": 80000000.0
    }
    response = client.post("/predict/price", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "fair_market_price_pkr" in data
    assert "confidence_interval_80" in data
    assert "investment_verdict" in data
    assert data["fair_market_price_pkr"] > 10_000_000
    print("\n[PASSED] Price Prediction:", data["fair_market_price_formatted"])


def test_predict_price_validation_negative_size():
    payload = {
        "plot_size_marla": -5.0,  # Invalid
        "covered_area_sqft": 4500.0,
        "bedrooms": 5,
        "bathrooms": 6,
        "age_years": 3.0,
        "city": "Lahore",
        "location": "DHA Phase 6"
    }
    response = client.post("/predict/price", json=payload)
    assert response.status_code == 422  # Pydantic validation error
    err = response.json()
    assert "greater than 0" in str(err)
    print("\n[PASSED] Rejected negative plot size with 422 Unprocessable Entity")


def test_predict_price_validation_unknown_city():
    payload = {
        "plot_size_marla": 10.0,
        "covered_area_sqft": 2200.0,
        "bedrooms": 3,
        "bathrooms": 4,
        "age_years": 2.0,
        "city": "London",  # Unknown city
        "location": "Mayfair"
    }
    response = client.post("/predict/price", json=payload)
    assert response.status_code == 422
    err = response.json()
    assert "Unknown city" in str(err)
    print("\n[PASSED] Rejected unknown city with 422 Unprocessable Entity")


def test_predict_lead_score_valid():
    payload = {
        "budget_pkr": 50000000.0,
        "num_calls": 5,
        "avg_call_duration_mins": 9.0,
        "response_time_hours": 1.0,
        "days_since_first_contact": 10.0,
        "followup_count": 4,
        "lead_source": "Zameen.com",
        "preferred_city": "Islamabad",
        "purpose": "Buy",
        "property_type_preferred": "House",
        "visit_booked": "Yes",
        "visit_completed": "Yes"
    }
    response = client.post("/predict/lead-score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "conversion_probability_pct" in data
    assert "priority_tier" in data
    assert "recommended_sales_action" in data
    print("\n[PASSED] Lead Scoring Result:", data["priority_tier"], f"({data['conversion_probability_pct']}%)")


def test_predict_lead_validation_negative_budget():
    payload = {
        "budget_pkr": -100000.0,  # Invalid
        "num_calls": 3,
        "avg_call_duration_mins": 5.0,
        "response_time_hours": 2.0,
        "days_since_first_contact": 5.0,
        "followup_count": 2,
        "lead_source": "Facebook Ads",
        "preferred_city": "Karachi"
    }
    response = client.post("/predict/lead-score", json=payload)
    assert response.status_code == 422
    print("\n[PASSED] Rejected negative budget with 422 Unprocessable Entity")


def test_explain_price():
    payload = {
        "plot_size_marla": 10.0,
        "covered_area_sqft": 2500.0,
        "bedrooms": 4,
        "bathrooms": 4,
        "age_years": 1.0,
        "city": "Islamabad",
        "location": "Bahria Town",
        "property_type": "House"
    }
    response = client.post("/explain/price", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "top_positive_value_drivers" in data
    assert len(data["top_positive_value_drivers"]) > 0
    print("\n[PASSED] Price SHAP Explanation generated successfully")


def test_explain_lead():
    payload = {
        "budget_pkr": 60000000.0,
        "num_calls": 6,
        "avg_call_duration_mins": 10.0,
        "response_time_hours": 0.5,
        "days_since_first_contact": 7.0,
        "followup_count": 5,
        "lead_source": "Referral",
        "preferred_city": "Lahore",
        "purpose": "Buy",
        "property_type_preferred": "House",
        "visit_booked": "Yes",
        "visit_completed": "Yes"
    }
    response = client.post("/explain/lead", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "urdulish_narrative" in data
    assert "lead_tier" in data
    print("\n[PASSED] Lead UrduLish Explanation:\n", data["urdulish_narrative"])


def test_predict_batch_csv():
    # Construct a sample CSV in memory
    csv_content = (
        "plot_size_marla,covered_area_sqft,bedrooms,bathrooms,age_years,city,location,property_type,listed_price_pkr\n"
        "10.0,2400.0,3,4,2.0,Lahore,DHA Phase 5,House,38000000.0\n"
        "20.0,4600.0,5,6,4.0,Karachi,Clifton,House,95000000.0\n"
    )
    files = {"file": ("test_properties.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/predict/batch?batch_type=property", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["total_records_processed"] == 2
    assert data["successful_records"] == 2
    print("\n[PASSED] Batch CSV Processing passed for 2 records")


if __name__ == "__main__":
    test_health()
    test_model_info()
    test_predict_price_valid()
    test_predict_price_validation_negative_size()
    test_predict_price_validation_unknown_city()
    test_predict_lead_score_valid()
    test_predict_lead_validation_negative_budget()
    test_explain_price()
    test_explain_lead()
    test_predict_batch_csv()
    print("\n" + "="*70)
    print(" ALL TASK 1 FASTAPI ENDPOINT TESTS PASSED WITH 100% SUCCESS!")
    print("="*70)
