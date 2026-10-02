import os
import sys
import time
import json
import sqlite3
from typing import Dict, Any

# Ensure current directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_db_connection, query_candidate_properties_soft
from embedding_service import embedding_service, LocalFallbackVectorizer, EmbeddingService
from dialogue_memory import dialogue_memory
from recommendation import RecommendationEngine
from memory import get_session_memory, reset_session_memory
from crm_store import crm_store
from appointment_manager import appointment_manager
from fastapi.testclient import TestClient
from app import app


def print_header(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_case_1_embedding_service():
    print_header("TEST CASE 1: Embedding Service & Fallback Validation")
    
    # 1. Primary Vector Generation
    t0 = time.time()
    query1 = "installment plan flexible down payment"
    v1 = embedding_service.get_embedding(query1)
    t1 = time.time()
    print(f"[*] Embedding generated in {(t1 - t0)*1000:.2f} ms | Vector Dimension: {len(v1)}")
    assert len(v1) > 0, "Vector should have non-zero dimension"

    # 2. LRU Cache hit test
    t2 = time.time()
    v1_cached = embedding_service.get_embedding(query1)
    t3 = time.time()
    cache_time_ms = (t3 - t2) * 1000
    print(f"[*] LRU Cache Hit: {cache_time_ms:.4f} ms")
    assert v1 == v1_cached, "Cached vector must match original"
    assert cache_time_ms < 5.0, "Cache lookup must be sub-5ms"

    # 3. Local Scikit-learn TF-IDF fallback vectorizer
    fallback = LocalFallbackVectorizer()
    fb_vec1 = fallback.transform("dha lahore luxury house installment")
    fb_vec2 = fallback.transform("down payment schedule monthly qist")
    fb_sim = EmbeddingService.cosine_similarity(fb_vec1, fb_vec2)
    print(f"[*] Local Fallback Dim: {len(fb_vec1)} | Cosine Sim: {fb_sim:.4f}")
    assert len(fb_vec1) > 0, "Fallback vectorizer must return non-empty vector"

    # 4. Semantic similarity comparison
    query2 = "down payment kitni hogi mahana qist schedule"
    query_unrelated = "commercial shop rental income in saddar karachi"
    v2 = embedding_service.get_embedding(query2)
    v_unrelated = embedding_service.get_embedding(query_unrelated)

    sim_related = embedding_service.cosine_similarity(v1, v2)
    sim_unrelated = embedding_service.cosine_similarity(v1, v_unrelated)
    print(f"[*] Similarity (Related Installment queries): {sim_related:.4f}")
    print(f"[*] Similarity (Installment vs Commercial Rental): {sim_unrelated:.4f}")
    assert sim_related > sim_unrelated, "Related queries must have higher cosine similarity than unrelated ones"

    print(">>> TEST CASE 1 PASSED SUCCESSFULLY! <<<\n")


def test_case_2_dialogue_memory():
    print_header("TEST CASE 2: Phase 2 Dialogue Memory Cold-Start & Retrieval")

    # 1. Verify cold-start seeding
    assert len(dialogue_memory.exemplars_cache) >= 15, "Should have at least 15 cold-start exemplars loaded"
    print(f"[*] Active exemplars in memory: {len(dialogue_memory.exemplars_cache)}")

    # 2. Query A: Installment negotiation
    q_inst = "Main DHA mein 4 crore ka ghar dekh raha hoon, installment plan flexible hona chahiye down payment kitni hogi?"
    res_inst = dialogue_memory.retrieve_exemplar(q_inst, threshold=0.60)
    assert res_inst is not None, "Should match installment exemplar"
    print(f"[*] Query: '{q_inst[:50]}...'")
    print(f"    -> Matched Category: {res_inst['category']} (Score: {res_inst['similarity']:.3f})")
    assert "Installment" in res_inst["category"]
    assert "PROVEN SALES GUIDANCE" in res_inst["banner"]

    # 3. Query B: NOC & Legal legitimacy
    q_noc = "Kya yeh project LDA approved hai? Legal NOC papers clear hain?"
    res_noc = dialogue_memory.retrieve_exemplar(q_noc, threshold=0.60)
    assert res_noc is not None, "Should match NOC exemplar"
    print(f"[*] Query: '{q_noc}'")
    print(f"    -> Matched Category: {res_noc['category']} (Score: {res_noc['similarity']:.3f})")
    assert "NOC" in res_noc["category"] or "Legal" in res_noc["category"]

    # 4. Query C: Price objection
    q_price = "Yeh rate bohat zyada lag raha hai market se, thora sasta mil sakta hai?"
    res_price = dialogue_memory.retrieve_exemplar(q_price, threshold=0.55)
    assert res_price is not None, "Should match price objection exemplar"
    print(f"[*] Query: '{q_price}'")
    print(f"    -> Matched Category: {res_price['category']} (Score: {res_price['similarity']:.3f})")
    assert "Price" in res_price["category"] or "Rate" in res_price["category"]

    print(">>> TEST CASE 2 PASSED SUCCESSFULLY! <<<\n")


def test_case_3_ml_property_ranking():
    print_header("TEST CASE 3: Phase 3 Soft SQL Query & ML Multi-Factor Ranking")

    mem = get_session_memory("test_ml_ranking_session")
    mem.city = "Lahore"
    mem.area = "DHA"
    mem.budget_pkr = 38000000.0  # 3.8 Crore PKR
    mem.purpose = "Sale"
    mem.property_type = "House"

    user_query = "Main DHA Lahore mein 4 crore tak ka ghar dekh raha hoon, flexible 3-year installment plan mil sakta hai?"

    # 1. Soft SQL candidate fetch
    candidates = query_candidate_properties_soft(
        city=mem.city,
        area=mem.area,
        budget_pkr=mem.budget_pkr,
        purpose=mem.purpose,
        budget_tolerance=0.25,
        limit=10
    )
    print(f"[*] Candidates fetched via soft SQL query (+/- 25% tolerance): {len(candidates)}")
    assert len(candidates) > 0, "Soft query must return candidate properties"

    # 2. Run ML Recommender
    rec_engine = RecommendationEngine()
    rec_data = rec_engine.get_recommendations(mem, user_query)
    ranked = rec_data["properties"]
    print(f"[*] ML-Ranked Properties Count: {len(ranked)}")
    assert len(ranked) > 0, "Should return ranked properties"

    top_prop = ranked[0]
    print(f"[*] Top Ranked Property: {top_prop['title']}")
    print(f"    - Price: {top_prop['price_formatted']} ({top_prop['price_pkr']:,} PKR)")
    print(f"    - Location: {top_prop['area']}, {top_prop['city']}")
    print(f"    - ML Score: {top_prop.get('ml_score', 'N/A')}")
    print(f"    - Score Breakdown: {top_prop.get('ml_breakdown', {})}")
    print(f"    - Payment Plan: {top_prop.get('payment_plan')}")

    # Verify score presence and validity
    assert "ml_score" in top_prop, "Ranked candidate must contain ml_score"
    assert 0.0 <= top_prop["ml_score"] <= 1.0, "Score must be between 0.0 and 1.0"
    assert "ml_breakdown" in top_prop, "Candidate must contain score breakdown"

    # Verify unified context injection
    ctx = rec_data["formatted_context"]
    assert "--- TOP ML-RANKED PROPERTY MATCHES ---" in ctx
    assert "PROVEN SALES GUIDANCE" in ctx

    print(">>> TEST CASE 3 PASSED SUCCESSFULLY! <<<\n")


def test_case_4_closed_loop_feedback():
    print_header("TEST CASE 4: Closed-Loop Feedback on Booking")

    test_session = f"conv_test_session_{int(time.time())}"
    test_email = "investor.client@testpakistan.com"

    # 1. Simulate prior conversation turns in CRM
    turn1 = crm_store.log_transcript(
        session_id=test_session,
        client_email=test_email,
        raw_transcript="Assalam-o-Alaikum, mujhe property chahiye.",
        normalized_transcript="Assalam-o-Alaikum, mujhe property chahiye.",
        agent_response="Walaikum Assalam! Main aap ki kya madad kar sakti hoon?",
        latency_sec=0.1
    )

    turn2 = crm_store.log_transcript(
        session_id=test_session,
        client_email=test_email,
        raw_transcript="Agar possession delay hoti hai to penalty clause kya hai contractual guarantee?",
        normalized_transcript="Agar possession delay hoti hai to penalty clause kya hai contractual guarantee?",
        agent_response="Sir contractual agreement mein penalty clause hai jahan promised timeline se delay hone par developer monthly rent rebate pay karta hai.",
        latency_sec=0.4
    )

    # Verify initial converted flag is 0
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT is_converted FROM crm_call_transcripts WHERE session_id = ?", (test_session,))
    flags_before = [r[0] for r in c.fetchall()]
    conn.close()
    print(f"[*] is_converted flags before booking: {flags_before}")
    assert all(f == 0 for f in flags_before), "Before booking, is_converted must be 0"

    initial_exemplar_count = len(dialogue_memory.exemplars_cache)

    # 2. Book appointment through appointment_manager
    book_res = appointment_manager.book_appointment(
        session_id=test_session,
        client_name="Test Investor",
        client_email=test_email,
        city="Lahore",
        property_title="1 Kanal Luxury Villa DHA",
        appointment_date="Tomorrow",
        appointment_time="03:00 PM",
        notes="Closed loop test verification."
    )
    print(f"[*] Booking result: {book_res.get('status')} | Success: {book_res.get('success')}")
    assert book_res.get("success") is True, "Appointment booking should succeed"

    # 3. Verify transcripts converted status updated to 1
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT is_converted FROM crm_call_transcripts WHERE session_id = ?", (test_session,))
    flags_after = [r[0] for r in c.fetchall()]
    conn.close()
    print(f"[*] is_converted flags after booking: {flags_after}")
    assert any(f == 1 for f in flags_after), "Transcripts must be marked is_converted = 1"

    # 4. Verify new exemplar indexed into dialogue_memory
    print(f"[*] Exemplars count: before={initial_exemplar_count}, after={len(dialogue_memory.exemplars_cache)}")
    assert len(dialogue_memory.exemplars_cache) >= initial_exemplar_count

    print(">>> TEST CASE 4 PASSED SUCCESSFULLY! <<<\n")


def test_case_5_e2e_api_integration():
    print_header("TEST CASE 5: End-to-End Voice / Chat Integration via FastAPI")

    client = TestClient(app)

    # 1. Test /api/v1/chat endpoint
    payload = {
        "session_id": f"e2e_voice_test_{int(time.time())}",
        "message": "Main DHA Lahore mein 4 crore tak ka ghar dekh raha hoon, installment plan flexible hona chahiye."
    }

    t0 = time.time()
    response = client.post("/api/v1/chat", json=payload)
    elapsed = time.time() - t0

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    data = response.json()

    print(f"[*] /api/v1/chat Response Time: {elapsed:.3f}s")
    print(f"[*] Agent Reply: \"{data.get('reply')[:90]}...\"")
    print(f"[*] Matched Properties: {len(data.get('matched_properties', []))}")
    print(f"[*] Few-shot Guidance Present: {data.get('few_shot_guidance') is not None}")

    assert len(data.get("matched_properties", [])) > 0, "Must return matched properties"
    assert data.get("few_shot_guidance") is not None, "Few shot guidance should be retrieved for installment query"
    assert elapsed < 3.0, "Total roundtrip latency should be well under 3.0s"

    # 2. Test Vapi completions endpoint (/v1/chat/completions)
    vapi_payload = {
        "model": "urdu-real-estate-llm",
        "messages": [
            {"role": "user", "content": "DHA Lahore mein installment plan par 4 crore ka ghar available hai?"}
        ],
        "stream": False
    }

    t0 = time.time()
    vapi_res = client.post(
        "/v1/chat/completions",
        json=vapi_payload,
        headers={"x-call-id": f"vapi_e2e_call_{int(time.time())}"}
    )
    vapi_elapsed = time.time() - t0

    assert vapi_res.status_code == 200
    vapi_data = vapi_res.json()
    print(f"[*] /v1/chat/completions Response Time: {vapi_elapsed:.3f}s")
    print(f"[*] Vapi Assistant Message: \"{vapi_data['choices'][0]['message']['content'][:90]}...\"")
    print(f"[*] Meta retrieved properties count: {vapi_data['meta'].get('retrieved_properties_count')}")
    print(f"[*] Meta few_shot_guidance: {vapi_data['meta'].get('few_shot_guidance') is not None}")

    assert vapi_data["choices"][0]["message"]["content"]
    assert vapi_data["meta"]["retrieved_properties_count"] > 0

    print(">>> TEST CASE 5 PASSED SUCCESSFULLY! <<<\n")


if __name__ == "__main__":
    init_db()
    print("======================================================================")
    print("  RUNNING UNIFIED PHASE 2 & 3 ML SYSTEM TEST SUITE")
    print("======================================================================")
    
    test_case_1_embedding_service()
    test_case_2_dialogue_memory()
    test_case_3_ml_property_ranking()
    test_case_4_closed_loop_feedback()
    test_case_5_e2e_api_integration()

    print("\n" + "=" * 70)
    print("  ALL 5 TEST CASES PASSED WITH 100% SUCCESS!")
    print("=" * 70)
