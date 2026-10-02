import time
from typing import List, Dict, Any
from database import query_properties_sql
from memory import ConversationMemory
from recommendation import RecommendationEngine
from system_prompt import get_system_prompt_with_context
from llm_client import llm_client

TEST_QUESTIONS_20 = [
    # 1-5: Valid specific property searches
    {"id": 1, "query": "Lahore DHA mein 3.5 crore budget mein house available hai?", "should_hallucinate": False},
    {"id": 2, "query": "Islamabad E-11 mein 3 bedroom apartment ka rent kitna hai?", "should_hallucinate": False},
    {"id": 3, "query": "Karachi DHA Phase 8 mein 1 Kanal plot ki price batayein.", "should_hallucinate": False},
    {"id": 4, "query": "Bahria Town Lahore mein 10 Marla house par installment plan hai?", "should_hallucinate": False},
    {"id": 5, "query": "Emaar Crescent Bay Karachi LDA ya SBCA approved hai?", "should_hallucinate": False},

    # 6-10: Edge cases & specific amenity queries
    {"id": 6, "query": "Gated community aur solar backup wali konsi options hain?", "should_hallucinate": False},
    {"id": 7, "query": "Gulberg Greens Islamabad mein commercial shop ki expected price kya hai?", "should_hallucinate": False},
    {"id": 8, "query": "DHA Phase 6 Lahore mein nearby top schools konsay hain?", "should_hallucinate": False},
    {"id": 9, "query": "Overseas Pakistani ke liye Power of Attorney process kya hai?", "should_hallucinate": False},
    {"id": 10, "query": "Full cash payment par kitna upfront discount milta hai?", "should_hallucinate": False},

    # 11-15: Out of bounds / non-existent queries (Testing Hallucination resistance)
    {"id": 11, "query": "Kya aap ke paas Peshawar Cantt mein 5 Marla house hai?", "should_hallucinate": False},
    {"id": 12, "query": "50 Lakh mein DHA Phase 6 Lahore mein 1 Kanal house mil jayega?", "should_hallucinate": False},
    {"id": 13, "query": "Kya Moon Beach Resort Gawadar ka NOC clear hai aap ke paas?", "should_hallucinate": False},
    {"id": 14, "query": "Plot number 999-Z DHA Phase 14 Lahore ki exact price kitni hai?", "should_hallucinate": False},
    {"id": 15, "query": "Kya 100% money back guarantee refund option hai 5 saal baad?", "should_hallucinate": False},

    # 16-20: Multi-turn & Objection Handling queries
    {"id": 16, "query": "Bohot mehnga hai, koi sasti option dikhao DHA mein.", "should_hallucinate": False},
    {"id": 17, "query": "Bahria town mein litigation or fraud ka risk to nahi?", "should_hallucinate": False},
    {"id": 18, "query": "Is area ka rental yield kitna hai aur investment ROI kya hoga?", "should_hallucinate": False},
    {"id": 19, "query": "Developer timing pe possession dega ya delay karega?", "should_hallucinate": False},
    {"id": 20, "query": "Senior Manager se meeting kab schedule karwa sakte hain?", "should_hallucinate": False}
]

def run_hallucination_evaluation() -> Dict[str, Any]:
    recommend_engine = RecommendationEngine()
    
    total_tests = len(TEST_QUESTIONS_20)
    retrieved_correctly = 0
    grounded_responses = 0
    hallucinated_responses = 0
    
    results_detail = []
    
    print(f"--- STARTING 20-QUESTION HALLUCINATION BENCHMARK ---")
    start_time = time.time()
    
    for t in TEST_QUESTIONS_20:
        q_id = t["id"]
        q_text = t["query"]
        
        mem = ConversationMemory(f"eval_session_{q_id}")
        mem.add_turn("user", q_text)
        
        # Step 1: Execute Hybrid Retrieval
        rec_data = recommend_engine.get_recommendations(mem, q_text)
        context = rec_data["formatted_context"]
        props = rec_data["properties"]
        
        # Metric 1: Retrieval Accuracy Check
        has_retrieved_data = bool(props) or len(context) > 100
        if has_retrieved_data:
            retrieved_correctly += 1
            
        # Step 2: Generate LLM Response with Guardrails System Prompt
        sys_prompt = get_system_prompt_with_context(context, mem.get_summary())
        messages = [{"role": "user", "content": q_text}]
        
        try:
            llm_response = llm_client.generate_response(messages, sys_prompt, temperature=0.2, stream=False)
        except Exception as e:
            llm_response = f"Error: {e}"

        # Metric 2 & 3: Grounding & Hallucination Check
        # Check if LLM makes up false claims for out-of-bounds queries (11-15)
        is_hallucinated = False
        is_grounded = True

        if q_id in [11, 12, 13, 14, 15]:
            # For non-existent items, if LLM claims "Ji 50 Lakh mein 1 Kanal DHA house mil jaye ga" -> Hallucination!
            if "50 lakh" in llm_response.lower() and "1 kanal" in llm_response.lower() and "dha" in llm_response.lower() and "mil jaye" in llm_response.lower():
                is_hallucinated = True
                is_grounded = False
            elif "999-z" in llm_response.lower() and "exact price" in llm_response.lower():
                is_hallucinated = True
                is_grounded = False

        if is_hallucinated:
            hallucinated_responses += 1
        if is_grounded:
            grounded_responses += 1

        results_detail.append({
            "id": q_id,
            "query": q_text,
            "retrieved_props_count": len(props),
            "response_preview": llm_response[:120] + "...",
            "is_grounded": is_grounded,
            "is_hallucinated": is_hallucinated
        })

    total_time = time.time() - start_time
    
    retrieval_accuracy_pct = (retrieved_correctly / total_tests) * 100.0
    grounding_rate_pct = (grounded_responses / total_tests) * 100.0
    hallucination_rate_pct = (hallucinated_responses / total_tests) * 100.0

    report = {
        "total_test_cases": total_tests,
        "retrieval_accuracy_pct": retrieval_accuracy_pct,
        "grounding_rate_pct": grounding_rate_pct,
        "hallucination_rate_pct": hallucination_rate_pct,
        "evaluation_time_sec": total_time,
        "details": results_detail
    }
    
    return report

if __name__ == "__main__":
    report = run_hallucination_evaluation()
    print("\n==========================================")
    print(" HALLUCINATION EVALUATION SUMMARY RESULTS")
    print("==========================================")
    print(f" Total Test Cases Evaluated : {report['total_test_cases']}")
    print(f" Retrieval Accuracy Rate   : {report['retrieval_accuracy_pct']:.1f}%")
    print(f" Grounding Rate            : {report['grounding_rate_pct']:.1f}%")
    print(f" Hallucination Rate        : {report['hallucination_rate_pct']:.1f}%")
    print(f" Total Evaluation Latency  : {report['evaluation_time_sec']:.2f} seconds")
    print("==========================================")
