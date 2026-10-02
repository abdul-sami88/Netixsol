from typing import Dict, Any, List
import json
from datetime import datetime

class ExecutionTracer:
    """
    Task 5 — State Logging & Annotated Execution Traces
    Logs every node transition, input state snapshots, output state deltas,
    tool call parameters, and timestamps for full agent observablity.
    """
    _global_trace_store: Dict[str, List[Dict[str, Any]]] = {}

    @classmethod
    def log_trace(cls, session_id: str, trace_events: List[Dict[str, Any]]):
        if session_id not in cls._global_trace_store:
            cls._global_trace_store[session_id] = []
        cls._global_trace_store[session_id].extend(trace_events)

    @classmethod
    def get_session_trace(cls, session_id: str) -> List[Dict[str, Any]]:
        return cls._global_trace_store.get(session_id, [])

    @classmethod
    def get_all_traces(cls, limit: int = 50) -> Dict[str, Any]:
        return {
            "total_tracked_sessions": len(cls._global_trace_store),
            "sessions": {k: v[-limit:] for k, v in cls._global_trace_store.items()}
        }

tracer = ExecutionTracer()
