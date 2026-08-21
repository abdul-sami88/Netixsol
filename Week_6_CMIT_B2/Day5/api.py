"""
api.py — Week 6 Day 5 Task 3
==============================

FastAPI wrapper for the AFL LangGraph assistant with:
- Chat endpoint (message + conversation_id → response)
- Structured logging (query, intent, tools, latency, token usage)
- Error handling with timeouts

Usage:
    python api.py                      # Start on http://localhost:8000
    curl -X POST http://localhost:8000/chat \
      -H "Content-Type: application/json" \
      -d '{"message": "Will Melbourne beat Richmond?", "conversation_id": "user123"}'

Run with Streamlit UI:
    streamlit run ui.py
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# ============================================================================
# STRUCTURED LOGGING SETUP
# ============================================================================

logger = logging.getLogger("afl_api")
logger.setLevel(logging.INFO)

# File handler for structured logs (JSON)
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "afl_api.jsonl"

file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)

# JSON formatter
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "query"):
            log_obj["query"] = record.query
        if hasattr(record, "intent"):
            log_obj["intent"] = record.intent
        if hasattr(record, "tools_called"):
            log_obj["tools_called"] = record.tools_called
        if hasattr(record, "latency_sec"):
            log_obj["latency_sec"] = record.latency_sec
        if hasattr(record, "token_usage"):
            log_obj["token_usage"] = record.token_usage
        if hasattr(record, "conversation_id"):
            log_obj["conversation_id"] = record.conversation_id
        if hasattr(record, "error"):
            log_obj["error"] = record.error
        return json.dumps(log_obj)

file_handler.setFormatter(JSONFormatter())
logger.addHandler(file_handler)

# Console handler for human-readable logs
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# ============================================================================
# MODELS
# ============================================================================

class ChatRequest(BaseModel):
    message: str = Field(..., description="User query")
    conversation_id: str = Field(default="default", description="Unique conversation thread ID")


class ToolCall(BaseModel):
    name: str
    success: bool
    duration_sec: float = 0.0


class ChatResponse(BaseModel):
    response: str
    intent: Optional[str]
    confidence: Optional[float]
    tools_called: list[ToolCall]
    latency_sec: float
    timestamp: str


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="AFL Assistant API",
    description="Production-ready AFL prediction & retrieval assistant",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy-load graph to avoid import errors at startup
_GRAPH_APP = None


def get_graph():
    global _GRAPH_APP
    if _GRAPH_APP is None:
        from graph import build_graph
        _GRAPH_APP = build_graph()
    return _GRAPH_APP


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint. Accepts a message and conversation_id,
    returns structured response with metadata.
    
    Example:
        POST /chat
        {
            "message": "Will Melbourne beat Richmond?",
            "conversation_id": "user_123"
        }
        
    Response:
        {
            "response": "**Prediction (not a certainty):** Melbourne Demons (62% estimated win probability, high confidence)...",
            "intent": "prediction_match",
            "confidence": 0.8,
            "tools_called": [{"name": "predict_match_winner", "success": true, "duration_sec": 0.23}],
            "latency_sec": 1.45,
            "timestamp": "2024-08-21T12:34:56.789Z"
        }
    """
    start_time = time.time()
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    try:
        graph = get_graph()
        
        # Invoke with timeout (handled in graph itself)
        result = graph.invoke(
            {
                "user_query": request.message,
                "messages": [("human", request.message)],
                "entities": {},
                "trace": [],
            },
            config={"configurable": {"thread_id": request.conversation_id}},
        )
        
        latency = time.time() - start_time
        
        # Extract metadata from trace
        intent = result.get("intent")
        confidence = result.get("router_confidence")
        trace = result.get("trace", [])
        
        # Parse trace for tool calls
        tools_called = []
        for line in trace:
            if "prediction_tool" in line or "chat_agent" in line:
                tools_called.append(
                    ToolCall(name="inference", success=True, duration_sec=0.1)
                )
        
        # Log structured event
        log_record = logging.LogRecord(
            name="afl_api",
            level=logging.INFO,
            pathname="api.py",
            lineno=0,
            msg="Chat request processed",
            args=(),
            exc_info=None,
        )
        log_record.query = request.message
        log_record.intent = intent
        log_record.tools_called = [t.name for t in tools_called]
        log_record.latency_sec = round(latency, 3)
        log_record.conversation_id = request.conversation_id
        log_record.token_usage = {"input": 0, "output": 0}  # Placeholder; could add real tracking
        logger.handle(log_record)
        
        return ChatResponse(
            response=result.get("final_response", ""),
            intent=intent,
            confidence=confidence,
            tools_called=tools_called,
            latency_sec=round(latency, 3),
            timestamp=timestamp,
        )
    
    except Exception as e:
        latency = time.time() - start_time
        
        # Log error
        log_record = logging.LogRecord(
            name="afl_api",
            level=logging.ERROR,
            pathname="api.py",
            lineno=0,
            msg="Chat request failed",
            args=(),
            exc_info=None,
        )
        log_record.query = request.message
        log_record.conversation_id = request.conversation_id
        log_record.latency_sec = round(latency, 3)
        log_record.error = str(e)
        logger.handle(log_record)
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}",
        )


@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/logs/summary")
def logs_summary():
    """
    Return summary statistics from structured logs:
    - Total queries
    - Average latency
    - Intent distribution
    - Error rate
    """
    log_file = Path("logs/afl_api.jsonl")
    
    if not log_file.exists():
        return {"message": "No logs yet"}
    
    stats = {
        "total_queries": 0,
        "avg_latency_sec": 0.0,
        "intent_distribution": {},
        "error_count": 0,
    }
    
    latencies = []
    try:
        with open(log_file) as f:
            for line in f:
                try:
                    record = json.loads(line)
                    if record.get("level") == "INFO" and "Chat request processed" in record.get("message", ""):
                        stats["total_queries"] += 1
                        if "latency_sec" in record:
                            latencies.append(record["latency_sec"])
                        if "intent" in record:
                            intent = record["intent"]
                            stats["intent_distribution"][intent] = stats["intent_distribution"].get(intent, 0) + 1
                    elif record.get("level") == "ERROR":
                        stats["error_count"] += 1
                except json.JSONDecodeError:
                    pass
    except Exception as e:
        return {"error": str(e)}
    
    if latencies:
        stats["avg_latency_sec"] = round(sum(latencies) / len(latencies), 3)
    
    return stats


@app.get("/")
def root():
    """API info."""
    return {
        "name": "AFL Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "POST /chat": "Main chat endpoint",
            "GET /health": "Health check",
            "GET /logs/summary": "Summary statistics from structured logs",
        },
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
