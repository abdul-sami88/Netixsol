"""
test_ai_assistant.py
====================
Test suite for Day 4 - Task 2: LangGraph AI Assistant & Tools.
Tests:
1. price_predictor tool (returns valid range and PKR formatting)
2. lead_scorer tool (returns probability and Hot/Warm/Cold tier)
3. model_explainer tool (returns SHAP feature breakdown)
4. comparable_properties tool (returns real comps from dataset)
5. market_stats tool (returns price per marla and metrics)
6. chat_with_assistant end-to-end invocation with strict grounding
"""

import os
import sys
import json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from ai_assistant import (
    price_predictor,
    lead_scorer,
    model_explainer,
    comparable_properties,
    market_stats,
    chat_with_assistant
)


def test_tool_price_predictor():
    print("\n--- TEST 1: Price Predictor Tool ---")
    raw = price_predictor.invoke({
        "city": "Lahore",
        "location": "DHA Phase 6",
        "plot_size_marla": 20.0,
        "age_years": 5.0,
        "is_corner": 1
    })
    data = json.loads(raw)
    assert data["status"] == "success"
    assert "crore" in data["fair_valuation_formatted"].lower() or "lakh" in data["fair_valuation_formatted"].lower()
    assert "range_low_formatted" in data
    assert "range_high_formatted" in data
    print(f"Fair Valuation: {data['fair_valuation_formatted']} (Range: {data['range_low_formatted']} to {data['range_high_formatted']})")
    print("[PASSED] price_predictor tool test")


def test_tool_lead_scorer():
    print("\n--- TEST 2: Lead Scorer Tool ---")
    raw = lead_scorer.invoke({
        "budget_pkr": 50000000.0,
        "preferred_city": "Islamabad",
        "num_calls": 5,
        "visit_booked": "Yes",
        "visit_completed": "Yes"
    })
    data = json.loads(raw)
    assert data["status"] == "success"
    assert data["priority_tier"] in ["🔥 Hot", "🌤 Warm", "❄️ Cold"]
    assert 0 <= data["conversion_probability_pct"] <= 100
    print(f"Lead Tier: {data['priority_tier']} ({data['conversion_probability_pct']}%)")
    print(f"Recommended Action: {data['recommended_action']}")
    print("[PASSED] lead_scorer tool test")


def test_tool_model_explainer():
    print("\n--- TEST 3: Model Explainer Tool ---")
    raw = model_explainer.invoke({
        "target_type": "property",
        "city": "Lahore",
        "location_or_source": "DHA Phase 6",
        "plot_size_marla_or_budget": 20.0
    })
    data = json.loads(raw)
    assert data["status"] == "success"
    assert len(data["key_drivers"]) > 0
    print("Key Drivers:", data["key_drivers"])
    print("[PASSED] model_explainer tool test")


def test_tool_comparable_properties():
    print("\n--- TEST 4: Comparable Properties Tool ---")
    raw = comparable_properties.invoke({
        "city": "Lahore",
        "location": "DHA",
        "plot_size_marla": 20.0,
        "max_results": 3
    })
    data = json.loads(raw)
    assert data["status"] == "success"
    assert len(data["comparable_listings"]) > 0
    print(f"Found {len(data['comparable_listings'])} comps in {data['city']}.")
    for c in data["comparable_listings"]:
        print(f" - {c['plot_size_marla']} Marla in {c['location']}: {c['asking_price_formatted']} ({c['price_per_marla_formatted']}/Marla)")
    print("[PASSED] comparable_properties tool test")


def test_tool_market_stats():
    print("\n--- TEST 5: Market Stats Tool ---")
    raw = market_stats.invoke({
        "city": "Lahore",
        "location": "DHA"
    })
    data = json.loads(raw)
    assert data["status"] == "success"
    assert data["total_listings"] > 0
    print(f"Market Stats for {data['area']}:")
    print(f" - Avg Price/Marla: {data['avg_price_per_marla_formatted']}")
    print(f" - Median Price: {data['median_property_price_formatted']}")
    print(f" - Total Inventory: {data['total_listings']}")
    print("[PASSED] market_stats tool test")


def test_chat_with_assistant():
    print("\n--- TEST 6: LangGraph AI Assistant End-to-End Chat ---")
    user_query = "DHA Phase 6 mein 1 kanal, 5 saal purana ghar, kitne ka jana chahiye?"
    print(f"User Query: '{user_query}'")
    
    result = chat_with_assistant(user_query)
    reply = result["reply"]
    print(f"\nAssistant Response:\n{reply}")

    # Verify that the reply is non-empty and contains price/crore/marla
    assert len(reply) > 20
    assert any(w in reply.lower() for w in ["crore", "lakh", "pkr", "model", "value", "qeemat"])
    print("[PASSED] LangGraph AI Assistant end-to-end chat test")


if __name__ == "__main__":
    print("=" * 70)
    print(" RUNNING LANGGRAPH AI ASSISTANT SUITE (DAY 4 - TASK 2)")
    print("=" * 70)
    test_tool_price_predictor()
    test_tool_lead_scorer()
    test_tool_model_explainer()
    test_tool_comparable_properties()
    test_tool_market_stats()
    test_chat_with_assistant()
    print("\n" + "=" * 70)
    print(" ALL TASK 2 LANGGRAPH ASSISTANT TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)
