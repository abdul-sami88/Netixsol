from typing import List, Dict, Any, Optional
from database import query_properties_sql, get_agent_by_city
from memory import ConversationMemory
from rag_engine import RAGEngine

class RecommendationEngine:
    def __init__(self, rag_engine: Optional[RAGEngine] = None):
        self.rag = rag_engine or RAGEngine()

    def get_recommendations(
        self,
        memory: ConversationMemory,
        user_query: str
    ) -> Dict[str, Any]:
        """
        Combines SQL structured filter with RAG semantic context to generate
        an accurate property recommendation payload.
        Handles unspecified city and buy vs rent clarifications without assuming Lahore.
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
                "unsupported_city": memory.unsupported_city
            }

        # 1. Check if City is specified
        city_banner = ""
        if not memory.city:
            city_banner = (
                "=== NO CITY SPECIFIED YET ===\n"
                "MANDATORY INSTRUCTION: The client has NOT specified their desired city yet. DO NOT ASSUME LAHORE or any specific city! Greet the client warmly and ask: 'Assalam-o-Alaikum sir! RealEstate Hub se Zara baat kar rahi hoon. Main aap ki kis tarah madad kar sakti hoon? Aap kaun se city (Lahore, Islamabad, ya Karachi) aur budget mein property dekh rahe hain?'\n\n"
            )

        # 2. SQL Query execution
        target_purpose = memory.purpose or "Sale"

        sql_results = []
        if memory.city or memory.budget_pkr or memory.property_type or memory.area:
            sql_results = query_properties_sql(
                city=memory.city,
                area=memory.area,
                max_price_pkr=memory.budget_pkr,
                bedrooms=memory.bedrooms,
                purpose=target_purpose if memory.purpose else None,
                property_type=memory.property_type,
                limit=4
            )

        # Sort Sale items first if purpose is unspecified
        if not memory.purpose and sql_results:
            sql_results.sort(key=lambda x: 0 if x["purpose"] == "Sale" else 1)

        memory.last_recommended_properties = sql_results

        # 3. RAG Semantic Retrieval
        rag_context = self.rag.get_context_str(user_query, top_k=2)

        # 4. Purpose Unspecified Prompt Banner
        purpose_banner = ""
        if memory.city and not memory.purpose:
            purpose_banner = (
                "=== PURPOSE NOT SPECIFIED (BUY VS RENT) ===\n"
                "MANDATORY INSTRUCTION: Ask the client politely whether they want to BUY (Khareedna) or RENT (Kiraya) the property!\n"
                "Example: 'Acha... kya aap property khareedna (Buy) chahte hain ya rent (Kiraya) par lena chahte hain sir?'\n\n"
            )

        # 5. Format properties string for LLM injection
        props_formatted = []
        for idx, p in enumerate(sql_results, 1):
            amenities_str = ", ".join(p['amenities']) if isinstance(p.get('amenities'), list) else p.get('amenities', '')
            props_formatted.append(
                f"Option {idx}: {p['title']}\n"
                f"  - Price: {p['price_formatted']} ({p['price_pkr']:,} PKR)\n"
                f"  - Location: {p['area']}, {p['city']}\n"
                f"  - Details: {p['size_val']} {p['size_unit']} | {p['bedrooms']} Beds | {p['bathrooms']} Baths\n"
                f"  - Purpose: For {p['purpose']}\n"
                f"  - Amenities: {amenities_str}\n"
            )

        properties_str = "\n".join(props_formatted) if props_formatted else "No specific property filters applied yet."

        # Agent Contact
        assigned_agent = get_agent_by_city(memory.city or "Lahore")

        combined_context = (
            f"{city_banner}"
            f"{purpose_banner}"
            f"--- STRUCTURED SQL PROPERTY MATCHES ---\n"
            f"{properties_str}\n\n"
            f"--- ASSIGNED CITY RELATIONSHIP MANAGER ---\n"
            f"Name: {assigned_agent['name']} | Phone: {assigned_agent['phone']} | Rating: {assigned_agent['rating']}/5.0\n\n"
            f"--- SEMANTIC BROCHURE & NOC KNOWLEDGE BASE ---\n"
            f"{rag_context}"
        )

        return {
            "properties": sql_results,
            "agent": assigned_agent,
            "formatted_context": combined_context,
            "unsupported_city": None
        }

if __name__ == "__main__":
    from memory import get_session_memory
    mem = get_session_memory("test_session_new_call")
    mem.add_turn("user", "Assalam-o-Alaikum")
    
    engine = RecommendationEngine()
    res = engine.get_recommendations(mem, "Assalam-o-Alaikum")
    print("Formatted Context output preview for fresh call:")
    print(res["formatted_context"])
