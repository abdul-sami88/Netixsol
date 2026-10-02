import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from database import get_db_connection, init_db
from embedding_service import embedding_service

# 15 Curated Pakistani Real Estate Cold-Start Winning Dialogues
COLD_START_EXEMPLARS = [
    {
        "category": "Installment Negotiation & Down Payment",
        "user_utterance": "Main DHA Lahore mein 4 crore tak ka ghar dekh raha hoon, installment plan flexible hona chahiye down payment kitni hogi?",
        "agent_exemplar": "Ji bilkul sir! DHA Phase 6 mein hamare paas 4 Crore ka brand new 1 Kanal luxury house available hai jis par flexible 3-year installment plan mil sakta hai. Down payment sirf 25% (takreeban 1 Crore) hai, baqi asaan mahana qiston mein pay kar sakte hain aur 18 months mein physical possession mil jati hai. Kya main aap ka kal sham ka site visit arrange kar doon?"
    },
    {
        "category": "NOC & Legal Legitimacy Verification",
        "user_utterance": "Kya yeh project LDA ya CDA approved hai? Legal NOC papers clear hain ya koi issue to nahi?",
        "agent_exemplar": "Sir 100% legal compliance hamari pehli tarjeeh hai! Yeh project completely LDA aur CDA approved hai with official NOC number. Allotment letters, approved layout maps aur NDC (No Demand Certificate) clear hain. Agar aap chahein to visit ke waqt main hamare Senior Legal Advisor se direct verification files aap ke samnay pesh karwa sakti hoon."
    },
    {
        "category": "Budget Stretching via Installments",
        "user_utterance": "Mera budget 3.5 Crore hai lekin mujhe DHA Phase 6 ya Gulberg mein accha 1 Kanal ghar chahiye, kya mumkin hai?",
        "agent_exemplar": "Sir bilkul mumkin hai! Halankay Phase 6 mein ready houses 4 Crore se start hotay hain, lekin developer ka 36-month easy installment package 3.5 Crore cash budget walon ke liye best fit hai. Aap sirf 90 Lakh upfront de kar booking karwa sakte hain aur baqi asaan installment par chala sakte hain. Is tarah aap ko budget compromise kiye baghair premium category ghar mil jata hai."
    },
    {
        "category": "Urgent Site Visit Closing",
        "user_utterance": "Ghar ki pictures aur location to acchi lag rahi hai, aagay ka kya procedure hoga?",
        "agent_exemplar": "Acha... behtareen tareeqa yeh hai sir ke aap on-ground visit karein taake location aur construction quality khud check kar sakein. Kal Friday sham 4:00 PM ya Saturday subah 11:00 AM mein se kaun sa time aap ke liye comfortable hoga? Main hamare Area Relationship Manager ki VIP slot reserve kar deti hoon."
    },
    {
        "category": "Overseas Pakistani Power of Attorney & RDA",
        "user_utterance": "Main overseas hoon Dubai mein rehta hoon, kya main Roshan Digital Account aur Power of Attorney ke zariye buy kar sakta hoon?",
        "agent_exemplar": "Ji bilkul sir! Hamaray overseas clients ke liye special dedicated desk hai. Aap Pakistan aae baghair Roshan Digital Account (RDA) se direct bank transfer kar sakte hain, aur Pakistani Embassy se attested Special Power of Attorney ke tehat transfer complete ho jata hai. Hum tamam documentation coordinate karwate hain."
    },
    {
        "category": "Price Objection & Market Rate Defense",
        "user_utterance": "Yeh rate bohat zyada lag raha hai, market mein thora sasta mil raha hai doosri jagah.",
        "agent_exemplar": "Hmm... aap ki baat bilkul samajh aati hai sir. Lekin pehli nazar mein rate thora uncha lagta hai kyunkay yeh 100 feet wide main boulevard par LDA approved gated sector mein hai jahan 15-20% annual capital appreciation guaranteed hai. Sastay plots mein aksar utility ya possession delay hota hai. Yahan underground electricity aur gas fully operational hai."
    },
    {
        "category": "Rental Yield & High ROI",
        "user_utterance": "Agar main yeh apartment ya commercial shop khareedoon to rental income aur ROI kitna banay ga?",
        "agent_exemplar": "Sir investment perspective se yeh top-tier asset hai! Commercial shops mein 8% se 10% annual rental yield easily deliver ho raha hai, jabkay residential luxury houses par 5% se 6% rental return ke sath sath 18% capital appreciation milti hai. Tenants ki demand multinational executives aur expats ki taraf se consistently high rehti hai."
    },
    {
        "category": "School & Hospital Proximity",
        "user_utterance": "Bacchon ke schools aur emergency hospitals kitnay distance par hain is location se?",
        "agent_exemplar": "Sir family living ke liye yeh ideal community hai! Top schools jaisay LGS, Beaconhouse aur Roots Millennium sirf 5 se 7 minutes ki drive par hain. Is ke ilawa National Hospital aur Shaukat Khanum Annex medical facilities bilkul 2 kilometer ke radius mein available hain."
    },
    {
        "category": "Possession vs Under Construction Guarantees",
        "user_utterance": "Agar possession waqt par na mili to kya guarantee hai? Construction time par complete hogi?",
        "agent_exemplar": "Sir yeh contractual legal agreement mein penalty clause ke sath written hota hai. Agar possession promised timeline (18 months) se delay hoti hai to developer client ko monthly rent rebate pay karta hai. Sath hi construction work 70% already ground par mukammal ho chuka hai jo aap visit par physically dekh sakte hain."
    },
    {
        "category": "Utility Connections (Sui Gas & Electricity)",
        "user_utterance": "Gas aur bijli ke meters lagay huay hain ya application process chal raha hai?",
        "agent_exemplar": "Sir tamam utilities fully functional hain! Underground 3-phase electricity meters installed hain, water filtration plant functional hai, aur Sui Gas pipe network commissioned hai. Koi pending utility connection dues ya delays nahi hain."
    },
    {
        "category": "Resale & Liquidity Exit Strategy",
        "user_utterance": "Kal ko agar mujhe yeh property resell karni paray to buyer aasani se mil jayega?",
        "agent_exemplar": "Ji bilkul sir! DHA aur Bahria Town ke primary sectors highly liquid assets hain. Ready built property aur main boulevard locations par active open market buyer pool rehta hai. Hamara apna in-house secondary sales network bhi 30 se 45 days ke andar client ko profitable exit provide karta hai."
    },
    {
        "category": "Corner Plot & Park Facing Premium",
        "user_utterance": "Park facing ya corner plot ka price 10% zyada kyun charge kar rahe hain?",
        "agent_exemplar": "Sir corner aur park-facing plots premium inventory hoti hain. Extra ventilation, double frontage car parking aur natural daylight ki wajah se in ki rental demand 20% zyada hoti hai aur future resale par hamesha regular plots se 15-20 Lakh ka extra premium milta hai."
    },
    {
        "category": "Hidden Costs & Transfer Taxes Transparency",
        "user_utterance": "Is price ke ilawa koi hidden charges, FBR taxes ya transfer fee to nahi jo baad mein maangi jaye?",
        "agent_exemplar": "Sir hum 100% transparency follow karte hain. Quotation ke andar property cost, society transfer fees, aur filer taxes (Advance Tax 236K/236C) ka clear breakdown pehle din provide kiya jata hai. Koi hidden ya unannounced commission fee nahi hoti."
    },
    {
        "category": "Weekend Family Site Visit Coordination",
        "user_utterance": "Main week days par busy hota hoon, kya Sunday ko family ke sath visit kar sakte hain?",
        "agent_exemplar": "Zabardast sir! Hamara site office Sunday ko bhi 10:00 AM se 6:00 PM open hota hai. Aap Sunday subah 11:30 AM ya dopahar 3:00 PM family ke sath tashreef laiye, hamaray Senior Executive aap ko coffee ke sath complete project ka physical walkthrough karwayenge."
    },
    {
        "category": "Commercial Shop vs Residential Comparison",
        "user_utterance": "Mera 2 crore ka budget hai, commercial shop lena behtar hai ya residential plot?",
        "agent_exemplar": "Sir agar aap ka goal regular monthly rental income hai to 2 Crore mein Bahria ya DHA Commercial Hub mein ground floor shop best hai jo 1.5 se 1.8 Lakh monthly rent generate karegi. Lekin agar aap ka target 3 saal baad big capital gain hai to residential plot 50% se zyada appreciate karega. Main dono options ki comparative analysis sheet aap ko WhatsApp karwa sakti hoon."
    }
]


