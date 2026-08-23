"""
api.py — AFL Assistant FastAPI Wrapper
=========================================================

Task 1 hardening notes:
- Timeout handling uses asyncio.wait_for + asyncio.to_thread, NOT signal.alarm.
  The previous version used signal.alarm, which only works in the main
  thread of the main interpreter -- but FastAPI runs sync route handlers in
  a worker thread pool by default, so signal.alarm raised
  "signal only works in main thread of the main interpreter" on EVERY
  request in a real deployment (confirmed via TestClient). This is very
  likely the actual cause of "prediction fails / doesn't understand the
  query" reports -- the request never reached the graph at all, it crashed
  in the timeout wrapper before doing anything.
- Basic abuse/rate tracking: a lightweight in-memory per-conversation
  counter flags repeated off-topic queries (possible scope-probing /
  prompt-injection attempts) for logging -- see `_track_abuse_signal()`.
  This is intentionally simple (in-memory, resets on restart); a real
  deployment should move this to Redis/a proper rate limiter, noted in the
  monitoring checklist.
- Disclaimer consistency check: prediction responses are verified to
  contain disclaimer language before being returned; a violation is logged
  as an error (should never happen given nodes.py's structural guarantee,
  but this is a cheap defense-in-depth check worth having in production).

Usage:
    python api.py
    # Runs on http://localhost:8000

Test:
    curl -X POST http://localhost:8000/chat \
      -H "Content-Type: application/json" \
      -d '{"message": "Will Melbourne beat Richmond?", "conversation_id": "test"}'
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
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
# ABUSE / SCOPE-PROBING TRACKING (Task 1: basic rate/abuse handling)
# ============================================================================
# Lightweight in-memory tracking of repeated off-topic queries per
# conversation -- a signal for scope-probing or prompt-injection attempts
# trying to push the assistant outside its AFL-only scope. Intentionally
# simple (resets on process restart, no cross-instance sharing); a real
# deployment should back this with Redis or a proper rate limiter -- see
# MONITORING.md.
_OFF_TOPIC_HISTORY: dict[str, deque] = defaultdict(lambda: deque(maxlen=20))
_OFF_TOPIC_WINDOW_SECONDS = 300
_OFF_TOPIC_ALERT_THRESHOLD = 5


def _track_abuse_signal(conversation_id: str, intent: Optional[str], query: str) -> None:
    if intent != "off_topic":
        return
    now = time.time()
    history = _OFF_TOPIC_HISTORY[conversation_id]
    history.append(now)
    recent = [t for t in history if now - t <= _OFF_TOPIC_WINDOW_SECONDS]
    if len(recent) >= _OFF_TOPIC_ALERT_THRESHOLD:
        logger.warning(
            f"Possible scope-probing: conversation_id={conversation_id} has "
            f"{len(recent)} off-topic queries in the last {_OFF_TOPIC_WINDOW_SECONDS}s "
            f"(most recent: {query[:80]!r})"
        )


_DISCLAIMER_MARKERS = ("not a certainty", "statistical estimate", "not a guarantee")


def _check_disclaimer_consistency(intent: Optional[str], response_text: str) -> None:
    """Defense-in-depth: nodes.py structurally guarantees every prediction
    response carries disclaimer language, but this is cheap to verify at
    the API boundary too, and a violation here would indicate a real bug
    worth paging on rather than silently shipping an unhedged prediction."""
    if intent not in ("prediction_match", "prediction_player"):
        return
    if not any(marker in response_text.lower() for marker in _DISCLAIMER_MARKERS):
        logger.error(
            f"DISCLAIMER MISSING on a {intent} response -- this should be "
            f"structurally impossible; investigate nodes.py's response_formatter_node. "
            f"Response was: {response_text[:200]!r}"
        )


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
_PREDICT_AVAILABLE = False


def get_graph():
    global _GRAPH_APP
    if _GRAPH_APP is None:
        try:
            from graph import build_graph
            _GRAPH_APP = build_graph()
            logger.info("Graph loaded successfully")
        except ImportError as e:
            logger.error(f"Failed to import graph: {e}")
            raise RuntimeError(f"Graph initialization failed: {e}")
    return _GRAPH_APP


def check_predict_available():
    """Validate that predict.py and artifacts are available."""
    global _PREDICT_AVAILABLE
    if _PREDICT_AVAILABLE:
        return True
    
    try:
        from day2_interface import is_available
        available, error = is_available()
        if not available:
            logger.warning(f"Predict module not available: {error}")
            return False
        _PREDICT_AVAILABLE = True
        logger.info("Predict module validated")
        return True
    except Exception as e:
        logger.warning(f"Could not validate predict module: {e}")
        return False


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.on_event("startup")
def startup_event():
    """Validate dependencies on startup."""
    try:
        graph = get_graph()
        logger.info("✓ Graph loaded")
        
        # Check if predict.py is available (not critical, but good to know)
        if check_predict_available():
            logger.info("✓ Predict module available (predictions enabled)")
        else:
            logger.warning("⚠ Predict module not available (factual queries only)")
    except Exception as e:
        logger.error(f"Startup validation failed: {e}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint. Accepts a message and conversation_id,
    returns structured response with metadata.
    
    Handles:
    - Prediction queries (match winner, top player)
    - Factual queries (AFL rules, statistics)
    - Off-topic detection (scope guardrails)
    - Multi-turn conversations (thread-based memory)
    
    Example:
        POST /chat
        {
            "message": "Will Melbourne beat Richmond?",
            "conversation_id": "user_123"
        }
        
    Response:
        {
            "response": "**Prediction (not a certainty):** Melbourne Demons (62% estimated win probability)...",
            "intent": "prediction_match",
            "confidence": 0.8,
            "tools_called": [{"name": "predict_match_winner", "success": true}],
            "latency_sec": 0.5,
            "timestamp": "2024-08-21T12:34:56.789Z"
        }
    """
    start_time = time.time()
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    try:
        # Validate input -- these are CLIENT errors (400), not server errors (500)
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        if len(request.message) > 5000:
            raise HTTPException(status_code=400, detail="Message too long (max 5000 characters)")
        
        logger.info(f"Processing query: {request.message[:50]}... (conversation_id: {request.conversation_id})")
        
        # Get graph and invoke with a real, thread-safe timeout.
        # asyncio.to_thread runs the blocking graph.invoke() call in a
        # worker thread; asyncio.wait_for enforces the timeout from the
        # event loop, which works correctly regardless of which thread the
        # request handler itself is running in (unlike signal.alarm, which
        # only works in the main thread and would raise on every request
        # under FastAPI's default threaded execution of sync endpoints).
        graph = get_graph()
        initial_state = {
            "user_query": request.message,
            "messages": [("human", request.message)],
            "entities": {},
            "trace": [],
        }
        config = {"configurable": {"thread_id": request.conversation_id}}

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(graph.invoke, initial_state, config),
                timeout=30,
            )
        except asyncio.TimeoutError:
            logger.error(f"Graph invoke timed out (>30s) for conversation_id={request.conversation_id}")
            raise HTTPException(
                status_code=504,
                detail="Request timed out (the assistant took too long to respond)"
            )
        
        if result is None:
            raise RuntimeError("Graph returned None result")
        
        latency = time.time() - start_time
        
        # Extract metadata from result
        intent = result.get("intent")
        confidence = result.get("router_confidence")
        trace = result.get("trace", [])
        final_response = result.get("final_response", "")
        
        # Validate response
        if not final_response:
            logger.warning(f"Empty response from graph for query: {request.message[:50]}")
            raise RuntimeError("Graph returned empty response")

        _check_disclaimer_consistency(intent, final_response)
        _track_abuse_signal(request.conversation_id, intent, request.message)
        
        # Parse trace for tool calls
        tools_called = []
        
        for line in trace:
            if "[prediction_tool]" in line and "predict_match_winner(" in line:
                tools_called.append(ToolCall(name="predict_match_winner", success=True, duration_sec=0.1))
            elif "[prediction_tool]" in line and "predict_top_player(" in line:
                tools_called.append(ToolCall(name="predict_top_player", success=True, duration_sec=0.1))
            elif "[chat_agent]" in line and "delegating" in line:
                tools_called.append(ToolCall(name="chat_agent", success=True, duration_sec=0.1))
            elif "EXCEPTION" in line or "ERROR" in line:
                tools_called.append(ToolCall(name="unknown_tool", success=False, duration_sec=0.0))
        
        # Log structured event
        log_record = logging.LogRecord(
            name="afl_api",
            level=logging.INFO,
            pathname="api.py",
            lineno=0,
            msg="Chat request processed successfully",
            args=(),
            exc_info=None,
        )
        log_record.query = request.message[:100]
        log_record.intent = intent
        log_record.tools_called = [t.name for t in tools_called]
        log_record.latency_sec = round(latency, 3)
        log_record.conversation_id = request.conversation_id
        log_record.token_usage = {"input": 0, "output": 0}  # populated by ai_chat_afl's LLM call if/when it exposes usage
        logger.handle(log_record)
        
        return ChatResponse(
            response=final_response,
            intent=intent,
            confidence=confidence,
            tools_called=tools_called,
            latency_sec=round(latency, 3),
            timestamp=timestamp,
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    
    except Exception as e:
        latency = time.time() - start_time
        error_msg = str(e)
        error_type = type(e).__name__
        
        # Log error
        log_record = logging.LogRecord(
            name="afl_api",
            level=logging.ERROR,
            pathname="api.py",
            lineno=0,
            msg=f"Chat request failed: {error_type}",
            args=(),
            exc_info=None,
        )
        log_record.query = request.message[:100]
        log_record.conversation_id = request.conversation_id
        log_record.latency_sec = round(latency, 3)
        log_record.error = error_msg
        logger.handle(log_record)
        
        # Return user-friendly error message
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {error_type} - {error_msg[:100]}"
        )


@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "graph": "ready" if _GRAPH_APP is not None else "not_loaded",
            "predict": "available" if check_predict_available() else "unavailable",
        }
    }


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
        "success_count": 0,
    }
    
    latencies = []
    try:
        with open(log_file) as f:
            for line in f:
                try:
                    record = json.loads(line)
                    if record.get("level") == "INFO" and "processed" in record.get("message", ""):
                        stats["total_queries"] += 1
                        stats["success_count"] += 1
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
    
    stats["error_rate"] = round(stats["error_count"] / (stats["total_queries"] + 1), 4)
    
    return stats


@app.get("/")
def root():
    """API info."""
    return {
        "name": "AFL Assistant API",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": {
            "POST /chat": "Main chat endpoint (message + conversation_id)",
            "GET /health": "Health check with component status",
            "GET /logs/summary": "Summary statistics from structured logs",
            "GET /docs": "Interactive API documentation (Swagger UI)",
        },
        "example_request": {
            "message": "Will Melbourne beat Richmond?",
            "conversation_id": "user_123"
        }
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("Starting AFL Assistant API...")
    print("Documentation available at: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
