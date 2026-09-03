"""
Task 4 — Structured JSON Telemetry Logger
Tracks:
- Average Latency (p50, p90, p99)
- Voice Quality (STT confidence & normalization metrics)
- API Failures (Gemini / Groq / FastAPI exceptions)
- Calendar Failures (Google Calendar API errors)
- Email Failures (SMTP dispatch failures)
- Booking Successes (Completed bookings)
- RAG Misses (Zero relevance retrieval events)
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
TELEMETRY_FILE = LOG_DIR / "telemetry_events.jsonl"

class TelemetryLogger:
    def __init__(self):
        pass

    def log_event(
        self,
        event_type: str, # 'API_CALL', 'VOICE_STT', 'CALENDAR', 'EMAIL', 'RAG_QUERY', 'BOOKING'
        session_id: str,
        latency_sec: float,
        status: str = "SUCCESS", # 'SUCCESS', 'FAILURE', 'RAG_MISS'
        details: Optional[Dict[str, Any]] = None
    ):
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "session_id": session_id,
            "latency_sec": round(latency_sec, 3),
            "status": status,
            "details": details or {}
        }
        
        # Append structured JSON event line
        with open(TELEMETRY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        if not TELEMETRY_FILE.exists():
            return []
        events = []
        with open(TELEMETRY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line.strip()))
        return events[-limit:]

telemetry_logger = TelemetryLogger()