class DialogueMemoryEngine:
    """
    Phase 2 Dynamic Few-Shot In-Context Learning Engine.
    - Manages cold-start winning exemplars and dynamically indexes newly converted calls.
    - Performs cosine similarity matching against caller queries.
    - Yields structured few-shot sales guidance to steer LLM tone and objection handling.
    """
    def __init__(self, similarity_threshold: float = 0.65):
        self.similarity_threshold = similarity_threshold
        init_db()
        self.exemplars_cache: List[Dict[str, Any]] = []
        self.seed_exemplars_if_empty()
        self.reload_cache()

    def seed_exemplars_if_empty(self):
        """Seeds the database with high-converting cold start corpus if empty."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM dialogue_exemplars")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print(f"[DialogueMemoryEngine] Seeding {len(COLD_START_EXEMPLARS)} cold-start exemplars...")
            for ex in COLD_START_EXEMPLARS:
                # Precompute vector embedding
                vec = embedding_service.get_embedding(ex["user_utterance"])
                vec_json = json.dumps(vec)
                cursor.execute("""
                    INSERT INTO dialogue_exemplars (
                        category, user_utterance, agent_exemplar, embedding, conversion_count, source_session_id
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    ex["category"],
                    ex["user_utterance"],
                    ex["agent_exemplar"],
                    vec_json,
                    5,  # initial weight for proven baseline
                    "seed_corpus"
                ))
            conn.commit()
            print("[DialogueMemoryEngine] Cold-start seed complete.")
            
        conn.close()

    def reload_cache(self):
        """Loads all exemplars into memory with numpy vectors for sub-millisecond retrieval."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, category, user_utterance, agent_exemplar, embedding, conversion_count FROM dialogue_exemplars")
        rows = cursor.fetchall()
        conn.close()

        loaded = []
        for r in rows:
            try:
                vec = json.loads(r["embedding"])
                vec_np = np.array(vec, dtype=float)
                norm = np.linalg.norm(vec_np)
                if norm > 0:
                    vec_np = vec_np / norm
                loaded.append({
                    "id": r["id"],
                    "category": r["category"],
                    "user_utterance": r["user_utterance"],
                    "agent_exemplar": r["agent_exemplar"],
                    "conversion_count": r["conversion_count"],
                    "vector": vec_np
                })
            except Exception as e:
                continue

        self.exemplars_cache = loaded

    def retrieve_exemplar(self, user_query: str, threshold: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Matches user query against proven winning exemplars.
        Returns the top matching exemplar if similarity exceeds threshold.
        """
        if not user_query or not user_query.strip() or not self.exemplars_cache:
            return None

        min_thresh = threshold if threshold is not None else self.similarity_threshold
        query_vec = embedding_service.get_embedding(user_query.strip())
        q_np = np.array(query_vec, dtype=float)
        norm_q = np.linalg.norm(q_np)
        if norm_q == 0:
            return None
        q_np = q_np / norm_q

        best_score = -1.0
        best_ex = None

        for ex in self.exemplars_cache:
            # Check vector dimension compatibility
            if len(ex["vector"]) != len(q_np):
                continue
            sim = float(np.dot(q_np, ex["vector"]))
            if sim > best_score:
                best_score = sim
                best_ex = ex

        if best_ex and best_score >= min_thresh:
            guidance_banner = (
                f"=== PROVEN SALES GUIDANCE (FEW-SHOT HIGH CONVERTING EXEMPLAR) ===\n"
                f"Context Category: {best_ex['category']}\n"
                f"Similarity Score: {best_score:.3f}\n"
                f"Proven High-Converting Agent Response Style:\n"
                f"\"{best_ex['agent_exemplar']}\"\n"
                f"MANDATORY INSTRUCTION: Emulate this empathetic tone, reassurance, and proactive closing strategy in your reply.\n"
            )
            return {
                "id": best_ex["id"],
                "category": best_ex["category"],
                "user_utterance": best_ex["user_utterance"],
                "agent_exemplar": best_ex["agent_exemplar"],
                "similarity": best_score,
                "banner": guidance_banner
            }

        return None

    def index_converted_session(self, session_id: str) -> int:
        """
        Auto-learning feedback loop:
        Extracts key customer objection turns & agent responses from a converted call,
        computes embeddings, and updates dialogue_exemplars.
        """
        if not session_id:
            return 0

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT raw_transcript, normalized_transcript, agent_response 
            FROM crm_call_transcripts 
            WHERE session_id = ?
            ORDER BY id ASC
        """, (session_id,))
        turns = cursor.fetchall()
        
        if not turns:
            conn.close()
            return 0

        indexed_count = 0
        ignored_phrases = ["assalam", "salam", "hello", "hi", "ok", "acha", "theek", "shukriya", "bye", "allah hafiz"]

        for t in turns:
            user_text = (t["normalized_transcript"] or t["raw_transcript"] or "").strip()
            agent_text = (t["agent_response"] or "").strip()

            # Filter trivial greetings or short affirmative grunts
            if len(user_text.split()) < 3 or any(user_text.lower() == p for p in ignored_phrases):
                continue
            if len(agent_text.split()) < 5:
                continue

            # Compute embedding for caller's query
            vec = embedding_service.get_embedding(user_text)
            q_np = np.array(vec, dtype=float)
            norm_q = np.linalg.norm(q_np)
            if norm_q > 0:
                q_np = q_np / norm_q

            # Check if this closely matches an existing exemplar
            matched_id = None
            for ex in self.exemplars_cache:
                if len(ex["vector"]) == len(q_np):
                    if float(np.dot(q_np, ex["vector"])) >= 0.85:
                        matched_id = ex["id"]
                        break

            if matched_id:
                # Increment conversion count for reinforced exemplar
                cursor.execute("""
                    UPDATE dialogue_exemplars 
                    SET conversion_count = conversion_count + 1 
                    WHERE id = ?
                """, (matched_id,))
                indexed_count += 1
            else:
                # Insert as a new learned exemplar
                cursor.execute("""
                    INSERT INTO dialogue_exemplars (
                        category, user_utterance, agent_exemplar, embedding, conversion_count, source_session_id
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    "Learned Booking Turn",
                    user_text,
                    agent_text,
                    json.dumps(vec),
                    1,
                    session_id
                ))
                indexed_count += 1

        conn.commit()
        conn.close()

        if indexed_count > 0:
            self.reload_cache()
            print(f"[DialogueMemoryEngine] Indexed {indexed_count} winning turns from session {session_id}.")

        return indexed_count


# Global singleton instance
dialogue_memory = DialogueMemoryEngine()
