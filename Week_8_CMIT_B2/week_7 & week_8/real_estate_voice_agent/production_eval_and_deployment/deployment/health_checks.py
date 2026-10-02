"""
Task 5 — Production Health Check Probes
Provides standard Kubernetes & Cloud Probes:
- /healthz: Basic Liveness Check
- /livez: Process & Runtime Liveness Check
- /readyz: Deep Readiness Check (Database, LLM API keys, SMTP connectivity)
"""

import os
import sqlite3
import smtplib
from typing import Dict, Any
from config import config

def check_liveness() -> Dict[str, Any]:
    """Liveness probe to confirm HTTP server is running."""
    return {
        "status": "UP",
        "probe": "liveness",
        "service": "real-estate-voice-agent"
    }

def check_readiness() -> Dict[str, Any]:
    """
    Deep Readiness probe verifying SQLite DB, Gemini/Groq keys, and SMTP server reachability.
    """
    db_status = False
    llm_status = False
    smtp_status = False
    details = {}

    # 1. Database Check
    try:
        conn = sqlite3.connect(config.DB_PATH)
        c = conn.cursor()
        c.execute("SELECT 1")
        conn.close()
        db_status = True
        details["database"] = "CONNECTED"
    except Exception as e:
        details["database"] = f"FAILED: {e}"

    # 2. LLM Key Configuration Check
    if bool(config.GEMINI_API_KEY and "your_" not in config.GEMINI_API_KEY) or bool(config.GROQ_API_KEY and "your_" not in config.GROQ_API_KEY):
        llm_status = True
        details["llm_api_keys"] = "CONFIGURED"
    else:
        details["llm_api_keys"] = "MISSING_OR_PLACEHOLDER"

    # 3. SMTP Connectivity Check
    try:
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT, timeout=5)
        server.starttls()
        server.quit()
        smtp_status = True
        details["smtp_server"] = "REACHABLE"
    except Exception as e:
        details["smtp_server"] = f"FAILED: {e}"

    is_ready = db_status and llm_status and smtp_status

    return {
        "status": "READY" if is_ready else "NOT_READY",
        "probe": "readiness",
        "ready_checks": {
            "database": db_status,
            "llm_api": llm_status,
            "smtp": smtp_status
        },
        "details": details
    }
