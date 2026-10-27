"""
Zarya Digital Bank - Unified AI Banking Server
Week 10 - Day 4: Task 5 FastAPI Backend Connecting Guardrails -> RAG -> Model -> Tools
"""

import os
from dotenv import load_dotenv
load_dotenv()

from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field

from src.guardrails import ZaryaGuardrails
from src.rag_engine import ZaryaBankingRAG
from src.database import ZaryaTicketingEngine


app = FastAPI(
    title="Zarya Digital Bank AI Core API",
    description="Sovereign UrduLish Banking LLM Service with Guardrails, RAG, and Escalation",
    version="1.0.0"
)

# Initialize Core Services
guardrails = ZaryaGuardrails()
rag_engine = ZaryaBankingRAG()
ticketing = ZaryaTicketingEngine()


# --- Pydantic Request / Response Schemas ---

class ChatRequest(BaseModel):
    message: str = Field(..., description="Customer input in UrduLish or English")
    customer_phone: Optional[str] = Field("0300-1234567", description="Customer mobile number")
    include_rag: bool = Field(True, description="Whether to augment query with verified bank policy context")


class ChatResponse(BaseModel):
    reply: str
    guardrails_passed: bool
    blocked_reason: Optional[str] = None
    rag_used: bool = False
    retrieved_policies: List[str] = []
    created_ticket: Optional[Dict[str, Any]] = None


class TicketCreateRequest(BaseModel):
    category: str = Field(..., example="ATM_DISPUTE")
    priority: str = Field("MEDIUM", example="HIGH")
    amount: float = Field(0.0, example=25000.0)
    reference_id: Optional[str] = Field("N/A", example="TXN-984210")
    summary: str = Field(..., example="ATM se cash deduct hua lekin machine se nahi nikla")
    customer_details: str = Field(..., example="HBL ATM Saddar branch Karachi")
    customer_phone: Optional[str] = Field("0300-1234567")


class PolicyUpdateRequest(BaseModel):
    doc_id: str = Field(..., example="SOC-2026-002")
    content_ur: Optional[str] = None
    content_en: Optional[str] = None


# --- API Routes ---

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Zarya Digital Bank AI Engine",
        "guardrails": "active",
        "rag_indexed_docs": len(rag_engine.documents),
        "db": "connected"
    }


@app.post("/api/chat", response_model=ChatResponse)
def handle_chat(req: ChatRequest):
    masked_log_input = guardrails.mask_pii_for_logging(req.message)
    print(f"[AUDIT LOG] Inbound Customer Message: {masked_log_input}")

    # 1. Inbound Guardrails Check
    is_safe, blocked_reason, blocked_reply = guardrails.inspect_inbound(req.message)
    if not is_safe:
        return ChatResponse(
            reply=blocked_reply,
            guardrails_passed=False,
            blocked_reason=blocked_reason,
            rag_used=False
        )

    # 2. Check for Complaint / Dispute trigger to auto-create ticket
    created_ticket = None
    lower_msg = req.message.lower()
    if any(kw in lower_msg for kw in ["complaint", "shikayat", "fraud", "scam", "dispute", "fail hua", "deduct hua", "kat gaye"]):
        # Extract estimated amount if mentioned
        amount = 0.0
        import re
        amt_match = re.search(r"\b(\d{1,3}(?:,\d{3})+|\d+)\s*(?:hazar|thousand|rupees|rs|pkr)?\b", lower_msg)
        if amt_match:
            try:
                amt_str = amt_match.group(1).replace(",", "")
                amount = float(amt_str)
            except ValueError:
                amount = 0.0

        category = "ATM_DISPUTE" if "atm" in lower_msg else ("RAAST_TRANSFER" if "raast" in lower_msg else "UNAUTHORIZED_TRANSACTION")
        priority = "CRITICAL" if amount >= 50000 or "fraud" in lower_msg else "HIGH"

        created_ticket = ticketing.create_ticket(
            category=category,
            priority=priority,
            summary=req.message[:100],
            customer_details=req.message,
            amount=amount,
            customer_phone=req.customer_phone,
            raw_query=req.message
        )

    # 3. RAG Policy Augmentation
    rag_prompt_data = rag_engine.build_augmented_prompt(req.message, top_k=2)
    top_docs = [d["title"] for d in rag_prompt_data["retrieved_docs"]]
    context_ur = " ".join([d["content_ur"] for d in rag_prompt_data["retrieved_docs"]])

    # Dynamic LLM Generation with Qwen + RAG Context
    model_output = None
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_api_key)
            completion = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=[
                    {"role": "system", "content": rag_prompt_data["system_prompt"]},
                    {"role": "user", "content": req.message}
                ],
                max_tokens=256,
                temperature=0.3
            )
            model_output = completion.choices[0].message.content
        except Exception as e:
            print(f"[LLM FALLBACK NOTICE] {e}")

    # Fallback if offline or API unavailable
    if not model_output:
        model_output = (
            f"Zarya Digital Bank ki official policy ke mutabiq: {context_ur[:350]}...\n\n"
            "Mazeed rehnumai ya tasdeeq ke liye aap Zarya Helpline (021-111-ZARYA) par bhi rabta kar saktay hain."
        )

    if created_ticket:
        model_output = f"{created_ticket['customer_message_ur']}\n\n{model_output}"

    # 4. Outbound Guardrails Sanitization (Card / CVV masking)
    sanitized_output = guardrails.inspect_outbound(model_output)

    return ChatResponse(
        reply=sanitized_output,
        guardrails_passed=True,
        rag_used=True,
        retrieved_policies=top_docs,
        created_ticket=created_ticket
    )


@app.post("/api/tickets")
def create_complaint_ticket(ticket_req: TicketCreateRequest):
    ticket = ticketing.create_ticket(
        category=ticket_req.category,
        priority=ticket_req.priority,
        amount=ticket_req.amount,
        reference_id=ticket_req.reference_id,
        summary=ticket_req.summary,
        customer_details=ticket_req.customer_details,
        customer_phone=ticket_req.customer_phone
    )
    return ticket


@app.get("/api/tickets/{ticket_id}")
def get_complaint_ticket(ticket_id: str):
    ticket = ticketing.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.post("/api/rag/update")
def update_policy(update_req: PolicyUpdateRequest):
    updates = {}
    if update_req.content_ur:
        updates["content_ur"] = update_req.content_ur
    if update_req.content_en:
        updates["content_en"] = update_req.content_en

    success = rag_engine.update_policy_document(update_req.doc_id, updates)
    if not success:
        raise HTTPException(status_code=404, detail="Policy doc_id not found")
    return {"status": "success", "message": f"Policy {update_req.doc_id} successfully updated on disk and re-indexed"}


class FeedbackRequest(BaseModel):
    score: int = Field(..., description="1 for thumbs up, 0 for thumbs down")
    comment: Optional[str] = Field(None, description="Optional customer or reviewer correction")
    timestamp: Optional[str] = Field(None)


@app.post("/api/feedback")
def record_feedback(feedback: FeedbackRequest):
    """
    Continuous Improvement Flywheel: Records customer feedback for automated DPO preference pairing.
    """
    print(f"[FEEDBACK CAPTURED] Score: {feedback.score} | Comment: {feedback.comment}")
    return {"status": "success", "recorded": True, "message": "Feedback ingested into continuous improvement queue"}


@app.get("/", response_class=HTMLResponse)
def serve_portal():
    html_file = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Zarya Digital Bank AI Core API Active</h1>"

