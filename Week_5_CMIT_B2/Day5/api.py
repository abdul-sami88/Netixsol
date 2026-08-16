"""
Week 5 Day 5 Capstone: FastAPI wrapper for the Freelance Client Inquiry
& Proposal Agent, with structured logging suitable for later monitoring.
"""

import logging
import os
import sys
import time
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agent_system import agent_app  # noqa: E402

# ---------------------------------------------------------------------
# Logging setup: inputs, tool calls (via node status), latency, tokens, errors
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("agent_api.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("intake_agent")

app = FastAPI(title="Freelance Client Intake & Proposal Agent API", version="1.0.0")


class InquiryRequest(BaseModel):
    client_message: str
    target_currency: Optional[str] = "USD"

    @field_validator("client_message")
    @classmethod
    def not_absurdly_long(cls, v: str) -> str:
        if len(v) > 4000:
            raise ValueError("client_message exceeds 4000 character limit")
        return v


class InquiryResponse(BaseModel):
    inquiry_id: str
    category: str
    draft_response: str
    quote_usd: Optional[float] = None
    quote_converted: Optional[float] = None
    conversion_note: Optional[str] = None
    needs_human: bool
    status: str
    latency_ms: float


class ApprovalRequest(BaseModel):
    inquiry_id: str
    approve: bool


@app.post("/inquiry", response_model=InquiryResponse)
async def process_inquiry(request: InquiryRequest):
    start_time = time.time()
    inquiry_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": inquiry_id}}

    logger.info(
        f"New Inquiry | ID: {inquiry_id} | Currency: {request.target_currency} | "
        f"Input: '{request.client_message[:120]}'"
    )

    try:
        result = agent_app.invoke(
            {
                "client_message": request.client_message,
                "target_currency": request.target_currency or "USD",
                "needs_human": False,
            },
            config=config,
        )

        next_state = agent_app.get_state(config)
        is_paused = len(next_state.next) > 0 and next_state.next[0] == "human_review"
        status = "Pending_Human_Approval" if is_paused else result.get("status", "Unknown")

        latency = (time.time() - start_time) * 1000
        mock_tokens = len(request.client_message.split()) * 2 + 40  # est. token usage for cost tracking

        logger.info(
            f"Inquiry Processed | ID: {inquiry_id} | Category: {result.get('category')} | "
            f"Status: {status} | Latency: {latency:.1f}ms | Est Tokens: {mock_tokens} | "
            f"NeedsHuman: {is_paused} | ToolNote: {result.get('conversion_note', 'n/a')}"
        )

        return InquiryResponse(
            inquiry_id=inquiry_id,
            category=result.get("category", "Unknown"),
            draft_response=result.get("draft_response", ""),
            quote_usd=result.get("quote_usd"),
            quote_converted=result.get("quote_converted"),
            conversion_note=result.get("conversion_note"),
            needs_human=is_paused,
            status=status,
            latency_ms=latency,
        )

    except Exception as e:
        latency = (time.time() - start_time) * 1000
        logger.error(f"Agent Execution Error | ID: {inquiry_id} | Latency: {latency:.1f}ms | {e}")
        raise HTTPException(status_code=500, detail="Internal agent error") from e


@app.post("/approve")
async def approve_inquiry(request: ApprovalRequest):
    """Human-in-the-loop checkpoint: a reviewer approves or rejects a
    priced proposal before it is dispatched to the client."""
    config = {"configurable": {"thread_id": request.inquiry_id}}
    start_time = time.time()
    try:
        current = agent_app.get_state(config)
        if not current.next or current.next[0] != "human_review":
            raise HTTPException(status_code=400, detail="Inquiry is not awaiting human review")

        new_status = "Approved by Human" if request.approve else "Rejected by Human"
        agent_app.update_state(config, {"status": new_status})
        final = agent_app.invoke(None, config=config)

        latency = (time.time() - start_time) * 1000
        logger.info(
            f"Human Decision | ID: {request.inquiry_id} | Approved: {request.approve} | "
            f"Final Status: {final.get('status')} | Latency: {latency:.1f}ms"
        )
        return {"inquiry_id": request.inquiry_id, "final_status": final.get("status")}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approval Error | ID: {request.inquiry_id} | {e}")
        raise HTTPException(status_code=500, detail="Internal agent error") from e


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    print("Run with: uvicorn api:app --reload")
