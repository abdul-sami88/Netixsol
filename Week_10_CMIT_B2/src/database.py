"""
Zarya Digital Bank - Database & Ticketing Engine
Week 10 - Day 4: Task 5 Structured Tools & Escalation System
"""

import os
import sqlite3
import random
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "zarya_banking.db")


# SBP Regulatory Turnaround Times (in business days)
SBP_TAT_MAPPING = {
    "ATM_DISPUTE": 10,
    "RAAST_TRANSFER": 2,
    "IBFT_TRANSFER": 15,
    "UNAUTHORIZED_TRANSACTION": 30,
    "CARD_ISSUE": 7,
    "ACCOUNT_SERVICE": 3,
    "GENERAL_QUERY": 1,
}


def get_db_connection(db_path: str = DB_PATH):
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_PATH):
    """Initializes tickets and escalation tables."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS complaint_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id TEXT UNIQUE NOT NULL,
        customer_phone TEXT,
        category TEXT NOT NULL,
        priority TEXT NOT NULL,
        amount REAL DEFAULT 0.0,
        reference_id TEXT,
        summary TEXT NOT NULL,
        customer_reported_details TEXT,
        tat_days INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'OPEN',
        escalated_to_human BOOLEAN NOT NULL DEFAULT 0,
        escalation_reason TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS security_audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        masked_prompt TEXT NOT NULL,
        action_taken TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


class ZaryaTicketingEngine:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        init_db(self.db_path)

    def generate_ticket_id(self) -> str:
        random_num = random.randint(100000, 999999)
        return f"ZAR-2026-{random_num}"

    def assess_escalation(
        self,
        category: str,
        priority: str,
        amount: float = 0.0,
        raw_text: str = ""
    ) -> Tuple[bool, Optional[str]]:
        """
        Determines whether ticket must be escalated to a senior human specialist.
        """
        reasons = []

        # 1. High value threshold (> Rs. 50,000)
        if amount >= 50000.0:
            reasons.append(f"High financial value (Rs. {amount:,.0f} >= Rs. 50,000 threshold)")

        # 2. Fraud / Unauthorized activity
        if category in ["UNAUTHORIZED_TRANSACTION", "FRAUD"]:
            reasons.append("Security risk: Unauthorized / Fraud transaction reported")

        # 3. Explicit High/Critical Priority
        if priority in ["HIGH", "CRITICAL"]:
            reasons.append(f"Critical SLA priority assigned ({priority})")

        # 4. Distress / anger keywords
        distress_keywords = ["police", "court", "fraud", "scam", "lout liya", "chori", "barbaad", "sbp complaint"]
        if any(kw in raw_text.lower() for kw in distress_keywords):
            reasons.append("Customer sentiment: Distress / Escalation keywords detected")

        if reasons:
            return True, " | ".join(reasons)
        return False, None

    def create_ticket(
        self,
        category: str,
        priority: str,
        summary: str,
        customer_details: str,
        amount: float = 0.0,
        reference_id: str = "N/A",
        customer_phone: str = "03XX-XXXXXXX",
        raw_query: str = ""
    ) -> Dict[str, Any]:
        """
        Creates ticket in database and calculates SBP TAT.
        """
        ticket_id = self.generate_ticket_id()
        tat_days = SBP_TAT_MAPPING.get(category.upper(), 5)
        now_iso = datetime.now(timezone.utc).isoformat()

        escalated, reason = self.assess_escalation(
            category=category,
            priority=priority,
            amount=amount,
            raw_text=f"{summary} {customer_details} {raw_query}"
        )

        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO complaint_tickets (
            ticket_id, customer_phone, category, priority, amount,
            reference_id, summary, customer_reported_details, tat_days,
            status, escalated_to_human, escalation_reason, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_id, customer_phone, category, priority, amount,
            reference_id, summary, customer_details, tat_days,
            "ESCALATED_HUMAN_QUEUE" if escalated else "OPEN",
            1 if escalated else 0, reason, now_iso, now_iso
        ))

        conn.commit()
        conn.close()

        return {
            "ticket_id": ticket_id,
            "category": category,
            "priority": priority,
            "amount": amount,
            "reference_id": reference_id,
            "tat_days": tat_days,
            "status": "ESCALATED_HUMAN_QUEUE" if escalated else "OPEN",
            "escalated_to_human": escalated,
            "escalation_reason": reason,
            "customer_message_ur": (
                f"Aap ki shikayat darj kar li gayi hai. Ticket ID: {ticket_id}. "
                f"SBP regulations ke mutabiq is category ka resolution time {tat_days} working days hai."
                + (" Humare senior fraud specialist ko yeh case foran escalate kar diya gaya hai." if escalated else "")
            )
        }

    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM complaint_tickets WHERE ticket_id = ?", (ticket_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_all_tickets(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM complaint_tickets ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

