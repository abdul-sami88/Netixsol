"""
Socratic AI Tutor Engine
Core conversational agent delivering grounded, Socratic, mastery-adapted guidance in English and UrduLish.
Grounded in course assets with video timestamp citations and strict anti-leakage guardrails.
"""

from typing import Dict, Any, List, Optional
import json
import re
from socratic_tutor.grounded_rag import GroundedRAGRetriever
from socratic_tutor.socratic_ladder import SocraticHintLadder
from socratic_tutor.guardrails import GuardrailsDefense

class SocraticTutorEngine:
    """
    Intelligent conversational tutor embodying the 1 am Socratic mentor persona.
    """

    def __init__(self, db_path: str = "data/content_vector_db.json"):
        self.rag = GroundedRAGRetriever(db_path)
        self.ladder = SocraticHintLadder()
        self.guardrails = GuardrailsDefense()
        # student_id -> conversation state
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get_or_create_session(
        self,
        student_id: str,
        student_name: str = "Student",
        mastery_score: float = 0.40,
        preferred_language: str = "english"
    ) -> Dict[str, Any]:
        """Initializes or retrieves student conversation session."""
        if student_id not in self.sessions:
            self.sessions[student_id] = {
                "student_id": student_id,
                "student_name": student_name,
                "mastery_score": mastery_score,
                "preferred_language": preferred_language.lower(),
                "current_concept": "recursion",
                "current_rung": 1,
                "history": [],
                "leakage_attempts_blocked": 0
            }
        return self.sessions[student_id]

    def respond(
        self,
        student_id: str,
        user_message: str,
        student_name: str = "Student",
        mastery_score: float = 0.40,
        language: str = "english",
        forbidden_solution_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes student input and produces a grounded Socratic response.
        """
        session = self.get_or_create_session(student_id, student_name, mastery_score, language)
        lang = session["preferred_language"]

        # 1. Guardrail Check: Jailbreak / Prompt Injection Detection
        is_jailbreak, reason = self.guardrails.detect_jailbreak(user_message)
        if is_jailbreak:
            session["leakage_attempts_blocked"] += 1
            refusal = self.guardrails.get_jailbreak_refusal_message(lang)
            return {
                "tutor_response": refusal,
                "rung": session["current_rung"],
                "is_jailbreak_blocked": True,
                "answer_leaked": False,
                "citation": ""
            }

        # 2. Check for Direct Solution Demand
        is_demanding_solution = self.guardrails.detect_solution_demand(user_message)
        if is_demanding_solution:
            session["leakage_attempts_blocked"] += 1
            if lang == "urdulish":
                prefix = f"Suno {student_name}, raat ke 1 baj rahay hain aur I know thora stress ho raha hai! Lekin agar main poora code likh doon to exam ya real project mein aap kaisay karogay? Aao mil kar solve karte hain.\n\n"
            else:
                prefix = f"Hey {student_name}, I know it's 1 am and you're tired, but handing you the full code won't build your confidence. Let's tackle this together step-by-step.\n\n"
        else:
            prefix = ""

        # 3. Detect Concept Context from message or session
        concept = session["current_concept"]
        for c_cand in ["recursion", "while_loops", "for_loops", "functions_def", "lists", "dictionaries"]:
            if c_cand in user_message.lower() or c_cand.replace("_", " ") in user_message.lower():
                concept = c_cand
                session["current_concept"] = concept
                break

        # 4. Advance Hint Ladder if student asks for next hint or expresses being stuck
        stuck_keywords = ["still stuck", "next hint", "give me more", "samajh nahi aaya", "aur batao", "what next", "hint please"]
        if any(kw in user_message.lower() for kw in stuck_keywords):
            session["current_rung"] = min(4, session["current_rung"] + 1)
        elif "got it" in user_message.lower() or "samajh aa gaya" in user_message.lower():
            session["current_rung"] = 1

        rung = session["current_rung"]

        # 5. Retrieve Grounded Context from Vector DB with Timestamps
        rag_res = self.rag.retrieve_grounding_context(query=f"{concept} {user_message}", top_k=2)
        citation = self.rag.format_citation_link(rag_res["video_timestamps"], lang)

        # 6. Generate Socratic Hint Ladder Content
        ladder_step = self.ladder.get_ladder_step(concept_id=concept, rung=rung, language=lang)
        hint_text = ladder_step["hint_text"]

        # 7. Mastery-based Tone & Scaffolding Adaptation
        m_score = session["mastery_score"]
        if m_score < 0.45: # Novice Tier
            if lang == "urdulish":
                pedagogy_note = "Pehle simple socho: recursive function aik Russian doll ki tarah hota hai jo khulti jati hai jab tak aakhri sab se choti guriya na aa jaye.\n\n"
            else:
                pedagogy_note = "Let's use a simple metaphor: think of recursion like Russian nesting dolls, opening each smaller layer until you reach the solid tiny doll at the center.\n\n"
        elif m_score >= 0.75: # Advanced Tier
            if lang == "urdulish":
                pedagogy_note = "Aapka core logic strong hai! Yahan call stack depth aur memory overhead (O(n) space) ko mind mein rakhein.\n\n"
            else:
                pedagogy_note = "You have a solid foundation! Focus on the stack frame state and how each frame unwinds when returning.\n\n"
        else: # Intermediate Tier
            pedagogy_note = ""

        # Assemble Tutor Response
        full_response = f"{prefix}{pedagogy_note}{hint_text}{citation}"

        # 8. Post-Generation Guardrail: Check for Solution Leakage
        forbidden = [forbidden_solution_code] if forbidden_solution_code else []
        sanitized_response, was_leaked = self.guardrails.sanitize_response(full_response, forbidden)

        session["history"].append({"user": user_message, "tutor": sanitized_response})

        return {
            "student_name": student_name,
            "concept": concept,
            "rung": rung,
            "rung_name": ladder_step["rung_name"],
            "tutor_response": sanitized_response,
            "is_jailbreak_blocked": False,
            "answer_leaked": was_leaked,
            "has_video_citation": len(rag_res["video_timestamps"]) > 0,
            "language": lang
        }
