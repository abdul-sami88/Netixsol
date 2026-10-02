import math
import numpy as np
from typing import List, Dict, Any, Optional
from database import query_properties_sql, query_candidate_properties_soft, get_agent_by_city
from memory import ConversationMemory
from rag_engine import RAGEngine
from embedding_service import embedding_service
from dialogue_memory import dialogue_memory

def format_pkr_amount(amount: Optional[float]) -> str:
    """Formats raw PKR numbers into natural Pakistani spoken denominations (Lakh / Crore)."""
    if not amount or amount <= 0:
        return "0 PKR"
    if amount >= 10000000: # >= 1 Crore (10 Million)
        val = amount / 10000000
        return f"{val:.2f}".rstrip('0').rstrip('.') + " Crore PKR"
    elif amount >= 100000: # >= 1 Lakh (100 Thousand)
        val = amount / 100000
        return f"{val:.2f}".rstrip('0').rstrip('.') + " Lakh PKR"
    elif amount >= 1000: # >= 1 Thousand
        k = amount / 1000
        return f"{k:.1f}".rstrip('0').rstrip('.') + " Thousand PKR"
    return f"{int(amount):,} PKR"

class RecommendationEngine:
    def __init__(self, rag_engine: Optional[RAGEngine] = None):
        self.rag = rag_engine or RAGEngine()

    def rank_properties_ml(
        self,
        candidates: List[Dict[str, Any]],
        memory: ConversationMemory,
        user_query: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Phase 3: Multi-factor ML candidate ranking & soft matching.
        Evaluates:
        1. Gaussian budget fit curve (with installment flexibility bonus)
        2. Semantic similarity between property description/amenities and caller query
        3. Area and sector proximity match
        4. Property type and bedroom compatibility
        """
        if not candidates:
            return []

        user_vec = embedding_service.get_embedding(user_query)
        scored_candidates = []

        for p in candidates:
            # 1. Budget Affordability (Gaussian fit curve)
            s_budget = 0.80
            if memory.budget_pkr and memory.budget_pkr > 0:
                price = float(p.get("price_pkr", 0.0))
                ratio = price / memory.budget_pkr

                if ratio >= 1.0:
                    # Over budget: Gaussian decay with sigma=0.22
                    s_budget = math.exp(-((ratio - 1.0) ** 2) / (2 * (0.22 ** 2)))
                    # Installment ease bonus: if over budget but offers flexible installment plan
                    if p.get("payment_plan"):
                        s_budget = min(1.0, s_budget + 0.18)
                else:
                    # Under budget: gentler decay (under budget is acceptable)
                    s_budget = math.exp(-((ratio - 1.0) ** 2) / (2 * (0.40 ** 2)))

            # 2. Semantic Match (Cosine similarity)
            amenities_list = p.get("amenities", [])
            amenities_text = ", ".join(amenities_list) if isinstance(amenities_list, list) else str(amenities_list)
            prop_text = f"{p.get('title', '')} in {p.get('area', '')} {p.get('city', '')}. {p.get('description', '')}. Amenities: {amenities_text}."
            
            prop_vec = embedding_service.get_embedding(prop_text)
            s_semantic = embedding_service.cosine_similarity(user_vec, prop_vec)

            # 3. Location / Sector Proximity
            s_loc = 0.70
            if memory.area and p.get("area"):
                if memory.area.lower() in p["area"].lower() or p["area"].lower() in memory.area.lower():
                    s_loc = 1.00
                elif memory.city and p.get("city") and memory.city.lower() in p["city"].lower():
                    s_loc = 0.65
                else:
                    s_loc = 0.30
            elif memory.city and p.get("city") and memory.city.lower() in p["city"].lower():
                s_loc = 0.85

            # 4. Property Type & Bedroom Compatibility
            s_type = 0.80
            if memory.property_type and p.get("property_type"):
                if memory.property_type.lower() == p["property_type"].lower():
                    s_type = 1.00
                else:
                    s_type = 0.40

            if memory.bedrooms and p.get("bedrooms"):
                diff = abs(p["bedrooms"] - memory.bedrooms)
                s_bed = max(0.40, 1.0 - 0.20 * diff)
                s_type = (s_type + s_bed) / 2.0

            # Composite ML Score
            composite_score = (
                0.35 * s_budget +
                0.35 * s_semantic +
                0.20 * s_loc +
                0.10 * s_type
            )
            composite_score = round(min(1.0, max(0.0, composite_score)), 3)

            p_copy = dict(p)
            p_copy["ml_score"] = composite_score
            p_copy["ml_breakdown"] = {
                "budget_fit": round(s_budget, 2),
                "semantic_match": round(s_semantic, 2),
                "location_fit": round(s_loc, 2)
            }
            scored_candidates.append(p_copy)

        # Rank descending by composite score
        scored_candidates.sort(key=lambda x: x["ml_score"], reverse=True)
        return scored_candidates[:limit]

    def get_recommendations(
        self,
        memory: ConversationMemory,
        user_query: str
    ) -> Dict[str, Any]:
        """
        Unified ML Recommender:
        - Phase 2: Dynamic Few-Shot In-Context Learning retrieval
        - Phase 3: Soft SQL candidate retrieval with multi-factor ML scoring
        - Combines Structured Properties + Relationship Manager + RAG Knowledge
        """
        # 0. Out-of-Coverage City Edge Case Handling
        if memory.unsupported_city:
            rag_context = self.rag.get_context_str(user_query, top_k=2)
            assigned_agent = get_agent_by_city("Lahore")
            
            combined_context = (
                f"=== OUT-OF-COVERAGE CITY REQUESTED: {memory.unsupported_city} ===\n"
                f"AVAILABLE CITIES COVERED IN DATABASE: Lahore, Islamabad, Karachi.\n"
                f"MANDATORY INSTRUCTION: Instruct the client politely: 'Acha... filhal mere paas sirf Lahore, Islamabad, aur Karachi ka data available hai. Mujhay batayein agar aap ko in cities ke baaray mein information chahiye?'\n\n"
                f"--- ASSIGNED HEAD OFFICE RELATIONSHIP MANAGER ---\n"
                f"Name: {assigned_agent['name']} | Phone: {assigned_agent['phone']}\n\n"
                f"--- BROCHURE KNOWLEDGE BASE ---\n"
                f"{rag_context}"
            )
            return {
                "properties": [],
                "agent": assigned_agent,
                "formatted_context": combined_context,
                "few_shot_exemplar": None,
                "unsupported_city": memory.unsupported_city
            }

        # 1. Phase 2: Dynamic Few-Shot Guidance Retrieval
        few_shot_exemplar = dialogue_memory.retrieve_exemplar(user_query)
        few_shot_banner = few_shot_exemplar["banner"] if few_shot_exemplar else ""

        # 2. Check if City is specified
        city_banner = ""
        if not memory.city:
            city_banner = (
                "=== NO CITY SPECIFIED YET ===\n"
                "MANDATORY INSTRUCTION: The client has NOT specified their desired city yet. DO NOT ASSUME LAHORE or any specific city! Greet the client warmly and ask: 'Assalam-o-Alaikum sir! RealEstate Hub se Zara baat kar rahi hoon. Main aap ki kis tarah madad kar sakti hoon? Aap kaun se city (Lahore, Islamabad, ya Karachi) aur budget mein property dekh rahe hain?'\n\n"
            )

        # 3. Purpose Unspecified Prompt Banner
        purpose_banner = ""
        if memory.city and not memory.purpose:
            purpose_banner = (
                "=== PURPOSE NOT SPECIFIED (BUY VS RENT) ===\n"
                "MANDATORY INSTRUCTION: Ask the client politely whether they want to BUY or RENT the property. Do NOT say both languages (do NOT say 'khareedna (Buy)' or 'rent (Kiraya)').\n"
                "Example: 'Acha... kya aap property buy karna chahte hain ya rent par lena chahte hain sir?'\n\n"
            )

        # 4. Phase 3: Soft SQL Query Execution & ML Ranking
        target_purpose = memory.purpose or "Sale"
        ranked_properties = []

        if memory.city or memory.budget_pkr or memory.property_type or memory.area:
            # Query candidate pool with +/- 20% budget tolerance and payment plan joins
            candidates = query_candidate_properties_soft(
                city=memory.city,
                area=memory.area,
                budget_pkr=memory.budget_pkr,
                bedrooms=memory.bedrooms,
                purpose=target_purpose if memory.purpose else None,
                property_type=memory.property_type,
                budget_tolerance=0.20,
                limit=15
            )

            if candidates:
                ranked_properties = self.rank_properties_ml(
                    candidates=candidates,
                    memory=memory,
                    user_query=user_query,
                    limit=3
                )
            else:
                # Fallback to standard query if relaxed soft query returned empty
                fallback_results = query_properties_sql(
                    city=memory.city,
                    area=memory.area,
                    max_price_pkr=memory.budget_pkr,
                    bedrooms=memory.bedrooms,
                    purpose=target_purpose if memory.purpose else None,
                    property_type=memory.property_type,
                    limit=3
                )
                ranked_properties = fallback_results

        # Update session memory with latest ranked properties
        memory.last_recommended_properties = ranked_properties

        # 5. RAG Semantic Retrieval
        rag_context = self.rag.get_context_str(user_query, top_k=2)

        # 6. Format properties string with payment plan & ML highlights for LLM
        props_formatted = []
        for idx, p in enumerate(ranked_properties, 1):
            amenities_str = ", ".join(p['amenities']) if isinstance(p.get('amenities'), list) else p.get('amenities', '')
            
            plan_str = "Standard Cash Settlement"
            if p.get("payment_plan"):
                plan = p["payment_plan"]
                dp_val = plan.get('down_payment_pkr')
                mo_val = plan.get('monthly_installment_pkr')
                dur_val = plan.get('duration_months', 36)
                
                dp_str = f"25% Down Payment = {format_pkr_amount(dp_val)}" if dp_val else "25% Down Payment"
                mo_str = f"{format_pkr_amount(mo_val)}/month" if mo_val else "Flexible"
                dur_str = f"{dur_val} months"
                plan_str = f"Flexible Installment Available ({dp_str}, Monthly Installment: {mo_str}, Duration: {dur_str})"

            score_str = f" [ML Match Score: {p.get('ml_score', 0.85)*100:.0f}%]" if p.get('ml_score') is not None else ""

            props_formatted.append(
                f"Option {idx}: {p['title']}{score_str}\n"
                f"  - Price: {p['price_formatted']} ({p['price_pkr']:,} PKR)\n"
                f"  - Location: {p['area']}, {p['city']}\n"
                f"  - Details: {p['size_val']} {p['size_unit']} | {p.get('bedrooms', 0)} Beds | {p.get('bathrooms', 0)} Baths\n"
                f"  - Payment Terms: {plan_str}\n"
                f"  - Purpose: For {p['purpose']}\n"
                f"  - Amenities: {amenities_str}\n"
            )

        properties_str = "\n".join(props_formatted) if props_formatted else "No specific property filters applied yet."

        # Agent Contact
        assigned_agent = get_agent_by_city(memory.city or "Lahore")

        # Assemble unified prompt context
        context_parts = []
        if few_shot_banner:
            context_parts.append(few_shot_banner)
        if city_banner:
            context_parts.append(city_banner)
        if purpose_banner:
            context_parts.append(purpose_banner)

        context_parts.append(
            f"--- TOP ML-RANKED PROPERTY MATCHES ---\n"
            f"{properties_str}\n\n"
            f"--- ASSIGNED CITY RELATIONSHIP MANAGER ---\n"
            f"Name: {assigned_agent['name']} | Phone: {assigned_agent['phone']} | Rating: {assigned_agent['rating']}/5.0\n\n"
            f"--- SEMANTIC BROCHURE & NOC KNOWLEDGE BASE ---\n"
            f"{rag_context}"
        )

        combined_context = "\n".join(context_parts)

        return {
            "properties": ranked_properties,
            "agent": assigned_agent,
            "formatted_context": combined_context,
            "few_shot_exemplar": few_shot_exemplar,
            "unsupported_city": None
        }

if __name__ == "__main__":
    from memory import get_session_memory
    mem = get_session_memory("test_ml_recommendation")
    mem.city = "Lahore"
    mem.budget_pkr = 38000000.0  # 3.8 Crore
    mem.area = "DHA"
    mem.purpose = "Sale"
    
    engine = RecommendationEngine()
    res = engine.get_recommendations(mem, "Main DHA Lahore mein 4 crore tak ka ghar dekh raha hoon, installment plan flexible hona chahiye.")
    print("Formatted Context output preview:")
    print(res["formatted_context"])
